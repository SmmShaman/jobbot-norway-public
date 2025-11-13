/**
 * Scheduled Scanner Edge Function
 *
 * Automatically runs job scanning for users with enabled schedules
 * Called by Supabase pg_cron or external cron service
 */

import { serve } from 'https://deno.land/std@0.168.0/http/server.ts'
import { createClient } from 'https://esm.sh/@supabase/supabase-js@2'

const corsHeaders = {
  'Access-Control-Allow-Origin': '*',
  'Access-Control-Allow-Headers': 'authorization, x-client-info, apikey, content-type',
}

interface UserSchedule {
  user_id: string
  telegram_chat_id: string
  scan_schedule_cron: string
  scan_schedule_timezone: string
  finn_search_urls: string[]
}

/**
 * Check if current time matches cron expression
 */
function matchesCron(cronExpr: string, timezone: string): boolean {
  const now = new Date()

  // Simple cron matching for common patterns
  // Format: minute hour day month dayOfWeek
  const parts = cronExpr.split(' ')
  if (parts.length !== 5) return false

  const [minute, hour, , , dayOfWeek] = parts

  const currentMinute = now.getMinutes()
  const currentHour = now.getHours()
  const currentDay = now.getDay() // 0=Sunday, 1=Monday, etc.

  // Check minute
  if (minute !== '*' && parseInt(minute) !== currentMinute) {
    return false
  }

  // Check hour
  if (hour !== '*' && !hour.includes(',') && !hour.includes('/')) {
    if (parseInt(hour) !== currentHour) {
      return false
    }
  }

  // Check day of week
  if (dayOfWeek !== '*') {
    const allowedDays = dayOfWeek.split(',').map(d => parseInt(d))
    if (!allowedDays.includes(currentDay)) {
      return false
    }
  }

  return true
}

/**
 * Run scan for a single user and send results to Telegram
 */
async function runScanForUser(
  supabaseClient: any,
  user: UserSchedule,
  supabaseUrl: string,
  supabaseKey: string
): Promise<{ success: boolean; jobsFound: number; jobsAnalyzed: number }> {
  console.log(`📅 Running scheduled scan for user ${user.user_id}`)

  try {
    // Step 1: Scrape jobs from user's FINN URLs
    let totalJobsScraped = 0
    const newJobIds: string[] = []

    for (const url of user.finn_search_urls || []) {
      console.log(`🔍 Scanning URL: ${url}`)

      const scrapeResponse = await fetch(`${supabaseUrl}/functions/v1/job-scraper`, {
        method: 'POST',
        headers: {
          'Authorization': `Bearer ${supabaseKey}`,
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          searchUrl: url,
          userId: user.user_id,
        }),
      })

      const scrapeData = await scrapeResponse.json()
      if (scrapeData.success) {
        totalJobsScraped += scrapeData.jobsScraped || 0
        newJobIds.push(...(scrapeData.newJobIds || []))
      }
    }

    console.log(`✅ Scraped ${totalJobsScraped} jobs, ${newJobIds.length} new`)

    // Step 2: Analyze new jobs (only jobs that haven't been analyzed)
    let totalJobsAnalyzed = 0

    if (newJobIds.length > 0) {
      // Get jobs that need full details extraction
      const { data: jobsToExtract } = await supabaseClient
        .from('jobs')
        .select('id, url')
        .in('id', newJobIds)
        .is('description', null)

      if (jobsToExtract && jobsToExtract.length > 0) {
        console.log(`📄 Extracting details for ${jobsToExtract.length} jobs`)

        const jobUrls = jobsToExtract.map((j: any) => j.url)

        const extractResponse = await fetch(`${supabaseUrl}/functions/v1/job-scraper`, {
          method: 'POST',
          headers: {
            'Authorization': `Bearer ${supabaseKey}`,
            'Content-Type': 'application/json',
          },
          body: JSON.stringify({
            jobUrls,
            userId: user.user_id,
          }),
        })

        await extractResponse.json()
      }

      // Analyze relevance for new jobs
      console.log(`🤖 Analyzing relevance for ${newJobIds.length} jobs`)

      const analyzeResponse = await fetch(`${supabaseUrl}/functions/v1/job-analyzer`, {
        method: 'POST',
        headers: {
          'Authorization': `Bearer ${supabaseKey}`,
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          jobIds: newJobIds,
          userId: user.user_id,
        }),
      })

      const analyzeData = await analyzeResponse.json()
      if (analyzeData.success) {
        totalJobsAnalyzed = analyzeData.jobsAnalyzed || 0
      }
    }

    // Step 3: Send results to Telegram
    if (user.telegram_chat_id) {
      console.log(`📱 Sending results to Telegram chat ${user.telegram_chat_id}`)

      // Get jobs with relevance > 50%
      const { data: relevantJobs } = await supabaseClient
        .from('jobs')
        .select('id, title, company, relevance_score, url')
        .eq('user_id', user.user_id)
        .gt('relevance_score', 50)
        .order('relevance_score', { ascending: false })
        .limit(5)

      let message = `🤖 <b>Автоматичне сканування завершено</b>\n\n`
      message += `📊 <b>Результати:</b>\n`
      message += `🔍 Знайдено вакансій: ${totalJobsScraped}\n`
      message += `🆕 Нових вакансій: ${newJobIds.length}\n`
      message += `🤖 Проаналізовано: ${totalJobsAnalyzed}\n`
      message += `⭐ Релевантних (>50%): ${relevantJobs?.length || 0}\n\n`

      if (relevantJobs && relevantJobs.length > 0) {
        message += `<b>🎯 Топ релевантних вакансій:</b>\n\n`
        relevantJobs.forEach((job: any, index: number) => {
          message += `${index + 1}. <b>${job.title}</b>\n`
          message += `   ${job.company} | Оцінка: ${job.relevance_score}%\n`
          message += `   ${job.url}\n\n`
        })
      }

      message += `<i>Час сканування: ${new Date().toLocaleString('uk-UA', { timeZone: user.scan_schedule_timezone })}</i>`

      const telegramToken = Deno.env.get('TELEGRAM_BOT_TOKEN')!
      await fetch(`https://api.telegram.org/bot${telegramToken}/sendMessage`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          chat_id: user.telegram_chat_id,
          text: message,
          parse_mode: 'HTML',
        }),
      })
    }

    // Update last scan time
    await supabaseClient
      .from('user_settings')
      .update({
        last_scheduled_scan_at: new Date().toISOString(),
      })
      .eq('user_id', user.user_id)

    return {
      success: true,
      jobsFound: totalJobsScraped,
      jobsAnalyzed: totalJobsAnalyzed,
    }

  } catch (error) {
    console.error(`❌ Error scanning for user ${user.user_id}:`, error)
    return {
      success: false,
      jobsFound: 0,
      jobsAnalyzed: 0,
    }
  }
}

