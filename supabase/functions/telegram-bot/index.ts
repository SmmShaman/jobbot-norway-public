/**
 * Telegram Bot Webhook Handler
 * Handles all Telegram bot interactions with inline keyboards
 */

import { serve } from "https://deno.land/std@0.168.0/http/server.ts"
import { createClient } from 'https://esm.sh/@supabase/supabase-js@2'

const corsHeaders = {
  'Access-Control-Allow-Origin': '*',
  'Access-Control-Allow-Headers': 'authorization, x-client-info, apikey, content-type',
}

const TELEGRAM_BOT_TOKEN = Deno.env.get('TELEGRAM_BOT_TOKEN')!

// Global variables for loop prevention and rate limiting
const botMessageIds = new Set<string>()
const userCooldowns = new Map<string, number>()

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
 * Only accept direct job search/ad URLs
 */
function isValidFinnUrl(text: string): boolean {
  const trimmed = text.trim()
  // Match only real FINN.no job search and ad URLs
  const searchPattern = /^https?:\/\/(www\.)?finn\.no\/job\/(fulltime|parttime|management)\/search\.html/i
  const adPattern = /^https?:\/\/(www\.)?finn\.no\/job\/(fulltime|parttime|management)\/ad\.html/i

  return searchPattern.test(trimmed) || adPattern.test(trimmed)
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
 * Full pipeline orchestration: Scan → Extract → Analyze
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

  // Step 1: Send initial message
  await sendTypingAction(chatId)
  const initialMsg = await sendTelegramMessage(
    chatId,
    `🔍 <b>Починаю сканування вакансій</b>\n\n` +
    `📋 Посилання: <code>${finnUrl}</code>\n\n` +
    `⏳ Шукаю вакансії...`
  )
  const statusMessageId = initialMsg.result.message_id

  try {
    // STEP 1: Scan URLs from search page (MODE 1)
    await sendTypingAction(chatId)
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
      await editMessage(
        chatId,
        statusMessageId,
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

    await editMessage(
      chatId,
      statusMessageId,
      `✅ <b>Знайдено ${scanData.jobsScraped} вакансій</b>\n\n` +
      jobTitles.join('\n') + '\n\n' +
      `⏳ Витягую деталі вакансій (контакти, опис, дедлайни)...`
    )

    // STEP 2: Extract details (MODE 2)
    await sendTypingAction(chatId)
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
      await editMessage(
        chatId,
        statusMessageId,
        `⚠️ <b>Помилка витягування даних</b>\n\n` +
        `Вакансії знайдені, але не вдалося витягнути деталі.\n` +
        `Спробуй ще раз або перевір Dashboard.`
      )
      return
    }

    await editMessage(
      chatId,
      statusMessageId,
      `✅ <b>Деталі витягнуто</b>\n\n` +
      `📊 Оброблено: ${extractData.jobsScraped} вакансій\n` +
      `💾 Збережено: ${extractData.jobsSaved} нових\n` +
      `🔄 Оновлено: ${extractData.jobsUpdated} існуючих\n\n` +
      `🤖 Зараз аналізую на релевантність з вашим профілем...`
    )

    // Get job IDs from database
    const { data: jobs } = await supabase
      .from('jobs')
      .select('id, title, company')
      .in('url', jobUrls)
      .eq('user_id', userId)
      .order('created_at', { ascending: false })

    if (!jobs || jobs.length === 0) {
      await editMessage(
        chatId,
        statusMessageId,
        `⚠️ <b>Не знайдено вакансій в базі</b>\n\n` +
        `Дані витягнуті, але щось пішло не так при збереженні.\n` +
        `Перевір Dashboard: https://jobbot-norway.netlify.app`
      )
      return
    }

    const jobIds = jobs.map((j: any) => j.id)

    // STEP 3: Analyze relevance
    await sendTypingAction(chatId)
    console.log('Step 3: Analyzing job relevance...')

    const analyzeResponse = await fetch(`${supabaseUrl}/functions/v1/job-analyzer`, {
      method: 'POST',
      headers: {
        'Authorization': `Bearer ${supabaseKey}`,
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({
        jobIds: jobIds,
        userId: userId,
      }),
    })

    const analyzeData = await analyzeResponse.json()
    console.log('Analyze result:', analyzeData)

    if (!analyzeData.success) {
      await editMessage(
        chatId,
        statusMessageId,
        `⚠️ <b>Помилка аналізу</b>\n\n` +
        `Вакансії збережені, але AI аналіз не вдався.\n` +
        `Можеш запустити аналіз вручну в Dashboard.`
      )
      return
    }

    // STEP 4: Get analysis results and format message
    const { data: analyzedJobs } = await supabase
      .from('jobs')
      .select('id, title, company, location, relevance_score, ai_recommendation')
      .in('id', jobIds)
      .order('relevance_score', { ascending: false })

    let resultsText = `✅ <b>Аналіз завершено!</b>\n\n`
    resultsText += `📊 Проаналізовано: ${analyzeData.jobsAnalyzed} вакансій\n\n`
    resultsText += `<b>Результати релевантності профіля до вакансій:</b>\n\n`

    analyzedJobs?.forEach((job: any, idx: number) => {
      const scoreEmoji = job.relevance_score >= 70 ? '🟢' : job.relevance_score >= 40 ? '🟡' : '🔴'
      resultsText += `${idx + 1}. <b>${job.title}</b>\n`
      resultsText += `   🏢 ${job.company} • 📍 ${job.location || 'N/A'}\n`
      resultsText += `   ${scoreEmoji} <b>Оцінка: ${job.relevance_score}/100</b>\n`
      if (job.ai_recommendation) {
        // Show FULL recommendation without truncation
        resultsText += `   💬 ${job.ai_recommendation}\n`
      }
      resultsText += `\n`
    })

    resultsText += `\n🔗 <a href="https://jobbot-norway.netlify.app">Відкрити Dashboard</a>`

    // Create inline buttons for top jobs (score >= 60)
    const topJobs = analyzedJobs?.filter((j: any) => j.relevance_score >= 60) || []
    const inlineKeyboard = {
      inline_keyboard: [
        ...topJobs.slice(0, 3).map((job: any) => [{
          text: `📝 ${job.title} (${job.relevance_score}/100)`,
          callback_data: `apply_${job.id}`,
        }]),
        [
          { text: '📊 Dashboard', url: 'https://jobbot-norway.netlify.app' }
        ]
      ]
    }

    await editMessage(
      chatId,
      statusMessageId,
      resultsText,
      inlineKeyboard
    )

    console.log('✅ Pipeline completed successfully')

  } catch (error) {
    console.error('Pipeline error:', error)
    await editMessage(
      chatId,
      statusMessageId,
      `❌ <b>Помилка виконання</b>\n\n` +
      `Щось пішло не так: ${error.message}\n\n` +
      `Спробуй ще раз або перевір Dashboard.`
    )
  }
}

// Main webhook handler
serve(async (req) => {
  if (req.method === 'OPTIONS') {
    return new Response('ok', { headers: corsHeaders })
  }

  try {
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

    // Store update_id to prevent reprocessing
    await supabase
      .from('processed_updates')
      .insert({
        update_id: updateId,
        processed_at: new Date().toISOString()
      })
      .select()
      .maybeSingle()

    // Handle callback query (button press)
    if (update.callback_query) {
      const callbackQuery = update.callback_query
      const chatId = callbackQuery.message.chat.id.toString()
      const data = callbackQuery.callback_data

      await answerCallbackQuery(callbackQuery.id)

      // Parse callback data
      const [action, id] = data.split('_')

      switch (action) {
        case 'apply': {
          // User wants to apply to job
          const jobId = id

          // TODO: Trigger application generation via Edge Function
          // Call: /functions/v1/generate-application

          await sendTelegramMessage(chatId, '⏳ Генерую заявку... Зачекайте, будь ласка.')

          // The generate-application function will send the preview when ready
          break
        }

        case 'approve': {
          // User approves application
          const applicationId = id

          // TODO: Submit application
          // Call: /functions/v1/submit-application

          await sendTelegramMessage(chatId, '✅ Відправляю заявку... Зачекайте.')
          break
        }

        case 'reject': {
          // User rejects application - show feedback options
          const applicationId = id

          const feedback = formatFeedbackOptions(applicationId)
          await sendTelegramMessage(chatId, feedback.text, feedback.reply_markup)
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
          const [subaction, applicationId] = data.split('_').slice(1)

          if (subaction === 'manual') {
            // Send current Ukrainian version for editing
            const { data: version } = await supabase
              .from('application_versions')
              .select('cover_letter_uk')
              .eq('application_id', applicationId)
              .eq('is_current', true)
              .single()

            await sendTelegramMessage(
              chatId,
              `✏️ <b>Редагування заявки</b>\n\nПоточна версія (українською):\n\n${version?.cover_letter_uk}\n\n<i>Надішліть виправлену версію повідомленням:</i>`
            )

            // Update state to WAITING_EDIT
            await supabase
              .from('telegram_conversations')
              .upsert({
                chat_id: chatId,
                telegram_user_id: callbackQuery.from.id.toString(),
                state: 'WAITING_EDIT',
                current_application_id: applicationId
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
        // User sent edited version
        // TODO: Send to LLM for grammar correction and translation
        await sendTelegramMessage(chatId, '✅ Обробляю вашу версію...')

        // Reset state
        await supabase
          .from('telegram_conversations')
          .update({ state: 'IDLE' })
          .eq('chat_id', chatId)
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
          `<b>Приклад посилання:</b>\n` +
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
