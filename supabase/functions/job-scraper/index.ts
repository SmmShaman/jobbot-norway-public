/**
 * Job Scraper Edge Function
 *
 * Scrapes job listings from FINN.no
 * Two modes:
 * 1. Extract job URLs from search results page
 * 2. Extract detailed info from individual job page
 */

import { serve } from 'https://deno.land/std@0.168.0/http/server.ts'
import { createClient } from 'https://esm.sh/@supabase/supabase-js@2'
import { DOMParser } from 'https://deno.land/x/deno_dom@v0.1.45/deno-dom-wasm.ts'

const corsHeaders = {
  'Access-Control-Allow-Origin': '*',
  'Access-Control-Allow-Headers': 'authorization, x-client-info, apikey, content-type',
}

interface JobListing {
  title: string
  company: string
  location: string
  url: string
  source: string
  description?: string
  contact_person?: string
  contact_email?: string
  contact_phone?: string
  deadline?: string
  posted_date?: string
}

/**
 * Extracts job listing URLs from FINN.no search results page
 */
async function extractJobUrlsFromSearchPage(searchUrl: string): Promise<string[]> {
  console.log('📄 Fetching search page:', searchUrl)

  const response = await fetch(searchUrl, {
    headers: {
      'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
    },
  })

  if (!response.ok) {
    throw new Error(`Failed to fetch search page: ${response.status}`)
  }

  const html = await response.text()
  const document = new DOMParser().parseFromString(html, 'text/html')

  // FINN.no job listing selectors
  const jobLinks: string[] = []

  // Try multiple selectors (FINN.no 2025 structure)
  const selectors = [
    'a[href*="/job/ad/"]',
    '[data-testid="search-results"] a[href*="/job/ad/"]',
    'a[href^="https://www.finn.no/job/ad/"]',
  ]

  for (const selector of selectors) {
    const links = document.querySelectorAll(selector)
    if (links.length > 0) {
      console.log(`✅ Found ${links.length} job links using selector: ${selector}`)

      links.forEach((link: any) => {
        let href = link.getAttribute('href')
        if (href) {
          // Convert relative URLs to absolute
          if (href.startsWith('/')) {
            href = `https://www.finn.no${href}`
          }
          if (!jobLinks.includes(href)) {
            jobLinks.push(href)
          }
        }
      })

      break // Stop after finding matches
    }
  }

  console.log(`📊 Total unique job URLs extracted: ${jobLinks.length}`)
  return jobLinks
}

/**
 * Extract job details using Azure OpenAI GPT-4
 * More reliable than CSS selectors which break when FINN.no changes structure
 */
