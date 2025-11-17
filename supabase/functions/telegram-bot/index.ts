/**
 * Telegram Bot Webhook Handler
 * Handles all Telegram bot interactions
 */
import serve from "https://deno.land/std@0.168.0/http/server.ts";
import createClient from "https://esm.sh/@supabase/supabase-js@2";

const corsHeaders = {
  "Access-Control-Allow-Origin": "*",
  "Access-Control-Allow-Headers": "authorization, x-client-info, apikey, content-type",
};

const TELEGRAM_BOT_TOKEN = Deno.env.get("TELEGRAM_BOT_TOKEN")!;

// Global variables for loop prevention and rate limiting
const botMessageIds = new Set<string>()
const userCooldowns = new Map<string, number>()
const MAX_STORED_MESSAGE_IDS = 1000 // Limit to prevent memory leak

/**
 * Cleanup old data from memory to prevent memory leaks
 */
function cleanupOldData() {
  // Cleanup old message IDs if exceeded limit
  if (botMessageIds.size > MAX_STORED_MESSAGE_IDS) {
    const toDelete = botMessageIds.size - MAX_STORED_MESSAGE_IDS
    const iterator = botMessageIds.values()
    for (let i = 0; i < toDelete; i++) {
      const value = iterator.next().value
      if (value) botMessageIds.delete(value)
    }
    console.log(`Cleaned up ${toDelete} old message IDs`)
  }

  // Cleanup old cooldowns (older than 1 hour)
  const oneHourAgo = Date.now() - 3600000
  for (const [chatId, timestamp] of userCooldowns.entries()) {
    if (timestamp < oneHourAgo) {
      userCooldowns.delete(chatId)
    }
  }
}

interface TelegramUpdate {
  update_id: number
  message?: any
  edited_message?: any
  channel_post?: any
  edited_channel_post?: any
  callback_query?: any
}

/**
 * Validate FINN.no URL to prevent false positives
 * Only accept direct job search/ad URLs (both old and new formats)
 */
function isValidFinnUrl(text: string): boolean {
  const trimmed = text.trim()

  // Old format: finn.no/job/fulltime/search.html
  const oldSearchPattern = /^https?:\/\/(www\.)?finn\.no\/job\/(fulltime|parttime|management)\/search\.html/i
  const oldAdPattern = /^https?:\/\/(www\.)?finn\.no\/job\/(fulltime|parttime|management)\/ad\.html/i

  // New format: finn.no/job/search?location=...
  const newSearchPattern = /^https?:\/\/(www\.)?finn\.no\/job\/search\?/i
  const newAdPattern = /^https?:\/\/(www\.)?finn\.no\/job\/ad\//i

  return oldSearchPattern.test(trimmed) ||
         oldAdPattern.test(trimmed) ||
         newSearchPattern.test(trimmed) ||
         newAdPattern.test(trimmed)
}

/**
 * Check cooldown to prevent spam (10 seconds between requests)
 */
function checkCooldown(chatId: string): boolean {
  const lastRequest = userCooldowns.get(chatId)
  const now = Date.now()

  // 10 seconds cooldown
  if (lastRequest && (now - lastRequest) < 10000) {
    return false
  }

  userCooldowns.set(chatId, now)
  return true
}

// Send message via Telegram API
async function sendTelegramMessage(chatId: string, text: string, replyMarkup?: any) {
  const url = `https://api.telegram.org/bot${TELEGRAM_BOT_TOKEN}/sendMessage`

  const response = await fetch(url, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({
      chat_id: chatId,
      text,
      parse_mode: 'HTML',
      reply_markup: replyMarkup,
    }),
  })

  const result = await response.json()

  // Store message_id to prevent processing bot's own messages
  if (result.ok && result.result?.message_id) {
    botMessageIds.add(`${chatId}_${result.result.message_id}`)
  }

  return result
}

// Answer callback query (acknowledge button press)
async function answerCallbackQuery(callbackQueryId: string, text?: string) {
  const url = `https://api.telegram.org/bot${TELEGRAM_BOT_TOKEN}/answerCallbackQuery`

  await fetch(url, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({
      callback_query_id: callbackQueryId,
      text: text || 'Обробляю...',
    }),
  })
}

// Format job notification with inline keyboard
function formatJobsNotification(jobs: any[]) {
  let text = `🔍 <b>Знайдено ${jobs.length} нових вакансій!</b>\n\n`

  jobs.forEach((job, idx) => {
    text += `${idx + 1}. <b>${job.title}</b>\n`
    text += `   📍 ${job.location || 'Не вказано'}\n`
    text += `   🏢 ${job.company || 'Не вказано'}\n`
    text += `   📊 Релевантність: <b>${job.relevance_score}%</b>\n`
    text += `   ${job.description?.substring(0, 100)}...\n\n`
  })

  // Inline keyboard with buttons for each job
  const inlineKeyboard = jobs.map((job, idx) => [{
    text: `📝 Подати заявку на вакансію ${idx + 1}`,
    callback_data: `apply_${job.id}`
  }])

  return {
    text,
    reply_markup: {
      inline_keyboard: inlineKeyboard
    }
  }
}