serve(async (req) => {
  // Handle CORS
  if (req.method === 'OPTIONS') {
    return new Response('ok', { headers: corsHeaders })
  }

  try {
    // Initialize Supabase client with service role
    const supabaseClient = createClient(
      Deno.env.get('SUPABASE_URL') ?? '',
      Deno.env.get('SUPABASE_SERVICE_ROLE_KEY') ?? '',
      {
        auth: {
          autoRefreshToken: false,
          persistSession: false,
        },
      }
    )

    const supabaseUrl = Deno.env.get('SUPABASE_URL')!
    const supabaseKey = Deno.env.get('SUPABASE_SERVICE_ROLE_KEY')!

    console.log('🕐 Scheduled scanner triggered at', new Date().toISOString())

    // Get all users with enabled schedules
    const { data: users, error: usersError } = await supabaseClient
      .from('user_settings')
      .select('user_id, telegram_chat_id, scan_schedule_cron, scan_schedule_timezone, finn_search_urls')
      .eq('scan_schedule_enabled', true)

    if (usersError) {
      throw usersError
    }

    if (!users || users.length === 0) {
      console.log('ℹ️ No users with enabled schedules')
      return new Response(
        JSON.stringify({ success: true, message: 'No users with enabled schedules', usersScanned: 0 }),
        { headers: { ...corsHeaders, 'Content-Type': 'application/json' }, status: 200 }
      )
    }

    console.log(`👥 Found ${users.length} users with enabled schedules`)

    // Check which users should be scanned now based on their cron schedule
    const results = []
    let totalScanned = 0

    for (const user of users) {
      const shouldScan = matchesCron(user.scan_schedule_cron, user.scan_schedule_timezone)

      if (shouldScan) {
        console.log(`✅ User ${user.user_id} schedule matches, starting scan...`)
        const result = await runScanForUser(supabaseClient, user as UserSchedule, supabaseUrl, supabaseKey)
        results.push({ userId: user.user_id, ...result })
        totalScanned++
      } else {
        console.log(`⏭️ User ${user.user_id} schedule does not match current time, skipping`)
      }
    }

    return new Response(
      JSON.stringify({
        success: true,
        message: `Scanned ${totalScanned} users`,
        totalUsersWithSchedule: users.length,
        usersScanned: totalScanned,
        results,
      }),
      {
        headers: { ...corsHeaders, 'Content-Type': 'application/json' },
        status: 200,
      }
    )

  } catch (error) {
    console.error('❌ Scheduled scanner error:', error)
    return new Response(
      JSON.stringify({ error: error.message }),
      {
        headers: { ...corsHeaders, 'Content-Type': 'application/json' },
        status: 500,
      }
    )
  }
})
