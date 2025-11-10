/**
 * AI Evaluator Edge Function
 * Analyzes job relevance against user profile using Azure OpenAI
 * Returns relevance score 0-100%
 */

import { serve } from "https://deno.land/std@0.168.0/http/server.ts"
import { createClient } from 'https://esm.sh/@supabase/supabase-js@2'

const corsHeaders = {
  'Access-Control-Allow-Origin': '*',
  'Access-Control-Allow-Headers': 'authorization, x-client-info, apikey, content-type',
}

interface RelevanceResult {
  relevance_score: number  // 0-100
  is_relevant: boolean
  match_reasons: string[]
  concerns: string[]
  recommendation: 'APPLY' | 'REVIEW' | 'SKIP'
}

async function analyzeJobRelevance(
  job: any,
  profile: any
): Promise<RelevanceResult> {
  const azureEndpoint = Deno.env.get('AZURE_OPENAI_ENDPOINT')!
  const azureApiKey = Deno.env.get('AZURE_OPENAI_API_KEY')!
  const deploymentName = Deno.env.get('AZURE_OPENAI_DEPLOYMENT')!

  // Build profile summary
  const profileSummary = `
ПРОФІЛЬ КАНДИДАТА:
- Ім'я: ${profile.full_name}
- Професія: ${profile.career_objective || 'Не вказано'}
- Досвід роботи: ${profile.work_experience?.length || 0} позицій
- Останні посади: ${profile.work_experience?.slice(0, 3).map((w: any) => w.position).join(', ') || 'Не вказано'}
- Технічні навички: ${profile.technical_skills?.join(', ') || 'Не вказано'}
- Мови: ${profile.languages?.join(', ') || 'Не вказано'}
- Освіта: ${profile.education?.map((e: any) => e.degree).join(', ') || 'Не вказано'}
- Локація: ${profile.location || 'Не вказано'}
  `.trim()

  const jobSummary = `
ВАКАНСІЯ:
- Назва: ${job.title}
- Компанія: ${job.company || 'Не вказано'}
- Опис: ${job.description?.substring(0, 500) || 'Не вказано'}
- Вимоги: ${job.requirements?.join('; ') || 'Не вказано'}
- Локація: ${job.location || 'Не вказано'}
  `.trim()

  const prompt = `
Ти експерт з HR і карєрного консультування.

${profileSummary}

${jobSummary}

ЗАВДАННЯ: Оціни релевантність цієї вакансії для кандидата по шкалі 0-100%.

ПРИКЛАДИ ОЦІНКИ:
- Вихователька дитячого садка → Робітник фабрики = 20% (має фізичну витривалість, але немає досвіду виробництва)
- Вихователька дитячого садка → Диспетчер аеропорта = 0% (повністю різні професії, різні навички)
- Python Developer → Senior Python Engineer = 90% (відповідає профілю, є досвід)
- Менеджер ресторану → Менеджер готелю = 75% (схожі навички управління, гостинність)
- Бухгалтер → Фінансовий аналітик = 60% (схожа сфера, але різні функції)

КРИТЕРІЇ ОЦІНКИ:
1. Чи відповідає досвід роботи? (40% ваги)
2. Чи є необхідні технічні навички? (30% ваги)
3. Чи відповідає освіта? (15% ваги)
4. Чи знає необхідні мови? (10% ваги)
5. Чи підходить локація? (5% ваги)

РЕКОМЕНДАЦІЇ:
- APPLY (80-100%): Ідеальний або відмінний матч
- REVIEW (50-79%): Частково підходить, потрібен розгляд
- SKIP (0-49%): Не підходить або мало релевантний

Поверни ТІЛЬКИ валідний JSON:
{
  "relevance_score": 85,
  "is_relevant": true,
  "match_reasons": ["має потрібний досвід Python розробки", "знає Norwegian та English", "локація підходить"],
  "concerns": ["немає досвіду з FastAPI", "бракує сертифіката AWS"],
  "recommendation": "APPLY"
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
        temperature: 0.1,
        max_tokens: 1000,
      }),
    }
  )

  if (!response.ok) {
    const error = await response.text()
    throw new Error(`Azure OpenAI API error: ${error}`)
  }

  const data = await response.json()
  const content = data.choices[0].message.content

  // Clean JSON response
  const cleanedContent = content
    .replace(/```json\n?/g, '')
    .replace(/```\n?/g, '')
    .trim()

  return JSON.parse(cleanedContent)
}

serve(async (req) => {
  // Handle CORS
  if (req.method === 'OPTIONS') {
    return new Response('ok', { headers: corsHeaders })
  }

  try {
    const supabaseClient = createClient(
      Deno.env.get('SUPABASE_URL') ?? '',
      Deno.env.get('SUPABASE_SERVICE_ROLE_KEY') ?? '',
    )

    const { job_id, user_id } = await req.json()

    if (!job_id || !user_id) {
      throw new Error('Missing job_id or user_id')
    }

    console.log('Evaluating job relevance:', { job_id, user_id })

    // 1. Get user profile
    const { data: profile, error: profileError } = await supabaseClient
      .from('user_profiles')
      .select('*')
      .eq('user_id', user_id)
      .single()

    if (profileError || !profile) {
      throw new Error('User profile not found. Please upload resume first.')
    }

    // 2. Get job details
    const { data: job, error: jobError } = await supabaseClient
      .from('jobs')
      .select('*')
      .eq('id', job_id)
      .single()

    if (jobError || !job) {
      throw new Error('Job not found')
    }

    // 3. Analyze with AI
    const relevanceResult = await analyzeJobRelevance(job, profile)

    // 4. Update job with relevance data
    const { data: updatedJob, error: updateError } = await supabaseClient
      .from('jobs')
      .update({
        relevance_score: relevanceResult.relevance_score,
        relevance_reasons: relevanceResult.match_reasons,
        ai_recommendation: relevanceResult.recommendation,
        analyzed_at: new Date().toISOString(),
      })
      .eq('id', job_id)
      .select()
      .single()

    if (updateError) throw updateError

    return new Response(
      JSON.stringify({
        success: true,
        job: updatedJob,
        relevance: relevanceResult,
        message: `Job evaluated: ${relevanceResult.relevance_score}% relevance`
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
