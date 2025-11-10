/**
 * Revise Application Edge Function
 * Revises cover letter based on user feedback using Azure OpenAI
 */

import { serve } from "https://deno.land/std@0.168.0/http/server.ts"
import { createClient } from 'https://esm.sh/@supabase/supabase-js@2'

const corsHeaders = {
  'Access-Control-Allow-Origin': '*',
  'Access-Control-Allow-Headers': 'authorization, x-client-info, apikey, content-type',
}

async function reviseCoverLetter(
  originalUk: string,
  originalNo: string,
  job: any,
  profile: any,
  feedbackType: string,
  userFeedback?: string
): Promise<{ uk: string; no: string }> {
  const azureEndpoint = Deno.env.get('AZURE_OPENAI_ENDPOINT')!
  const azureApiKey = Deno.env.get('AZURE_OPENAI_API_KEY')!
  const deploymentName = Deno.env.get('AZURE_OPENAI_DEPLOYMENT')!

  let feedbackInstruction = ''

  switch (feedbackType) {
    case 'wrong_data':
      feedbackInstruction = `
Користувач вказав що в листі є НЕВІРНІ ДАНІ.
Перевір всі факти з профілю кандидата і виправ будь-які неточності:
- Назви компаній повинні точно співпадати
- Посади повинні бути точними
- Роки досвіду не можна перебільшувати
- Технічні навички тільки ті що є в профілі
      `
      break

    case 'inaccurate':
      feedbackInstruction = `
Користувач вказав що є НЕТОЧНОСТІ.
Покращ лист:
- Зроби більш конкретним і точним
- Додай конкретні приклади з досвіду
- Уточни як саме досвід підходить до вимог вакансії
- Перевір чи всі твердження підкріплені фактами з профілю
      `
      break

    case 'user_comment':
      feedbackInstruction = `
Користувач дав такий коментар для покращення:
"${userFeedback}"

Врахуй цей коментар і переробі лист відповідно.
      `
      break

    default:
      feedbackInstruction = 'Покращ загальну якість мотиваційного листа.'
  }

  const prompt = `
Ти експерт з написання мотиваційних листів.

ОРИГІНАЛЬНИЙ ЛИСТ (українською):
${originalUk}

ОРИГІНАЛЬНИЙ ЛИСТ (norsk):
${originalNo}

ПРОФІЛЬ КАНДИДАТА:
- Ім'я: ${profile.full_name}
- Досвід: ${JSON.stringify(profile.work_experience?.slice(0, 3) || [])}
- Навички: ${profile.technical_skills?.join(', ') || 'Не вказано'}

ВАКАНСІЯ:
- Назва: ${job.title}
- Компанія: ${job.company}
- Вимоги: ${job.requirements?.join('; ') || 'Не вказано'}

FEEDBACK ВІД КОРИСТУВАЧА:
${feedbackInstruction}

ЗАВДАННЯ:
1. Переробі мотиваційний лист на обох мовах (українською та norsk)
2. Врахуй feedback користувача
3. Використовуй ТІЛЬКИ факти з профілю кандидата
4. НЕ вигадуй нову інформацію
5. Збережи професійний тон
6. Довжина: 250-350 слів

Поверни результат у форматі JSON:
{
  "cover_letter_uk": "текст українською...",
  "cover_letter_no": "tekst på norsk..."
}
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
        max_tokens: 2000,
      }),
    }
  )

  if (!response.ok) {
    const error = await response.text()
    throw new Error(`Azure OpenAI API error: ${error}`)
  }

  const data = await response.json()
  const content = data.choices[0].message.content

  // Parse JSON response
  const cleaned = content
    .replace(/```json\n?/g, '')
    .replace(/```\n?/g, '')
    .trim()

  const result = JSON.parse(cleaned)

  return {
    uk: result.cover_letter_uk,
    no: result.cover_letter_no
  }
}

async function correctGrammarAndTranslate(
  editedTextUk: string,
  job: any,
  profile: any
): Promise<{ uk: string; no: string }> {
  const azureEndpoint = Deno.env.get('AZURE_OPENAI_ENDPOINT')!
  const azureApiKey = Deno.env.get('AZURE_OPENAI_API_KEY')!
  const deploymentName = Deno.env.get('AZURE_OPENAI_DEPLOYMENT')!

  const prompt = `
Ти професійний редактор і перекладач.

ВІДРЕДАГОВАНИЙ ТЕКСТ (українською):
${editedTextUk}

ЗАВДАННЯ:
1. Виправ граматику та орфографію в українському тексті
2. Покращ стилістику (якщо потрібно) зберігаючи зміст
3. Перекладі на норвезьку мову (bokmål)
4. В норвезькому тексті використовуй формальне "De"
5. Збережи структуру та довжину тексту

Поверни результат у форматі JSON:
{
  "cover_letter_uk": "виправлений текст українською...",
  "cover_letter_no": "oversatt tekst på norsk..."
}
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
        temperature: 0.3,
        max_tokens: 2000,
      }),
    }
  )

  if (!response.ok) {
    const error = await response.text()
    throw new Error(`Azure OpenAI API error: ${error}`)
  }

  const data = await response.json()
  const content = data.choices[0].message.content

  const cleaned = content
    .replace(/```json\n?/g, '')
    .replace(/```\n?/g, '')
    .trim()

  const result = JSON.parse(cleaned)

  return {
    uk: result.cover_letter_uk,
    no: result.cover_letter_no
  }
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

    const { application_id, feedback_type, user_feedback, edited_text_uk, chat_id } = await req.json()

    if (!application_id) {
      throw new Error('Missing application_id')
    }

    console.log('Revising application:', { application_id, feedback_type })

    // Get application and job
    const { data: application } = await supabase
      .from('applications')
      .select('*, jobs(*)')
      .eq('id', application_id)
      .single()

    if (!application) throw new Error('Application not found')

    const job = application.jobs

    // Get user profile
    const { data: profile } = await supabase
      .from('user_profiles')
      .select('*')
      .eq('user_id', application.user_id)
      .single()

    // Get current version
    const { data: currentVersion } = await supabase
      .from('application_versions')
      .select('*')
      .eq('application_id', application_id)
      .eq('is_current', true)
      .single()

    let revisedUk, revisedNo, generationType

    if (edited_text_uk) {
      // User manually edited - correct grammar and translate
      console.log('Correcting grammar and translating...')
      const corrected = await correctGrammarAndTranslate(edited_text_uk, job, profile)
      revisedUk = corrected.uk
      revisedNo = corrected.no
      generationType = 'USER_EDITED'
    } else {
      // LLM revision based on feedback
      console.log('Revising with LLM...')
      const revised = await reviseCoverLetter(
        currentVersion.cover_letter_uk,
        currentVersion.cover_letter_no,
        job,
        profile,
        feedback_type,
        user_feedback
      )
      revisedUk = revised.uk
      revisedNo = revised.no
      generationType = 'LLM_REVISED'
    }

    // Mark current version as not current
    await supabase
      .from('application_versions')
      .update({ is_current: false })
      .eq('application_id', application_id)
      .eq('is_current', true)

    // Create new version
    const nextVersionNumber = currentVersion.version_number + 1

    const { data: newVersion, error: versionError } = await supabase
      .from('application_versions')
      .insert({
        application_id: application_id,
        job_id: application.job_id,
        user_id: application.user_id,
        version_number: nextVersionNumber,
        cover_letter_uk: revisedUk,
        cover_letter_no: revisedNo,
        generation_type: generationType,
        feedback_reason: feedback_type,
        user_feedback: user_feedback,
        ai_model: Deno.env.get('AZURE_OPENAI_DEPLOYMENT') || 'gpt-4.1-mini',
        is_current: true,
        is_approved: false
      })
      .select()
      .single()

    if (versionError) throw versionError

    // Send updated version to Telegram
    if (chat_id) {
      const isSecondAttempt = nextVersionNumber === 2

      const telegramUrl = Deno.env.get('SUPABASE_URL')!.replace('.supabase.co', '') + '.functions.supabase.co/telegram-notify'

      await fetch(telegramUrl, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          chat_id,
          type: isSecondAttempt ? 'second_attempt' : 'application_preview',
          job,
          application: {
            id: application_id,
            cover_letter_uk: revisedUk,
            cover_letter_no: revisedNo
          }
        })
      })
    }

    return new Response(
      JSON.stringify({
        success: true,
        version: newVersion,
        message: 'Application revised successfully'
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