// Format application preview with approve/reject buttons
function formatApplicationPreview(job: any, application: any) {
  let text = `📄 <b>Готова заявка на вакансію</b>\n\n`
  text += `<b>Вакансія:</b> ${job.title}\n`
  text += `<b>Компанія:</b> ${job.company}\n`
  text += `<b>Місце:</b> ${job.location || 'Не вказано'}\n\n`

  if (job.contact_name) {
    text += `<b>Контактна особа:</b> ${job.contact_name}\n`
  }
  if (job.contact_email) {
    text += `<b>Email:</b> ${job.contact_email}\n`
  }
  if (job.contact_phone) {
    text += `<b>Телефон:</b> ${job.contact_phone}\n`
  }

  text += `\n<b>📝 Заявка (Українська):</b>\n`
  text += `${application.cover_letter_uk?.substring(0, 300)}...\n\n`

  text += `<b>📝 Søknad (Norsk):</b>\n`
  text += `${application.cover_letter_no?.substring(0, 300)}...\n\n`

  text += `<i>Натисніть кнопку щоб переглянути повну версію або відправити.</i>`

  const inlineKeyboard = [
    [
      { text: '✅ Відправити заявку', callback_data: `approve_${application.id}` },
      { text: '❌ Не подобається', callback_data: `reject_${application.id}` }
    ],
    [
      { text: '📖 Повна версія (UA)', callback_data: `view_uk_${application.id}` },
      { text: '📖 Full version (NO)', callback_data: `view_no_${application.id}` }
    ]
  ]

  return {
    text,
    reply_markup: { inline_keyboard: inlineKeyboard }
  }
}

function balanceJsonBraces(text: string) {
  const trimmed = text.trim()
  const openCount = (trimmed.match(/{/g) || []).length
  const closeCount = (trimmed.match(/}/g) || []).length
  const missingClosing = Math.max(0, openCount - closeCount)
  if (missingClosing === 0) {
    return trimmed
  }
  return trimmed + '}'.repeat(missingClosing)
}

function parseApplicationResponse(content: string | object) {
  if (typeof content !== 'string') {
    return content
  }

  const trimmed = content.trim()

  try {
    return JSON.parse(trimmed)
  } catch (initialError) {
    const balanced = balanceJsonBraces(trimmed)

    if (balanced === trimmed) {
      throw initialError
    }

    try {
      console.warn('Balanced JSON braces before parsing AI response')
      return JSON.parse(balanced)
    } catch (secondError) {
      console.error('Failed to parse sanitized AI output', { trimmed, balanced })
      throw initialError
    }
  }
}

// Format feedback options when user rejects application
function formatFeedbackOptions(applicationId: string) {
  const text = `❌ Що саме не подобається в заявці?\n\nВиберіть причину або напишіть коментар:`

  const inlineKeyboard = [
    [{ text: '📋 Вказує невірні дані', callback_data: `feedback_wrong_${applicationId}` }],
    [{ text: '⚠️ Є неточності', callback_data: `feedback_inaccurate_${applicationId}` }],
    [{ text: '💬 Вставити свій коментар', callback_data: `feedback_comment_${applicationId}` }]
  ]

  return {
    text,
    reply_markup: { inline_keyboard: inlineKeyboard }
  }
}

// Format second attempt approval
function formatSecondAttempt(application: any) {
  let text = `📄 <b>Переглянута заявка (спроба 2)</b>\n\n`
  text += `<b>Заявка (Українська):</b>\n${application.cover_letter_uk?.substring(0, 300)}...\n\n`
  text += `<b>Søknad (Norsk):</b>\n${application.cover_letter_no?.substring(0, 300)}...\n\n`
  text += `<i>Це друга спроба. Виберіть дію:</i>`

  const inlineKeyboard = [
    [
      { text: '✅ Прийняти і відправити', callback_data: `final_approve_${application.id}` },
      { text: '✏️ Редагувати вручну', callback_data: `edit_manual_${application.id}` }
    ]
  ]

  return {
    text,
    reply_markup: { inline_keyboard: inlineKeyboard }
  }
}

// Format daily report
function formatDailyReport(report: any) {
  const date = new Date(report.report_date).toLocaleDateString('uk-UA', {
    day: 'numeric',
    month: 'long',
    year: 'numeric'
  })

  let text = `📊 <b>Звіт за ${date}</b>\n\n`
  text += `🔍 Нових вакансій знайдено: <b>${report.jobs_found}</b>\n`
  text += `✨ Релевантність вище 50%: <b>${report.jobs_relevant}</b>\n`
  text += `📝 Згенеровано заявок: <b>${report.applications_generated}</b>\n`
  text += `✅ Відправлено заявок: <b>${report.applications_sent}</b>\n\n`

  // Monthly stats
  text += `📅 <b>Статистика за листопад:</b>\n`
  text += `Всього відправлено заявок: <b>${report.monthly_total || 0}</b>`

  return text
}

// Send typing action
async function sendTypingAction(chatId: string) {
  const url = `https://api.telegram.org/bot${TELEGRAM_BOT_TOKEN}/sendChatAction`

  await fetch(url, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({
      chat_id: chatId,
      action: 'typing',
    }),
  })
}

// Edit message text
async function editMessage(chatId: string, messageId: number, text: string, replyMarkup?: any) {
  const url = `https://api.telegram.org/bot${TELEGRAM_BOT_TOKEN}/editMessageText`

  const response = await fetch(url, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({
      chat_id: chatId,
      message_id: messageId,
      text: text,
      parse_mode: 'HTML',
      reply_markup: replyMarkup,
    }),
  })

  const result = await response.json()

  // Store edited message_id as well
  if (result.ok && messageId) {
    botMessageIds.add(`${chatId}_${messageId}`)
  }

  return result
}

/**
 * Full pipeline orchestration: Scan → Extract → Analyze (with progressive updates)
 */