async function extractJobDetailsWithAI(html: string, jobUrl: string): Promise<JobListing> {
  console.log('🤖 Using AI to extract job details from:', jobUrl)

  const azureEndpoint = Deno.env.get('AZURE_OPENAI_ENDPOINT')!
  const azureApiKey = Deno.env.get('AZURE_OPENAI_API_KEY')!
  const deploymentName = Deno.env.get('AZURE_OPENAI_DEPLOYMENT') || 'gpt-4'

  // Parse HTML to get clean text
  const document = new DOMParser().parseFromString(html, 'text/html')
  const bodyText = document.body?.textContent || html

  const systemPrompt = `You are an expert at extracting structured job posting information from HTML pages.
Extract ONLY the actual job posting content, removing all navigation, breadcrumbs, footers, and UI elements.

Return a JSON object with these exact fields:
{
  "title": "Job title",
  "company": "Company name (NOT breadcrumb text like 'Her er du')",
  "location": "City and postal code (e.g. '2850 Lena' or 'Oslo')",
  "description": "Clean job description without HTML tags, navigation, or UI elements. Include responsibilities, qualifications, benefits.",
  "contact_person": "Name and title of contact person, if mentioned",
  "contact_email": "Contact email address, if mentioned",
  "contact_phone": "Contact phone number, if mentioned (format: +47 XXX XX XXX)",
  "deadline": "Application deadline date, if mentioned (e.g. '25.11.2025')"
}

IMPORTANT:
- Extract ONLY actual job content, not website navigation or UI
- Company should be the employer name, NOT breadcrumb text
- Description should be clean prose, not HTML or navigation text
- Set fields to null if not found (don't guess or make up information)
- Keep Norwegian text as-is, don't translate`

  const userPrompt = `Extract structured job information from this FINN.no job posting page.

URL: ${jobUrl}

PAGE CONTENT:
${bodyText.substring(0, 15000)}

Return ONLY valid JSON, no additional text.`

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
          temperature: 0.1,
          max_tokens: 2000,
          response_format: { type: 'json_object' },
        }),
      }
    )

    if (!response.ok) {
      const errorText = await response.text()
      console.error('❌ Azure OpenAI error:', response.status, errorText)
      throw new Error(`Azure OpenAI API error: ${response.status}`)
    }

    const data = await response.json()
    const extractedData = JSON.parse(data.choices[0].message.content)

    console.log('✅ AI extracted job details:', {
      title: extractedData.title,
      company: extractedData.company,
      location: extractedData.location,
      hasDescription: !!extractedData.description,
      hasContact: !!(extractedData.contact_person || extractedData.contact_email || extractedData.contact_phone)
    })

    // Convert Norwegian date format (DD.MM.YYYY) to ISO (YYYY-MM-DD)
    let deadlineISO: string | undefined = undefined
    if (extractedData.deadline) {
      try {
        // Try to parse DD.MM.YYYY or YYYY-MM-DD
        const dateMatch = extractedData.deadline.match(/(\d{2})\.(\d{2})\.(\d{4})/)
        if (dateMatch) {
          // DD.MM.YYYY format
          const [, day, month, year] = dateMatch
          deadlineISO = `${year}-${month}-${day}`
        } else if (/^\d{4}-\d{2}-\d{2}$/.test(extractedData.deadline)) {
          // Already ISO format
          deadlineISO = extractedData.deadline
        }
      } catch (e) {
        console.error('Failed to parse deadline:', extractedData.deadline)
      }
    }

    const jobListing: JobListing = {
      title: extractedData.title || 'Unknown Title',
      company: extractedData.company || 'Unknown Company',
      location: extractedData.location || 'Unknown Location',
      url: jobUrl,
      source: 'FINN',
      description: extractedData.description || undefined,
      contact_person: extractedData.contact_person || undefined,
      contact_email: extractedData.contact_email || undefined,
      contact_phone: extractedData.contact_phone || undefined,
      deadline: deadlineISO,
      posted_date: undefined,
    }

    return jobListing

  } catch (error) {
    console.error('❌ AI extraction failed:', error)
    throw new Error(`Failed to extract job details with AI: ${error.message}`)
  }
}

/**
 * Extracts detailed information from a single job listing page
 */
