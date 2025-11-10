/**
 * Telegram Notify Edge Function
 * Sends notifications about new relevant jobs via Telegram bot
 */

import { serve } from "https://deno.land/std@0.168.0/http/server.ts"

const corsHeaders = {
  'Access-Control-Allow-Origin': '*',
  'Access-Control-Allow-Headers': 'authorization, x-client-info, apikey, content-type',
}

interface TelegramMessage {
  chat_id: string
  text: string
  parse_mode?: 'HTML' | 'Markdown' | 'MarkdownV2'
  disable_web_page_preview?: boolean
}

async function sendTelegramMessage(message: TelegramMessage): Promise<boolean> {
  const botToken = Deno.env.get('TELEGRAM_BOT_TOKEN')!

  const response = await fetch(
    `https://api.telegram.org/bot${botToken}/sendMessage`,
    {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify(message),
    }
  )

  if (!response.ok) {
    const error = await response.text()
    throw new Error(`Telegram API error: ${error}`)
  }

  return true
}

function formatJobNotification(job: any): string {
  const relevanceEmoji = job.relevance_score >= 80 ? '🔥' :
                         job.relevance_score >= 50 ? '⭐' : '📋'

  const recommendationEmoji = job.ai_recommendation === 'APPLY' ? '✅' :
                              job.ai_recommendation === 'REVIEW' ? '🔍' : '❌'

  return `
${relevanceEmoji} <b>Нова релевантна вакансія!</b>

<b>Назва:</b> ${job.title}
<b>Компанія:</b> ${job.company || 'Не вказано'}
<b>Локація:</b> ${job.location || 'Не вказано'}

<b>Релевантність:</b> ${job.relevance_score}%
<b>Рекомендація:</b> ${recommendationEmoji} ${job.ai_recommendation}

<b>Причини відповідності:</b>
${job.relevance_reasons?.map((r: string) => `• ${r}`).join('\n') || 'Не вказано'}

<b>Посилання:</b> ${job.url}

<i>Відправлено через JobBot Norway</i>
  `.trim()
}

serve(async (req) => {
  // Handle CORS
  if (req.method === 'OPTIONS') {
    return new Response('ok', { headers: corsHeaders })
  }

  try {
    const { chat_id, job, type = 'new_job' } = await req.json()

    if (!chat_id) {
      throw new Error('Missing chat_id')
    }

    let messageText = ''

    switch (type) {
      case 'new_job':
        if (!job) throw new Error('Missing job data')
        messageText = formatJobNotification(job)
        break

      case 'daily_summary':
        const { total_jobs, relevant_jobs, applications_sent } = job
        messageText = `
📊 <b>Щоденний звіт JobBot Norway</b>

<b>Знайдено вакансій:</b> ${total_jobs}
<b>Релевантних (>70%):</b> ${relevant_jobs}
<b>Відправлено заявок:</b> ${applications_sent}

<i>Гарного дня! 🚀</i>
        `.trim()
        break

      case 'application_sent':
        if (!job) throw new Error('Missing job data')
        messageText = `
✅ <b>Заявку відправлено!</b>

<b>Вакансія:</b> ${job.title}
<b>Компанія:</b> ${job.company}

<b>Статус:</b> Успішно відправлено
<b>Час:</b> ${new Date().toLocaleString('uk-UA')}
        `.trim()
        break

      default:
        throw new Error(`Unknown notification type: ${type}`)
    }

    await sendTelegramMessage({
      chat_id,
      text: messageText,
      parse_mode: 'HTML',
      disable_web_page_preview: true,
    })

    return new Response(
      JSON.stringify({
        success: true,
        message: 'Notification sent successfully'
      }),
      {
        headers: { ...corsHeaders, 'Content-Type': 'application/json' },
        status: 200,
      },
    )

  } catch (error) {
    console.error('Error:', error)
    return new Response(
      JSON.stringify({
        success: false,
        error: error.message
      }),
      {
        headers: { ...corsHeaders, 'Content-Type': 'application/json' },
        status: 400,
      },
    )
  }
})
