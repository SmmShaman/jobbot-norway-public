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
import { parseHTML } from 'https://esm.sh/linkedom@0.16.8'

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
  const { document } = parseHTML(html)

  // FINN.no job listing selectors
  const jobLinks: string[] = []

  // Try multiple selectors (FINN.no structure may vary)
  const selectors = [
    'article.sf-search-ad a[href*="/job/fulltime/ad.html"]',
    'a[href*="/job/fulltime/ad.html"]',
    '.ads__unit__link[href*="/job/"]',
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
  const { document } = parseHTML(html)

  // Extract job details
  const title = document.querySelector('h1, .job-title, [class*="title"]')?.textContent?.trim() || 'Unknown Title'

  const company = document.querySelector('.company-name, [class*="company"], [class*="employer"]')?.textContent?.trim() ||
                  document.querySelector('a[href*="/company/"]')?.textContent?.trim() ||
                  'Unknown Company'

  const location = document.querySelector('.location, [class*="location"], [class*="address"]')?.textContent?.trim() ||
                   'Unknown Location'

  // Extract description
  const descriptionEl = document.querySelector('.job-description, [class*="description"], article')
  const description = descriptionEl?.textContent?.trim().substring(0, 5000) || ''

  // Extract contact information
  const contactPerson = document.querySelector('[class*="contact-person"], [class*="contact-name"]')?.textContent?.trim()

  const contactEmail = document.querySelector('a[href^="mailto:"]')?.getAttribute('href')?.replace('mailto:', '') ||
                       html.match(/([a-zA-Z0-9._-]+@[a-zA-Z0-9._-]+\.[a-zA-Z0-9_-]+)/)?.[1]

  const contactPhone = document.querySelector('a[href^="tel:"]')?.textContent?.trim() ||
                       html.match(/(\+47[\s\d]{8,12}|[\d]{8})/)?.[1]

  // Extract deadline
  const deadline = document.querySelector('[class*="deadline"], [class*="apply-by"]')?.textContent?.trim()

  // Extract posted date
  const postedDate = document.querySelector('[class*="published"], [class*="posted"]')?.textContent?.trim()

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
      scraped_at: new Date().toISOString(),
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
