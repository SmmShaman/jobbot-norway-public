/**
 * Generate Application Edge Function
 * Generates cover letter in both Ukrainian and Norwegian using Azure OpenAI
 */

import { serve } from "https://deno.land/std@0.168.0/http/server.ts"
import { createClient } from 'https://esm.sh/@supabase/supabase-js@2'

const corsHeaders = {
  'Access-Control-Allow-Origin': '*',
  'Access-Control-Allow-Headers': 'authorization, x-client-info, apikey, content-type',
}

async function generateCoverLetter(job: any, profile: any, language: 'uk' | 'no'): Promise<string> {
  const azureEndpoint = Deno.env.get('AZURE_OPENAI_ENDPOINT')!
  const azureApiKey = Deno.env.get('AZURE_OPENAI_API_KEY')!
  const deploymentName = Deno.env.get('AZURE_OPENAI_DEPLOYMENT')!

  const langName = language === 'uk' ? 'українською' : 'norsk (bokmål)'
  const langInstruction = language === 'uk'
    ? 'Пиши природною українською мовою, професійно але тепло.'
    : 'Skriv på naturlig norsk bokmål, profesjonelt men varmt.'

  const prompt = `
Ти експерт з написання мотиваційних листів для норвезького ринку праці.

ПРОФІЛЬ КАНДИДАТА:
- Ім'я: ${profile.full_name}
- Професійний досвід: ${profile.professional_summary || 'Не вказано'}
- Досвід роботи: ${JSON.stringify(profile.work_experience?.slice(0, 3) || [])}
- Технічні навички: ${profile.technical_skills?.join(', ') || 'Не вказано'}
- Мови: ${profile.languages?.join(', ') || 'Не вказано'}
- Освіта: ${JSON.stringify(profile.education || [])}

ВАКАНСІЯ:
- Назва: ${job.title}
- Компанія: ${job.company}
- Локація: ${job.location || 'Не вказано'}
- Опис: ${job.description?.substring(0, 500) || 'Не вказано'}
- Вимоги: ${job.requirements?.join('; ') || 'Не вказано'}

ЗАВДАННЯ:
Напиши мотиваційний лист ${langName} для цієї вакансії.

ВАЖЛИВІ ВИМОГИ:
1. ${langInstruction}
2. Структура: вступ (чому ця вакансія), основна частина (досвід та навички), заключення (готовність до співпраці)
3. Довжина: 250-350 слів
4. Тон: професійний але дружній, не надто формальний
5. Підкресли релевантний досвід з профілю
6. Використовуй конкретні приклади з досвіду
7. Покажи знання про компанію (якщо є інформація)
8. НЕ вигадуй факти - використовуй тільки інформацію з профілю

${language === 'no' ? `
ДОДАТКОВО ДЛЯ НОРВЕЗЬКОЇ:
- Використовуй "De" (формальне звернення) до роботодавця
- Норвезькі фрази: "Med vennlig hilsen", "Jeg ser frem til"
- Норвезький стиль: прямий, чесний, не надто пишний
` : ''}

Поверни ТІЛЬКИ текст мотиваційного листа, без додаткових пояснень.
`

  const response = await fetch(
    `${azureEndpoint}/openai/deployments/${deploymentName}/chat/completions?api-version=2024-02-15-preview`,
    {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        'api-key': azureApiKey,
      },
      body: JSON.stringify({
        messages: [
          { role: 'user', content: prompt }
        ],
        temperature: 0.7,
        max_tokens: 1500,
      }),
    }
  )

  if (!response.ok) {
    const error = await response.text()
    throw new Error(`Azure OpenAI API error: ${error}`)
  }

  const data = await response.json()
  return data.choices[0].message.content.trim()
}

serve(async (req) => {
  if (req.method === 'OPTIONS') {
    return new Response('ok', { headers: corsHeaders })
  }

  try {
    const supabase = createClient(
      Deno.env.get('SUPABASE_URL') ?? '',
      Deno.env.get('SUPABASE_SERVICE_ROLE_KEY') ?? '',
    )

    const { job_id, user_id, chat_id } = await req.json()

    if (!job_id || !user_id) {
      throw new Error('Missing job_id or user_id')
    }

    console.log('Generating application:', { job_id, user_id })

    // 1. Get user profile
    const { data: profile, error: profileError } = await supabase
      .from('user_profiles')
      .select('*')
      .eq('user_id', user_id)
      .single()

    if (profileError || !profile) {
      throw new Error('User profile not found. Please upload resume first.')
    }

    // 2. Get job details
    const { data: job, error: jobError } = await supabase
      .from('jobs')
      .select('*')
      .eq('id', job_id)
      .single()

    if (jobError || !job) {
      throw new Error('Job not found')
    }

    // 3. Generate cover letters (both languages)
    console.log('Generating Ukrainian cover letter...')
    const coverLetterUk = await generateCoverLetter(job, profile, 'uk')

    console.log('Generating Norwegian cover letter...')
    const coverLetterNo = await generateCoverLetter(job, profile, 'no')

    // 4. Create application record
    const { data: application, error: appError } = await supabase
      .from('applications')
      .insert({
        user_id,
        job_id,
        status: 'PENDING'
      })
      .select()
      .single()

    if (appError) throw appError

    // 5. Save cover letter version
    const { data: version, error: versionError } = await supabase
      .from('application_versions')
      .insert({
        application_id: application.id,
        job_id,
        user_id,
        version_number: 1,
        cover_letter_uk: coverLetterUk,
        cover_letter_no: coverLetterNo,
        generation_type: 'INITIAL',
        ai_model: Deno.env.get('AZURE_OPENAI_DEPLOYMENT') || 'gpt-4.1-mini',
        is_current: true,
        is_approved: false
      })
      .select()
      .single()

    if (versionError) throw versionError

    // 6. Send preview to Telegram (if chat_id provided)
    if (chat_id) {
      const telegramUrl = Deno.env.get('SUPABASE_URL')!.replace('.supabase.co', '') + '.functions.supabase.co/telegram-notify'

      await fetch(telegramUrl, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          chat_id,
          type: 'application_preview',
          job,
          application: {
            id: application.id,
            cover_letter_uk: coverLetterUk,
            cover_letter_no: coverLetterNo
          }
        })
      })
    }

    return new Response(
      JSON.stringify({
        success: true,
        application,
        version,
        message: 'Application generated successfully'
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