async function extractJobDetails(jobUrl: string): Promise<JobListing> {
  console.log('📄 Fetching job details:', jobUrl)

  const response = await fetch(jobUrl, {
    headers: {
      'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
    },
  })

  if (!response.ok) {
    throw new Error(`Failed to fetch job page: ${response.status}`)
  }

  const html = await response.text()

  // Use AI to extract job details (more reliable than selectors)
  return await extractJobDetailsWithAI(html, jobUrl)
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
    return { score: 0, summary: 'No profile available for analysis' }
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
      relevance_summary: "короткий текстовий висновок (1-2 речення)",
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

/**
 * Save job to database (insert new or update existing)
 */
async function saveJobToDatabase(
  supabaseClient: any,
  userId: string,
  job: JobListing,
  relevanceScore?: number,
  relevanceSummary?: string
) {
  console.log('💾 Saving job to database:', job.title)

  // Check if job already exists
  const { data: existing } = await supabaseClient
    .from('jobs')
    .select('id')
    .eq('url', job.url)
    .eq('user_id', userId)
    .single()

  if (existing) {
    console.log('🔄 Job already exists, updating with new details:', job.url)

    // Update existing job with fresh data
    const updateData: any = {
      title: job.title,
      company: job.company,
      location: job.location,
      description: job.description,
      contact_person: job.contact_person,
      contact_email: job.contact_email,
      contact_phone: job.contact_phone,
      deadline: job.deadline,
      updated_at: new Date().toISOString(),
    }

    // Add relevance data if provided
    if (relevanceScore !== undefined) {
      updateData.relevance_score = relevanceScore
    }
    if (relevanceSummary) {
      updateData.ai_recommendation = relevanceSummary
    }

    const { error: updateError } = await supabaseClient
      .from('jobs')
      .update(updateData)
      .eq('id', existing.id)

    if (updateError) {
      console.error('❌ Database update error:', updateError)
      throw updateError
    }

    console.log('✅ Job updated with ID:', existing.id)
    return { id: existing.id, created: false, updated: true }
  }

  // Insert new job
  const insertData: any = {
    user_id: userId,
    title: job.title,
    company: job.company,
    location: job.location,
    url: job.url,
    source: job.source,
    description: job.description,
    contact_person: job.contact_person,
    contact_email: job.contact_email,
    contact_phone: job.contact_phone,
    deadline: job.deadline,
    status: 'NEW',
    discovered_at: new Date().toISOString(),
  }

  // Add relevance data if provided
  if (relevanceScore !== undefined) {
    insertData.relevance_score = relevanceScore
  }
  if (relevanceSummary) {
    insertData.ai_recommendation = relevanceSummary
  }

  const { data, error } = await supabaseClient
    .from('jobs')
    .insert(insertData)
    .select('id')
    .single()

  if (error) {
    console.error('❌ Database insert error:', error)
    throw error
  }

  console.log('✅ Job created with ID:', data.id)
  return { id: data.id, created: true, updated: false }
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

    const body = await req.json()
    const { searchUrl, jobUrls, userId } = body

    if (!userId) {
      throw new Error('Missing userId parameter')
    }

    let results = {
      jobUrlsExtracted: 0,
      jobsScraped: 0,
      jobsSaved: 0,
      jobsUpdated: 0,
      jobsSkipped: 0,
      jobs: [] as any[],
    }

    // MODE 1: Extract job URLs from search page
    if (searchUrl) {
      console.log('🔍 MODE 1: Extracting job URLs from search page')
      const extractedUrls = await extractJobUrlsFromSearchPage(searchUrl)
      results.jobUrlsExtracted = extractedUrls.length

      // Scrape details from each URL
      console.log(`🕷️  Starting to scrape ${extractedUrls.length} jobs...`)

      for (const url of extractedUrls) {
        try {
          const jobDetails = await extractJobDetails(url)
          results.jobsScraped++

          const saveResult = await saveJobToDatabase(supabaseClient, userId, jobDetails)

          if (saveResult.created) {
            results.jobsSaved++
            results.jobs.push({ id: saveResult.id, ...jobDetails })
          } else if (saveResult.updated) {
            results.jobsUpdated++
            results.jobs.push({ id: saveResult.id, ...jobDetails })
          } else {
            results.jobsSkipped++
          }

          // Rate limiting - wait 1 second between requests
          await new Promise(resolve => setTimeout(resolve, 1000))

        } catch (error) {
          console.error(`❌ Error scraping ${url}:`, error)
        }
      }
    }

    // MODE 2: Scrape specific job URLs
    if (jobUrls && Array.isArray(jobUrls)) {
      console.log('🔍 MODE 2: Scraping specific job URLs with relevance analysis')

      for (const url of jobUrls) {
        try {
          // Step 1: Extract job details
          const jobDetails = await extractJobDetails(url)
          results.jobsScraped++

          // Step 2: Analyze relevance to user profile
          const relevanceAnalysis = await analyzeJobRelevance(supabaseClient, userId, jobDetails)

          // Step 3: Save with relevance data
          const saveResult = await saveJobToDatabase(
            supabaseClient,
            userId,
            jobDetails,
            relevanceAnalysis.score,
            relevanceAnalysis.summary
          )

          if (saveResult.created) {
            results.jobsSaved++
            results.jobs.push({ id: saveResult.id, ...jobDetails })
          } else if (saveResult.updated) {
            results.jobsUpdated++
            results.jobs.push({ id: saveResult.id, ...jobDetails })
          } else {
            results.jobsSkipped++
          }

          // Rate limiting (2 seconds due to 2 AI calls)
          await new Promise(resolve => setTimeout(resolve, 2000))

        } catch (error) {
          console.error(`❌ Error scraping ${url}:`, error)
        }
      }
    }

    return new Response(
      JSON.stringify({
        success: true,
        ...results,
        message: `Scraped ${results.jobsScraped} jobs: ${results.jobsSaved} new, ${results.jobsUpdated} updated, ${results.jobsSkipped} unchanged`,
      }),
      {
        headers: { ...corsHeaders, 'Content-Type': 'application/json' },
        status: 200,
      }
    )

  } catch (error) {
    console.error('Error:', error)
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

// Redeployed with AI extraction 2025-11-12-14-54-27
