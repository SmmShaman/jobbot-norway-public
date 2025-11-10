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

interface TelegramUpdate {
  update_id: number
  message?: any
  callback_query?: any
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

  return response.json()
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
      const text = message.text || ''

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
          `👋 Вітаю! Я JobBot Norway - ваш AI-асистент для пошуку роботи в Норвегії.\n\nЯ буду надсилати вам релевантні вакансії та допомагати готувати заявки.\n\nДля початку налаштуйте свій профіль в веб-додатку: https://jobbot-norway.netlify.app`
        )
      }

      if (text === '/report') {
        // TODO: Generate and send daily report
        await sendTelegramMessage(chatId, '📊 Генерую звіт... Зачекайте.')
      }
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
