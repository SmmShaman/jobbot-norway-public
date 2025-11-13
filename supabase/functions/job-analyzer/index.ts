import { serve } from 'https://deno.land/std@0.177.0/http/server.ts'
import { createClient } from 'https://esm.sh/@supabase/supabase-js@2.39.3'

const corsHeaders = {
  'Access-Control-Allow-Origin': '*',
  'Access-Control-Allow-Headers': 'authorization, x-client-info, apikey, content-type',
}

interface JobListing {
  id: string
  title: string
  company: string
  location: string
  url: string
  description?: string
  source: string
}

/**
 * Analyze job relevance to user profile using Azure OpenAI
 */
async function analyzeJobRelevance(
  supabaseClient: any,
  userId: string,
  job: JobListing
): Promise<{ score: number; summary: string }> {
  console.log('🤖 Analyzing job relevance for:', job.title)

  // Get active user profile
  const { data: profile, error: profileError } = await supabaseClient
    .from('saved_profiles')
    .select('profile_data')
    .eq('user_id', userId)
    .eq('is_active', true)
    .single()

  if (profileError || !profile) {
    console.log('⚠️ No active profile found, skipping relevance analysis')
    return { score: 0, summary: 'No active profile for analysis' }
  }

  const azureEndpoint = Deno.env.get('AZURE_OPENAI_ENDPOINT')!
  const azureApiKey = Deno.env.get('AZURE_OPENAI_API_KEY')!
  const deploymentName = Deno.env.get('AZURE_OPENAI_DEPLOYMENT') || 'gpt-4'

  const systemPrompt = `You are an expert HR analyst specializing in matching candidates to job opportunities.
Analyze the candidate's profile against the job posting and return a structured JSON assessment.

CRITICAL: Return ONLY valid JSON, no markdown, no explanations outside JSON.`

  const userPrompt = JSON.stringify({
    task: "Проаналізуй релевантність кандидата до вакансії на основі всього наданого профілю (який може містити кілька резюме, історію досвіду, навички, обов'язки та використані інструменти). Виділи з опису вакансії основні обов'язки та вимоги, співстав їх з усіма знайденими згадками у профілі й поверни результат у структурованому JSON.",

    candidate_profile: {
      ...profile.profile_data,
      context_notes: "Профіль зібрано на основі кількох резюме, що відображають досвід кандидата у різні періоди його життя."
    },

    job: {
      title: job.title,
      company: job.company,
      location: job.location,
      source: job.source,
      url: job.url,
      description: job.description
    },

    output_schema: {
      score: "0..100 — загальна оцінка релевантності",
      relevance_summary: "ДЕТАЛЬНИЙ висновок (3-5 речень) з КОНКРЕТНИМИ причинами чому така оцінка: які вимоги виконуються, які ні, що відсутнє, що є перевагою",
      duties: ["3-8 коротких дій, які потрібно виконувати на посаді"],
      requirements: ["5-12 ключових вимог або кваліфікацій"],
      req_pairs: [
        {
          require: "назва вимоги",
          candidate: "YES | PARTIAL | NO",
          evidence: "короткий доказ з профілю або відсутність",
          experience_depth: "0–5 (0 — відсутній досвід, 5 — експертний рівень)",
          recency: "approx_years_since_last_use або немає"
        }
      ],
      key_points: ["до 5 головних спостережень щодо відповідності"],
      strengths: ["до 4 сильні сторони кандидата для цієї вакансії"],
      weaknesses: ["до 4 обмеження або недоліки"],
      action_required: "1-2 рекомендації кандидату (що підсилити або додати до профілю)"
    },

    rules: [
      "Якщо у профілі згадано навіть частковий збіг — позначай candidate=PARTIAL із поясненням.",
      "Якщо навичка або технологія є еквівалентною або суміжною (напр. React vs Vue, Python vs R) — PARTIAL.",
      "Якщо профіль містить декілька ролей, враховуй усі, навіть старі досвіди.",
      "Якщо у вакансії не розділено duties та requirements — розділи логічно за змістом.",
      "Не роби припущень і не додавай нічого, чого немає у профілі.",
      "ОБОВ'ЯЗКОВО: relevance_summary має містити КОНКРЕТНІ факти чому така оцінка: які вимоги виконано (з доказами), які НЕ виконано, що критично відсутнє",
      "Поверни виключно JSON, без markdown або пояснювального тексту."
    ]
  }, null, 2)

  try {
    const response = await fetch(
      `${azureEndpoint}/openai/deployments/${deploymentName}/chat/completions?api-version=2024-08-01-preview`,
      {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'api-key': azureApiKey,
        },
        body: JSON.stringify({
          messages: [
            { role: 'system', content: systemPrompt },
            { role: 'user', content: userPrompt }
          ],
          temperature: 0.2,
          max_tokens: 3000,
          response_format: { type: 'json_object' },
        }),
      }
    )

    if (!response.ok) {
      const errorText = await response.text()
      console.error('❌ Azure OpenAI relevance analysis error:', response.status, errorText)
      return { score: 0, summary: 'Analysis failed' }
    }

    const data = await response.json()
    const analysis = JSON.parse(data.choices[0].message.content)

    console.log('✅ Relevance analysis complete:', {
      score: analysis.score,
      summary: analysis.relevance_summary?.substring(0, 50) + '...'
    })

    return {
      score: analysis.score || 0,
      summary: analysis.relevance_summary || 'No summary available'
    }

  } catch (error) {
    console.error('❌ Relevance analysis failed:', error)
    return { score: 0, summary: 'Analysis error' }
  }
}