async function runFullPipeline(
  supabase: any,
  supabaseUrl: string,
  supabaseKey: string,
  userId: string,
  finnUrl: string,
  chatId: string
) {
  console.log('🚀 Starting full pipeline for URL:', finnUrl)

  try {
    // STEP 1: Scan URLs from search page
    await sendTypingAction(chatId)
    await sendTelegramMessage(
      chatId,
      `🔍 <b>Починаю сканування вакансій</b>\n\n` +
      `📋 Посилання: <code>${finnUrl}</code>\n\n` +
      `⏳ Шукаю вакансії...`
    )

    console.log('Step 1: Scanning job URLs...')
    const scanResponse = await fetch(`${supabaseUrl}/functions/v1/job-scraper`, {
      method: 'POST',
      headers: {
        'Authorization': `Bearer ${supabaseKey}`,
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({
        searchUrl: finnUrl,
        userId: userId,
      }),
    })

    const scanData = await scanResponse.json()
    console.log('Scan result:', scanData)

    if (!scanData.success || !scanData.jobs || scanData.jobs.length === 0) {
      await sendTelegramMessage(
        chatId,
        `❌ <b>Помилка сканування</b>\n\n` +
        `Не вдалося знайти вакансії за посиланням.\n` +
        `Перевір URL або спробуй пізніше.`
      )
      return
    }

    const jobUrls = scanData.jobs.map((j: any) => j.url)
    const jobTitles = scanData.jobs.map((j: any, idx: number) =>
      `${idx + 1}. ${j.title} • ${j.company || 'N/A'} • ${j.location || 'N/A'}`
    )

    await sendTelegramMessage(
      chatId,
      `✅ <b>Знайдено ${scanData.jobsScraped} вакансій</b>\n\n` +
      jobTitles.join('\n')
    )

    // STEP 2: Extract details
    await sendTypingAction(chatId)
    await sendTelegramMessage(
      chatId,
      `⏳ Витягую деталі вакансій (контакти, опис, дедлайни)...`
    )

    console.log('Step 2: Extracting job details...')
    const extractResponse = await fetch(`${supabaseUrl}/functions/v1/job-scraper`, {
      method: 'POST',
      headers: {
        'Authorization': `Bearer ${supabaseKey}`,
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({
        jobUrls: jobUrls,
        userId: userId,
      }),
    })

    const extractData = await extractResponse.json()
    console.log('Extract result:', extractData)

    if (!extractData.success) {
      await sendTelegramMessage(
        chatId,
        `⚠️ <b>Помилка витягування даних</b>\n\n` +
        `Вакансії знайдені, але не вдалося витягнути деталі.\n` +
        `Спробуй ще раз або перевір Dashboard.`
      )
      return
    }

    await sendTelegramMessage(
      chatId,
      `✅ <b>Деталі витягнуто</b>\n\n` +
      `📊 Оброблено: ${extractData.jobsScraped} вакансій\n` +
      `💾 Збережено: ${extractData.jobsSaved} нових\n` +
      `🔄 Оновлено: ${extractData.jobsUpdated} існуючих`
    )

    // Get job IDs from database
    const { data: jobs } = await supabase
      .from('jobs')
      .select('id, title, company, location, url, description')
      .in('url', jobUrls)
      .eq('user_id', userId)
      .order('created_at', { ascending: false })

    if (!jobs || jobs.length === 0) {
      await sendTelegramMessage(
        chatId,
        `⚠️ <b>Не знайдено вакансій в базі</b>\n\n` +
        `Дані витягнуті, але щось пішло не так при збереженні.\n` +
        `Перевір Dashboard: https://jobbot-norway.netlify.app`
      )
      return
    }

    // STEP 3: Analyze jobs ONE BY ONE and send progressive updates
    await sendTelegramMessage(
      chatId,
      `🤖 <b>Починаю аналіз релевантності</b>\n\n` +
      `📋 Буду аналізувати ${jobs.length} вакансій по черзі...`
    )

    console.log(`Step 3: Analyzing ${jobs.length} jobs progressively...`)

    for (let i = 0; i < jobs.length; i++) {
      const job = jobs[i]
      await sendTypingAction(chatId)

      console.log(`Analyzing job ${i + 1}/${jobs.length}: ${job.title}`)

      // Analyze single job
      const analyzeResponse = await fetch(`${supabaseUrl}/functions/v1/job-analyzer`, {
        method: 'POST',
        headers: {
          'Authorization': `Bearer ${supabaseKey}`,
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          jobIds: [job.id], // Analyze ONE job at a time
          userId: userId,
        }),
      })

      const analyzeData = await analyzeResponse.json()

      if (!analyzeData.success) {
        await sendTelegramMessage(
          chatId,
          `⚠️ Помилка аналізу вакансії "${job.title}"`
        )
        continue
      }

      // Get updated job data with analysis
      const { data: analyzedJob } = await supabase
        .from('jobs')
        .select('id, title, company, location, url, relevance_score, ai_recommendation')
        .eq('id', job.id)
        .single()

      if (!analyzedJob) continue

      // Format job message with analysis results
      const scoreEmoji = analyzedJob.relevance_score >= 70 ? '🟢' :
                        analyzedJob.relevance_score >= 40 ? '🟡' : '🔴'

      let jobText = `${scoreEmoji} <b>${analyzedJob.title}</b>\n\n`
      jobText += `🏢 <b>Компанія:</b> ${analyzedJob.company}\n`
      jobText += `📍 <b>Локація:</b> ${analyzedJob.location || 'Не вказано'}\n`
      jobText += `📊 <b>Релевантність:</b> ${analyzedJob.relevance_score}/100\n\n`

      if (analyzedJob.ai_recommendation) {
        jobText += `💬 <b>AI висновок:</b>\n${analyzedJob.ai_recommendation}\n\n`
      }

      jobText += `🔗 <a href="${analyzedJob.url}">Посилання на вакансію</a>`

      // Send job with "Write Application" button
      const keyboard = {
        inline_keyboard: [[
          { text: '✍️ Писати заявку/søknad', callback_data: `write_app_${analyzedJob.id}` }
        ]]
      }

      await sendTelegramMessage(chatId, jobText, keyboard)

      // Small delay to avoid flooding
      await new Promise(resolve => setTimeout(resolve, 500))
    }

    // Summary message
    await sendTelegramMessage(
      chatId,
      `✅ <b>Аналіз завершено!</b>\n\n` +
      `📊 Проаналізовано: ${jobs.length} вакансій\n\n` +
      `🔗 <a href="https://jobbot-norway.netlify.app">Відкрити Dashboard</a>`
    )

    console.log('✅ Pipeline completed successfully')

  } catch (error) {
    console.error('Pipeline error:', error)
    await sendTelegramMessage(
      chatId,
      `❌ <b>Помилка виконання</b>\n\n` +
      `Щось пішло не так: ${error.message}\n\n` +
      `Спробуй ще раз або перевір Dashboard.`
    )
  }
}

// Request counter for periodic cleanup
let requestCount = 0

// Main webhook handler
serve(async (req) => {
  if (req.method === 'OPTIONS') {
    return new Response('ok', { headers: corsHeaders })
  }

  try {
    // Periodic cleanup every 100 requests to prevent memory leaks
    requestCount++
    if (requestCount % 100 === 0) {
      cleanupOldData()
    }

    const supabase = createClient(
      Deno.env.get('SUPABASE_URL') ?? '',
      Deno.env.get('SUPABASE_SERVICE_ROLE_KEY') ?? '',
    )

    const update: TelegramUpdate = await req.json()

    // 1. CRITICAL: Ignore edited messages and channel posts to prevent loops
    if (update.edited_message || update.channel_post || update.edited_channel_post) {
      console.log('Ignoring edited_message/channel_post')
      return new Response(JSON.stringify({ ok: true }), {
        headers: { ...corsHeaders, 'Content-Type': 'application/json' },
        status: 200,
      })
    }

    // 2. CRITICAL: Deduplicate updates by update_id
    const updateId = update.update_id
    const { data: processed } = await supabase
      .from('processed_updates')
      .select('update_id')
      .eq('update_id', updateId)
      .maybeSingle()

    if (processed) {
      console.log('Update already processed:', updateId)
      return new Response(JSON.stringify({ ok: true }), {
        headers: { ...corsHeaders, 'Content-Type': 'application/json' },
        status: 200,
      })
    }

    // Store update_id to prevent reprocessing (use upsert to handle race conditions)
    await supabase
      .from('processed_updates')
      .upsert({
        update_id: updateId,
        processed_at: new Date().toISOString()
      }, {
        onConflict: 'update_id',
        ignoreDuplicates: true
      })

    // Handle callback query (button press)
    if (update.callback_query) {
      const callbackQuery = update.callback_query
      const chatId = callbackQuery.message.chat.id.toString()
      const data = callbackQuery.callback_data

      await answerCallbackQuery(callbackQuery.id)

      // Parse callback data
      const [action, ...rest] = data.split('_')

      switch (action) {
        case 'write': {
          // User clicked "Write Application" button
          const [subaction, jobId] = rest // write_app_jobId => ['app', 'jobId']

          if (subaction === 'app') {
            await sendTypingAction(chatId)
            await sendTelegramMessage(chatId, '✍️ <b>Генерую заявку...</b>\n\nОчікуй, це може зайняти до 30 секунд.')

            try {
              // Get job details
              const { data: job } = await supabase
                .from('jobs')
                .select('*')
                .eq('id', jobId)
                .single()

              if (!job) {
                await sendTelegramMessage(chatId, '❌ Вакансію не знайдено')
                break
              }

              // Get user settings
              const { data: userSettings } = await supabase
                .from('user_settings')
                .select('*')
                .eq('telegram_chat_id', chatId)
                .single()

              if (!userSettings) {
                await sendTelegramMessage(chatId, '❌ Користувача не знайдено. Прив\'яжи Telegram в Dashboard.')
                break
              }

              // Get canonical merged profile (saved_profiles) - use full JSON profile
              const { data: profileRow } = await supabase
                .from('saved_profiles')
                .select('profile_data')
                .eq('user_id', userSettings.user_id)
                .eq('is_active', true)
                .single()
              
              const profile = profileRow?.profile_data || null
              
              // Backwards-compat: if no saved_profiles, fallback to primary resume
              const { data: resume } = await supabase
                .from('resumes')
                .select('*')
                .eq('user_id', userSettings.user_id)
                .eq('is_primary', true)
                .single()

              // Build application prompt using the full saved_profiles.profile_data (preferred) or resume content fallback
              const profileText = profile 
                ? JSON.stringify(profile, null, 2) 
                : (resume?.content || 'Резюме не завантажено')
              
              const applicationPrompt = userSettings.application_prompt || `
Ти — експерт з написання мотиваційних листів для вакансій в Норвегії.

ВАКАНСІЯ:
Назва: ${job.title}
Компанія: ${job.company}
Опис: ${job.description}
Вимоги: ${job.requirements || 'Не вказано'}

КАНДИДАТ (повний профіль, saved_profiles.profile_data):
${profileText}

ЗАВДАННЯ:
Напиши професійний, адаптований до вакансії søknad (мотиваційний лист) норвезькою мовою (Bokmål).

ВИМОГИ:
- Офіційний, але дружній тон
- Підкреслити релевантний досвід і навички (витягнути з профілю)
- Показати мотивацію та релевантність до специфічних вимог
- Довжина: 150-250 слів

ФОРМАТ ВІДПОВІДІ (STRICT JSON ONLY — НІЯКИХ МАРКДАУН/ТЕКСТОВИХ ПІДСУМКІВ):
{
  "soknad_no": "текст søknad норвезькою",
  "translation_uk": "переклад українською"
}
              `

              // Use unified env variable names for Azure
              const azureEndpoint = Deno.env.get('AZURE_OPENAI_ENDPOINT')?.replace(/\/$/, '') || ''
              const azureKey = Deno.env.get('AZURE_OPENAI_API_KEY') || ''
              const deploymentName = Deno.env.get('AZURE_OPENAI_DEPLOYMENT') || 'gpt-4'
              const aiUrl = `${azureEndpoint}/openai/deployments/${deploymentName}/chat/completions?api-version=2024-08-01-preview`
              
              const aiResponse = await fetch(aiUrl, {
                method: 'POST',
                headers: {
                  'Content-Type': 'application/json',
                  'api-key': azureKey
                },
                body: JSON.stringify({
                  messages: [
                    {
                      role: 'system',
                      content: 'You are a professional application letter writer for Norwegian job market.'
                    },
                    {
                      role: 'user',
                      content: applicationPrompt
                    }
                  ],
                  temperature: 0.7,
                  max_tokens: 1500,
                  response_format: {
                    type: 'json_object'
                  }
                })
              })

              // Improved error handling and logging: reveal Azure error body if any
              if (!aiResponse.ok) {
                const errorText = await aiResponse.text()
                console.error('Azure OpenAI error (write_app):', aiResponse.status, errorText)
                await sendTelegramMessage(
                  chatId, 
                  `❌ <b>Помилка сервісу AI</b>\n\nСтатус: ${aiResponse.status}\n${errorText.substring(0, 1000)}`
                )
                throw new Error(`Azure OpenAI error: ${aiResponse.status} - ${errorText}`)
              }

              const aiData = await aiResponse.json()
              
              // aiData.choices[0].message.content може бути рядком JSON або об'єктом
              if (!aiData.choices || !aiData.choices[0]?.message) {
                console.error('Invalid AI response structure', aiData)
                throw new Error('Invalid AI response format')
              }

              let applicationText = aiData.choices[0].message.content
              let parsedApp
              
              try {
                parsedApp = parseApplicationResponse(applicationText)
              } catch (e) {
                console.error('Failed to parse AI output as JSON:', applicationText, e)
                throw new Error('AI returned invalid JSON')
              }

              // Save application to database
              const { data: savedApp, error: saveError } = await supabase
                .from('applications')
                .insert({
                  job_id: jobId,
                  user_id: userSettings.user_id,
                  cover_letter_no: parsedApp.soknad_no,
                  cover_letter_uk: parsedApp.translation_uk,
                  generated_prompt: applicationPrompt,
                  prompt_source: 'telegram',
                  status: 'draft',
                  created_at: new Date().toISOString()
                })
                .select()
                .single()

              if (saveError || !savedApp) {
                await sendTelegramMessage(chatId, `❌ Помилка збереження: ${saveError?.message}`)
                break
              }

              // Send application preview
              let previewText = `✅ <b>Заявка готова!</b>\n\n`
              previewText += `📋 <b>Вакансія:</b> ${job.title}\n`
              previewText += `🏢 <b>Компанія:</b> ${job.company}\n\n`
              previewText += `━━━━━━━━━━━━━━━━━━\n`
              previewText += `🇳🇴 <b>Søknad (Norsk):</b>\n\n`
              previewText += `${parsedApp.soknad_no}\n\n`
              previewText += `━━━━━━━━━━━━━━━━━━\n`
              previewText += `🇺🇦 <b>Переклад (Українська):</b>\n\n`
              previewText += `${parsedApp.translation_uk}`

              const keyboard = {
                inline_keyboard: [
                  [
                    { text: '✅ Підтвердити', callback_data: `approve_app_${savedApp.id}` },
                    { text: '❌ Відхилити', callback_data: `reject_app_${savedApp.id}` }
                  ],
                  [
                    { text: '✏️ Редагувати', callback_data: `edit_app_${savedApp.id}` }
                  ]
                ]
              }

              await sendTelegramMessage(chatId, previewText, keyboard)

            } catch (error) {
              console.error('Application generation error:', error)
              await sendTelegramMessage(chatId, `❌ <b>Помилка генерації заявки</b>\n\n${error.message}`)
            }
          }
          break
        }

        case 'apply': {
          // Legacy handler - redirect to write_app logic
          const jobId = rest[0]
          if (jobId) {
            await sendTypingAction(chatId)
            await sendTelegramMessage(chatId, '✍️ <b>Генерую заявку...</b>\n\nОчікуй, це може зайняти до 30 секунд.')
          }
          break
        }

        case 'approve': {
          // User approves application
          const [subaction, applicationId] = rest // approve_app_appId => ['app', 'appId']

          if (subaction === 'app') {
            // Update application status to approved
            const { error } = await supabase
              .from('applications')
              .update({ status: 'approved', approved_at: new Date().toISOString() })
              .eq('id', applicationId)

            if (error) {
              await sendTelegramMessage(chatId, `❌ Помилка: ${error.message}`)
              break
            }

            await sendTelegramMessage(
              chatId,
              `✅ <b>Заявку затверджено!</b>\n\n` +
              `Тепер її можна використати для подання на вакансію.\n\n` +
              `🔗 <a href="https://jobbot-norway.netlify.app">Відкрити Dashboard</a> для відправки`
            )
          }
          break
        }

        case 'reject': {
          // User rejects application
          const [subaction, applicationId] = rest // reject_app_appId => ['app', 'appId']

          if (subaction === 'app') {
            // Update application status to rejected
            await supabase
              .from('applications')
              .update({ status: 'rejected' })
              .eq('id', applicationId)

            await sendTelegramMessage(
              chatId,
              `❌ <b>Заявку відхилено</b>\n\n` +
              `Ти можеш створити нову заявку, натиснувши кнопку "Писати заявку" під вакансією.`
            )
          }
          break
        }

        case 'feedback': {
          // User selected feedback type (wrong, inaccurate, comment)
          const [feedbackType, applicationId] = data.split('_').slice(1)

          if (feedbackType === 'comment') {
            // Wait for user to type comment
            await sendTelegramMessage(
              chatId,
              '💬 Будь ласка, напишіть свій коментар для покращення заявки:'
            )

            // Update conversation state to WAITING_FEEDBACK
            await supabase
              .from('telegram_conversations')
              .upsert({
                chat_id: chatId,
                telegram_user_id: callbackQuery.from.id.toString(),
                state: 'WAITING_FEEDBACK',
                current_application_id: applicationId,
                context: { feedback_type: 'user_comment' }
              })
          } else {
            // Trigger regeneration with predefined feedback
            // TODO: Call /functions/v1/revise-application
            await sendTelegramMessage(chatId, '🔄 Переробляю заявку... Зачекайте.')
          }
          break
        }

        case 'final': {
          // Second attempt approval
          const [subaction, applicationId] = data.split('_').slice(1)

          if (subaction === 'approve') {
            // Submit application
            await sendTelegramMessage(chatId, '✅ Відправляю заявку...')
          }
          break
        }

        case 'edit': {
          // Open manual editor
          const [subaction, applicationId] = rest // edit_app_appId => ['app', 'appId']

          if (subaction === 'app') {
            // Get current application
            const { data: app } = await supabase
              .from('applications')
              .select('*')
              .eq('id', applicationId)
              .single()

            if (!app) {
              await sendTelegramMessage(chatId, '❌ Заявку не знайдено')
              break
            }

            await sendTelegramMessage(
              chatId,
              `✏️ <b>Редагування заявки</b>\n\n` +
              `<b>Поточна версія (норвезькою):</b>\n\n${app.cover_letter_no}\n\n` +
              `━━━━━━━━━━━━━━━━━━\n\n` +
              `<b>Переклад (українською):</b>\n\n${app.cover_letter_uk}\n\n` +
              `━━━━━━━━━━━━━━━━━━\n\n` +
              `<i>Надішли відредагований текст заявки <b>норвезькою</b> наступним повідомленням:</i>`
            )

            // Update conversation state to WAITING_EDIT
            await supabase
              .from('telegram_conversations')
              .upsert({
                chat_id: chatId,
                telegram_user_id: callbackQuery.from.id.toString(),
                state: 'WAITING_EDIT',
                current_application_id: applicationId,
                updated_at: new Date().toISOString()
              }, {
                onConflict: 'chat_id'
              })
          }
          break
        }

        case 'view': {
          // View full version
          const [lang, applicationId] = data.split('_').slice(1)

          const { data: version } = await supabase
            .from('application_versions')
            .select('*')
            .eq('application_id', applicationId)
            .eq('is_current', true)
            .single()

          const fullText = lang === 'uk' ? version?.cover_letter_uk : version?.cover_letter_no

          await sendTelegramMessage(
            chatId,
            `📖 <b>Повна версія (${lang === 'uk' ? 'Українська' : 'Norsk'})</b>\n\n${fullText}`
          )
          break
        }
      }
    }

    // Handle regular message
    if (update.message) {
      const message = update.message
      const chatId = message.chat.id.toString()
      const messageId = message.message_id
      const text = message.text || ''

      // 3. CRITICAL: Ignore messages from bots
      if (message.from?.is_bot) {
        console.log('Ignoring message from bot')
        return new Response(JSON.stringify({ ok: true }), {
          headers: { ...corsHeaders, 'Content-Type': 'application/json' },
          status: 200,
        })
      }

      // 4. CRITICAL: Ignore bot's own messages by message_id
      if (botMessageIds.has(`${chatId}_${messageId}`)) {
        console.log('Ignoring bot own message (message_id tracked)')
        return new Response(JSON.stringify({ ok: true }), {
          headers: { ...corsHeaders, 'Content-Type': 'application/json' },
          status: 200,
        })
      }

      // 5. BACKUP: Ignore bot's result messages by content (in case message_id tracking fails)
      if (text.includes('Аналіз завершено') ||
          text.includes('Результати релевантності') ||
          text.includes('Проаналізовано:') ||
          text.includes('Деталі витягнуто') ||
          text.includes('Оцінка:') ||
          text.includes('Відкрити Dashboard') ||
          text.includes('Починаю сканування') ||
          text.includes('Шукаю вакансії') ||
          text.includes('Помилка сканування') ||
          text.includes('Помилка витягування') ||
          text.includes('Помилка аналізу') ||
          text.includes('🟢') || text.includes('🟡') || text.includes('🔴')) {
        console.log('Ignoring bot result message (contains result indicators)')
        return new Response(JSON.stringify({ ok: true }), {
          headers: { ...corsHeaders, 'Content-Type': 'application/json' },
          status: 200,
        })
      }

      // Check conversation state
      const { data: conversation } = await supabase
        .from('telegram_conversations')
        .select('*')
        .eq('chat_id', chatId)
        .single()

      if (conversation?.state === 'WAITING_FEEDBACK') {
        // User sent feedback comment
        // TODO: Trigger revision with user comment
        await sendTelegramMessage(chatId, '🔄 Переробляю заявку з вашим коментарем... Зачекайте.')

        // Reset state
        await supabase
          .from('telegram_conversations')
          .update({ state: 'IDLE' })
          .eq('chat_id', chatId)
      }

      if (conversation?.state === 'WAITING_EDIT') {
        // User sent edited version (in Norwegian)
        const editedText = text
        const applicationId = conversation.current_application_id

        await sendTypingAction(chatId)
        await sendTelegramMessage(chatId, '✅ Обробляю вашу версію...')

        try {
          // Translate edited Norwegian text to Ukrainian using AI
          const azureEndpoint = Deno.env.get('AZURE_OPENAI_ENDPOINT')
          const azureKey = Deno.env.get('AZURE_OPENAI_API_KEY')
          const deploymentName = Deno.env.get('AZURE_OPENAI_DEPLOYMENT') || 'gpt-4'

          const translationResponse = await fetch(`${azureEndpoint}/openai/deployments/${deploymentName}/chat/completions?api-version=2024-08-01-preview`, {
            method: 'POST',
            headers: {
              'Content-Type': 'application/json',
              'api-key': azureKey || '',
            },
            body: JSON.stringify({
              messages: [
                { role: 'system', content: 'You are a professional translator. Translate Norwegian text to Ukrainian.' },
                { role: 'user', content: `Translate this Norwegian job application letter to Ukrainian:\n\n${editedText}` }
              ],
              temperature: 0.3,
              max_tokens: 1000
            })
          })

          if (!translationResponse.ok) {
            const errorText = await translationResponse.text()
            throw new Error(`Translation error: ${translationResponse.status} - ${errorText}`)
          }

          const translationData = await translationResponse.json()

          if (!translationData.choices || !translationData.choices[0]?.message?.content) {
            throw new Error('Invalid translation response format')
          }

          const ukrainianTranslation = translationData.choices[0].message.content

          // Update application with edited version
          const { error } = await supabase
            .from('applications')
            .update({
              cover_letter_no: editedText,
              cover_letter_uk: ukrainianTranslation,
              updated_at: new Date().toISOString()
            })
            .eq('id', applicationId)

          if (error) {
            await sendTelegramMessage(chatId, `❌ Помилка збереження: ${error.message}`)
          } else {
            // Get application
            const { data: app } = await supabase
              .from('applications')
              .select('*')
              .eq('id', applicationId)
              .single()

            if (!app) {
              await sendTelegramMessage(chatId, '❌ Заявку не знайдено')
              await supabase
                .from('telegram_conversations')
                .update({ state: 'IDLE', current_application_id: null })
                .eq('chat_id', chatId)
              return new Response(JSON.stringify({ ok: true }), {
                headers: { ...corsHeaders, 'Content-Type': 'application/json' },
                status: 200,
              })
            }

            // Get job info separately
            const { data: job } = await supabase
              .from('jobs')
              .select('title, company')
              .eq('id', app.job_id)
              .single()

            if (!job) {
              await sendTelegramMessage(chatId, '❌ Вакансію не знайдено')
              await supabase
                .from('telegram_conversations')
                .update({ state: 'IDLE', current_application_id: null })
                .eq('chat_id', chatId)
              return new Response(JSON.stringify({ ok: true }), {
                headers: { ...corsHeaders, 'Content-Type': 'application/json' },
                status: 200,
              })
            }

            // Send updated application preview
            let previewText = `✅ <b>Заявка оновлена!</b>\n\n`
            previewText += `📋 <b>Вакансія:</b> ${job.title}\n`
            previewText += `🏢 <b>Компанія:</b> ${job.company}\n\n`
            previewText += `━━━━━━━━━━━━━━━━━━\n`
            previewText += `🇳🇴 <b>Søknad (Norsk):</b>\n\n`
            previewText += `${editedText}\n\n`
            previewText += `━━━━━━━━━━━━━━━━━━\n`
            previewText += `🇺🇦 <b>Переклад (Українська):</b>\n\n`
            previewText += `${ukrainianTranslation}`

            const keyboard = {
              inline_keyboard: [
                [
                  { text: '✅ Підтвердити', callback_data: `approve_app_${applicationId}` },
                  { text: '❌ Відхилити', callback_data: `reject_app_${applicationId}` }
                ],
                [
                  { text: '✏️ Редагувати ще раз', callback_data: `edit_app_${applicationId}` }
                ]
              ]
            }

            await sendTelegramMessage(chatId, previewText, keyboard)
          }
        } catch (error) {
          console.error('Edit processing error:', error)
          await sendTelegramMessage(chatId, `❌ Помилка обробки: ${error.message}`)
        }

        // Reset state
        await supabase
          .from('telegram_conversations')
          .update({ state: 'IDLE', current_application_id: null })
          .eq('chat_id', chatId)

        return new Response(JSON.stringify({ ok: true }), {
          headers: { ...corsHeaders, 'Content-Type': 'application/json' },
          status: 200,
        })
      }

      // Handle commands
      if (text === '/start') {
        await sendTelegramMessage(
          chatId,
          `👋 <b>Вітаю в JobBot Norway!</b>\n\n` +
          `Я допоможу знайти та проаналізувати вакансії з FINN.no\n\n` +
          `<b>Команди:</b>\n` +
          `/scan - Запустити повне сканування (всі збережені URLs)\n` +
          `/scan [URL] - Сканувати конкретний URL\n` +
          `/help - Допомога\n` +
          `/report - Денний звіт\n\n` +
          `Або просто відправ посилання на FINN.no!\n\n` +
          `📊 Dashboard: https://jobbot-norway.netlify.app`
        )
        return new Response(JSON.stringify({ ok: true }), {
          headers: { ...corsHeaders, 'Content-Type': 'application/json' },
          status: 200,
        })
      }

      if (text === '/help') {
        await sendTelegramMessage(
          chatId,
          `❓ <b>Допомога</b>\n\n` +
          `<b>Як використовувати:</b>\n` +
          `1. Відправ посилання на пошук FINN.no\n` +
          `2. Бот знайде всі вакансії\n` +
          `3. Витягне деталі кожної вакансії\n` +
          `4. Проаналізує релевантність до твого профілю\n\n` +
          `<b>Приклади посилань:</b>\n` +
          `<code>https://www.finn.no/job/search?location=0.20001</code>\n` +
          `<code>https://www.finn.no/job/fulltime/search.html?location=0.20001</code>\n\n` +
          `<b>Команди:</b>\n` +
          `/scan - Запустити сканування всіх збережених URLs\n` +
          `/scan [URL] - Сканувати конкретний URL\n` +
          `/start - Початок роботи\n` +
          `/report - Денний звіт`
        )
        return new Response(JSON.stringify({ ok: true }), {
          headers: { ...corsHeaders, 'Content-Type': 'application/json' },
          status: 200,
        })
      }

      if (text.startsWith('/scan')) {
        const parts = text.split(' ')

        // Get user settings for stored URLs
        const { data: settings } = await supabase
          .from('user_settings')
          .select('finn_search_urls, user_id')
          .eq('telegram_chat_id', chatId)
          .single()

        if (!settings) {
          await sendTelegramMessage(
            chatId,
            `⚠️ <b>Акаунт не прив'язано</b>\n\n` +
            `Спочатку прив'яжи свій Telegram в Dashboard:\n` +
            `https://jobbot-norway.netlify.app\n\n` +
            `Settings → Telegram → вкажи Chat ID: <code>${chatId}</code>`
          )
          return
        }

        const userId = settings.user_id
        const supabaseUrl = Deno.env.get('SUPABASE_URL')!
        const supabaseKey = Deno.env.get('SUPABASE_SERVICE_ROLE_KEY')!

        if (parts.length > 1) {
          // /scan with specific URL
          const url = parts.slice(1).join(' ').trim()

          // Validate URL strictly
          if (!isValidFinnUrl(url)) {
            await sendTelegramMessage(
              chatId,
              `⚠️ Невірне посилання!\n\n` +
              `Підтримуються тільки посилання FINN.no:\n` +
              `• <code>https://finn.no/job/search?location=...</code>\n` +
              `• <code>https://finn.no/job/fulltime/search.html?...</code>\n` +
              `• <code>https://finn.no/job/parttime/search.html?...</code>\n` +
              `• <code>https://finn.no/job/management/search.html?...</code>`
            )
            return new Response(JSON.stringify({ ok: true }), {
              headers: { ...corsHeaders, 'Content-Type': 'application/json' },
              status: 200,
            })
          }

          // Check cooldown
          if (!checkCooldown(chatId)) {
            await sendTelegramMessage(
              chatId,
              `⏳ Зачекай 10 секунд перед наступним запитом`
            )
            return new Response(JSON.stringify({ ok: true }), {
              headers: { ...corsHeaders, 'Content-Type': 'application/json' },
              status: 200,
            })
          }

          await runFullPipeline(supabase, supabaseUrl, supabaseKey, userId, url, chatId)
          return new Response(JSON.stringify({ ok: true }), {
            headers: { ...corsHeaders, 'Content-Type': 'application/json' },
            status: 200,
          })
        } else {
          // /scan all saved URLs
          const savedUrls = settings.finn_search_urls || []

          if (savedUrls.length === 0) {
            await sendTelegramMessage(
              chatId,
              `⚠️ <b>Немає збережених URLs</b>\n\n` +
              `Додай FINN.no URLs в Dashboard:\n` +
              `https://jobbot-norway.netlify.app → Settings → Search URLs\n\n` +
              `Або відправ URL прямо сюди:`
            )
          } else {
            await sendTelegramMessage(
              chatId,
              `🚀 <b>Запускаю сканування ${savedUrls.length} збережених URLs...</b>\n\n` +
              `Це може зайняти кілька хвилин. Я буду оновлювати тебе на кожному етапі!`
            )

            // Run pipeline for each URL
            for (const url of savedUrls) {
              await runFullPipeline(supabase, supabaseUrl, supabaseKey, userId, url, chatId)
              // Wait between URLs to avoid rate limiting
              await new Promise(resolve => setTimeout(resolve, 3000))
            }
          }
        }
        return // Important: prevent further processing
      }

      // 6. CRITICAL: Check if user sent a direct FINN.no URL (strict validation)
      if (isValidFinnUrl(text)) {
        // Check cooldown first
        if (!checkCooldown(chatId)) {
          await sendTelegramMessage(
            chatId,
            `⏳ Зачекай 10 секунд перед наступним запитом`
          )
          return new Response(JSON.stringify({ ok: true }), {
            headers: { ...corsHeaders, 'Content-Type': 'application/json' },
            status: 200,
          })
        }

        // Get user ID from telegram_chat_id
        const { data: settings } = await supabase
          .from('user_settings')
          .select('user_id')
          .eq('telegram_chat_id', chatId)
          .single()

        if (!settings) {
          await sendTelegramMessage(
            chatId,
            `⚠️ <b>Акаунт не прив'язано</b>\n\n` +
            `Спочатку прив'яжи свій Telegram в Dashboard:\n` +
            `https://jobbot-norway.netlify.app\n\n` +
            `Settings → Telegram → вкажи Chat ID: <code>${chatId}</code>`
          )
          return new Response(JSON.stringify({ ok: true }), {
            headers: { ...corsHeaders, 'Content-Type': 'application/json' },
            status: 200,
          })
        }

        const userId = settings.user_id
        const supabaseUrl = Deno.env.get('SUPABASE_URL')!
        const supabaseKey = Deno.env.get('SUPABASE_SERVICE_ROLE_KEY')!

        await runFullPipeline(supabase, supabaseUrl, supabaseKey, userId, text, chatId)
        return new Response(JSON.stringify({ ok: true }), {
          headers: { ...corsHeaders, 'Content-Type': 'application/json' },
          status: 200,
        })
      }

      if (text === '/report') {
        // TODO: Generate and send daily report
        await sendTelegramMessage(chatId, '📊 Генерую звіт... Зачекайте.')
        return new Response(JSON.stringify({ ok: true }), {
          headers: { ...corsHeaders, 'Content-Type': 'application/json' },
          status: 200,
        })
      }

      // If no command matched, send help message
      await sendTelegramMessage(
        chatId,
        `🤔 Не розумію команду. Спробуй:\n\n` +
        `• Відправити посилання на FINN.no\n` +
        `• /scan - запустити сканування\n` +
        `• /help - отримати допомогу`
      )
    }

    return new Response(JSON.stringify({ ok: true }), {
      headers: { ...corsHeaders, 'Content-Type': 'application/json' },
      status: 200,
    })

  } catch (error) {
    console.error('Error:', error)
    return new Response(
      JSON.stringify({ error: error.message }),
      {
        headers: { ...corsHeaders, 'Content-Type': 'application/json' },
        status: 400,
      },
    )
  }
})
