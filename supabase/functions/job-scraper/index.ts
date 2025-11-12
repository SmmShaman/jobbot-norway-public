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
  const document = new DOMParser().parseFromString(html, 'text/html')

  // Extract job details (FINN.no 2025 structure)
  const title = document.querySelector('h1')?.textContent?.trim() || 'Unknown Title'

  // Extract company from JSON-LD structured data (most reliable)
  let company = 'Unknown Company'
  const scriptTags = document.querySelectorAll('script[type="application/ld+json"]')
  for (const script of Array.from(scriptTags)) {
    try {
      const data = JSON.parse(script.textContent || '{}')
      if (data['@type'] === 'JobPosting' && data.hiringOrganization?.name) {
        company = data.hiringOrganization.name
        break
      }
    } catch (e) {
      // Skip invalid JSON
    }
  }

  // Fallback: look for strong tag near "Arbeidsgiver" or similar
  if (company === 'Unknown Company') {
    const strongTags = document.querySelectorAll('strong')
    for (const strong of Array.from(strongTags)) {
      const text = strong.textContent?.trim() || ''
      // Skip breadcrumbs and navigation
      if (text.length > 2 && text.length < 100 &&
          !text.includes('Her er du') &&
          !text.includes('FINN') &&
          !text.includes('Jobb')) {
        company = text
        break
      }
    }
  }

  // Location is in dd elements, look for one with address pattern
  const ddElements = document.querySelectorAll('dd')
  let location = 'Unknown Location'
  for (const dd of Array.from(ddElements)) {
    const text = dd.textContent?.trim() || ''
    // Look for Norwegian postal codes (4 digits followed by city name)
    if (/\d{4}\s+[A-ZÆØÅ]/.test(text)) {
      location = text
      break
    }
  }

  // Fallback to any dd that looks like an address
  if (location === 'Unknown Location') {
    for (const dd of Array.from(ddElements)) {
      const text = dd.textContent?.trim() || ''
      if (text.length > 5 && text.length < 100 && !text.includes('@')) {
        location = text
        break
      }
    }
  }

  // Extract description from li elements
  const listItems = document.querySelectorAll('li')
  const descriptionParts: string[] = []
  for (const li of Array.from(listItems)) {
    const text = li.textContent?.trim()
    if (text && text.length > 10 && !text.includes('Frist')) {
      descriptionParts.push(text)
    }
  }
  const description = descriptionParts.slice(0, 20).join('\n').substring(0, 5000)

  // Extract contact person from dt/dd pairs
  let contactPerson: string | undefined
  const dtElements = document.querySelectorAll('dt')
  for (const dt of Array.from(dtElements)) {
    if (dt.textContent?.includes('Kontaktperson')) {
      const dd = dt.nextElementSibling
      if (dd && dd.tagName === 'DD') {
        contactPerson = dd.textContent?.trim()
        break
      }
    }
  }

  // Extract email (look for mailto links or email pattern)
  const contactEmail = document.querySelector('a[href^="mailto:"]')?.getAttribute('href')?.replace('mailto:', '') ||
                       html.match(/([a-zA-Z0-9._-]+@[a-zA-Z0-9._-]+\.[a-zA-Z0-9_-]+)/)?.[1]

  // Extract phone (look for Norwegian phone format)
  const contactPhone = document.querySelector('a[href^="tel:"]')?.textContent?.trim() ||
                       html.match(/(\+47[\s\d]{8,12})/)?.[1]

  // Extract deadline (look for "Frist" in li elements)
  let deadline: string | undefined
  for (const li of Array.from(listItems)) {
    const text = li.textContent?.trim() || ''
    if (text.includes('Frist')) {
      deadline = text.replace('Frist', '').trim()
      break
    }
  }

  // Extract posted date (not easily available)
  const postedDate: string | undefined = undefined

  const jobListing: JobListing = {
    title,
    company,
    location,
    url: jobUrl,
    source: 'FINN',
    description,
    contact_person: contactPerson,
    contact_email: contactEmail,
    contact_phone: contactPhone,
    deadline,
    posted_date: postedDate,
  }

  console.log('✅ Extracted job details:', { title, company, location })
  return jobListing
}

/**
 * Save job to database
 */
async function saveJobToDatabase(supabaseClient: any, userId: string, job: JobListing) {
  console.log('💾 Saving job to database:', job.title)

  // Check if job already exists
  const { data: existing } = await supabaseClient
    .from('jobs')
    .select('id')
    .eq('url', job.url)
    .eq('user_id', userId)
    .single()

  if (existing) {
    console.log('⚠️  Job already exists, skipping:', job.url)
    return { id: existing.id, created: false }
  }

  // Insert new job
  const { data, error } = await supabaseClient
    .from('jobs')
    .insert({
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
    })
    .select('id')
    .single()

  if (error) {
    console.error('❌ Database error:', error)
    throw error
  }

  console.log('✅ Job saved with ID:', data.id)
  return { id: data.id, created: true }
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
      console.log('🔍 MODE 2: Scraping specific job URLs')

      for (const url of jobUrls) {
        try {
          const jobDetails = await extractJobDetails(url)
          results.jobsScraped++

          const saveResult = await saveJobToDatabase(supabaseClient, userId, jobDetails)

          if (saveResult.created) {
            results.jobsSaved++
            results.jobs.push({ id: saveResult.id, ...jobDetails })
          } else {
            results.jobsSkipped++
          }

          // Rate limiting
          await new Promise(resolve => setTimeout(resolve, 1000))

        } catch (error) {
          console.error(`❌ Error scraping ${url}:`, error)
        }
      }
    }

    return new Response(
      JSON.stringify({
        success: true,
        ...results,
        message: `Scraped ${results.jobsScraped} jobs, saved ${results.jobsSaved} new, skipped ${results.jobsSkipped} duplicates`,
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