serve(async (req) => {
  // Handle CORS
  if (req.method === 'OPTIONS') {
    return new Response('ok', { headers: corsHeaders })
  }

  try {
    // Initialize Supabase client with service role for RLS bypass
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

    const { jobIds, userId } = await req.json()

    if (!userId) {
      throw new Error('Missing userId parameter')
    }

    if (!jobIds || !Array.isArray(jobIds) || jobIds.length === 0) {
      throw new Error('Missing jobIds parameter (must be array of job IDs)')
    }

    console.log(`🎯 Analyzing ${jobIds.length} job(s) for user ${userId}`)

    let results = {
      jobsAnalyzed: 0,
      jobsUpdated: 0,
      jobsFailed: 0,
      jobsSkipped: 0, // Already analyzed jobs
      jobs: [] as any[],
    }

    // Analyze each job
    for (const jobId of jobIds) {
      try {
        // Get job details from database
        const { data: job, error: jobError } = await supabaseClient
          .from('jobs')
          .select('*')
          .eq('id', jobId)
          .eq('user_id', userId)
          .single()

        if (jobError || !job) {
          console.error(`❌ Job not found: ${jobId}`)
          results.jobsFailed++
          continue
        }

        // Skip if already analyzed (has relevance_score and ai_recommendation)
        if (job.relevance_score !== null && job.relevance_score !== undefined && job.ai_recommendation) {
          console.log(`⏭️ Job already analyzed (score: ${job.relevance_score}), skipping:`, job.title)
          results.jobsSkipped++
          results.jobs.push({
            id: jobId,
            title: job.title,
            score: job.relevance_score,
            summary: job.ai_recommendation,
            skipped: true,
          })
          continue
        }

        // Analyze relevance
        const relevanceAnalysis = await analyzeJobRelevance(supabaseClient, userId, job)
        results.jobsAnalyzed++

        // Update job with relevance data
        const { error: updateError } = await supabaseClient
          .from('jobs')
          .update({
            relevance_score: relevanceAnalysis.score,
            ai_recommendation: relevanceAnalysis.summary,
            updated_at: new Date().toISOString(),
          })
          .eq('id', jobId)

        if (updateError) {
          console.error('❌ Failed to update job:', updateError)
          results.jobsFailed++
        } else {
          results.jobsUpdated++
          results.jobs.push({
            id: jobId,
            title: job.title,
            score: relevanceAnalysis.score,
            summary: relevanceAnalysis.summary,
          })
        }

        // Rate limiting - 1.5 seconds between AI calls
        await new Promise(resolve => setTimeout(resolve, 1500))

      } catch (error) {
        console.error(`❌ Error analyzing job ${jobId}:`, error)
        results.jobsFailed++
      }
    }

    return new Response(
      JSON.stringify({
        success: true,
        ...results,
        message: `Analyzed ${results.jobsAnalyzed} jobs: ${results.jobsUpdated} updated, ${results.jobsSkipped} skipped (already analyzed), ${results.jobsFailed} failed`,
      }),
      {
        headers: { ...corsHeaders, 'Content-Type': 'application/json' },
        status: 200,
      }
    )

  } catch (error) {
    console.error('❌ Job analyzer error:', error)
    return new Response(
      JSON.stringify({
        success: false,
        error: error.message || 'Unknown error',
      }),
      {
        headers: { ...corsHeaders, 'Content-Type': 'application/json' },
        status: 400,
      }
    )
  }
})
