/**
 * ENHANCED PDF Parser Edge Function
 * Supports MULTIPLE resumes (up to 5) and creates comprehensive profile
 * Uses customizable AI prompt for complete profile generation
 */

import { serve } from "https://deno.land/std@0.168.0/http/server.ts"
import { createClient } from 'https://esm.sh/@supabase/supabase-js@2'

// CORS headers
const corsHeaders = {
  'Access-Control-Allow-Origin': '*',
  'Access-Control-Allow-Headers': 'authorization, x-client-info, apikey, content-type',
}

// ENHANCED PROMPT for complete profile generation
const ENHANCED_PROMPT_SYSTEM = `You are an EXPERT HR Data Analyst specializing in creating COMPLETE, DETAILED professional profiles for Norwegian job applications.

Your mission: Extract EVERY possible detail from resumes and CREATE A FULLY POPULATED profile that leaves NO FIELD EMPTY. When information is missing, make INTELLIGENT INFERENCES based on context, career patterns, and Norwegian job market standards.

NEVER return incomplete profiles. EVERY field must contain meaningful, realistic data.`

const ENHANCED_RULES = `
MANDATORY INSTRUCTIONS FOR COMPLETE PROFILE GENERATION:

CRITICAL REQUIREMENTS:
1) EVERY FIELD MUST BE FILLED - If data is missing from resume, make INTELLIGENT INFERENCES or use REASONABLE DEFAULTS
2) NO EMPTY STRINGS OR NULL VALUES - All fields must contain meaningful data
3) COPY VERBATIM when data exists, but INTELLIGENTLY COMPLETE when missing
4) PRESERVE original language (Norwegian/English/Ukrainian) but ensure completeness

PERSONAL INFO COMPLETION RULES:
5) fullName: Extract from resume header/contact section
6) email: Extract from contact info. If missing, construct: firstname.lastname@email.com
7) phone: Extract from contact. If missing, use format: "+47 XXX XX XXX"
8) website: Extract from contact/portfolio links
9) address.city: Extract from location/contact. If missing, infer from job locations or use "Oslo"
10) address.country: Extract from context. If missing, use "Norway"

CAREER STATS COMPLETION:
11) currentRole: Extract from latest work experience position title
12) totalExperienceYears: Calculate from all work experience dates OR estimate from career span
13) industries: Extract from all work experience companies/sectors

WORK EXPERIENCE ENHANCEMENT:
14) For EACH role, ensure ALL fields are populated
15) technologiesUsed: Include ALL tools/technologies mentioned for each role

TECHNICAL SKILLS COMPREHENSIVE MAPPING:
16) aiTools: Extract AI/ML tools (ChatGPT, Claude, Azure OpenAI, etc.)
17) programmingLanguages: Extract languages (JavaScript, Python, TypeScript, etc.)
18) frameworks: Extract frameworks (React, Vite, Expo, etc.)
19) databases: Extract databases (Supabase, PostgreSQL, etc.)
20) cloudPlatforms: Extract cloud services (Azure, AWS, etc.)
21) developmentTools: Extract dev tools (Git, VS Code, etc.)
22) other: Include everything else (Stripe, Bolt.new, etc.)

LANGUAGE SKILLS INTELLIGENT COMPLETION:
23) If Norwegian mentioned → proficiencyLevel: "B1" or extract exact level
24) If English mentioned → proficiencyLevel: "B1" or extract exact level
25) If Ukrainian/Russian mentioned → proficiencyLevel: "Native"
26) ADD MISSING LANGUAGES based on context

EDUCATION MANDATORY COMPLETION:
27) institution: Extract school names
28) degree: Extract degree type, include Norwegian qualifications like "NOKUT-godkjent"
29) field: Extract field of study
30) graduationYear: Extract year

INTELLIGENT DATA INFERENCE RULES:
31) If email missing but name available → construct: firstname.lastname@domain.com
32) If phone missing → use Norwegian format: "+47 XXX XX XXX"
33) If experience years unclear → estimate from date ranges
34) If Norwegian language not listed but applying to Norwegian jobs → add Norwegian B1

VALIDATION AND COMPLETION:
35) NEVER leave required arrays empty - minimum 1 item per array
36) NEVER leave personalInfo fields empty - use intelligent defaults
37) ENSURE workExperience has at least 1 complete entry
38) VERIFY all careerStats fields are populated with realistic data
`

async function parseMultipleResumesWithAI(resumes: Array<{ content: string; filename: string }>, currentUser: string): Promise<any> {
  const azureEndpoint = Deno.env.get('AZURE_OPENAI_ENDPOINT')!
  const azureApiKey = Deno.env.get('AZURE_OPENAI_API_KEY')!
  const deploymentName = Deno.env.get('AZURE_OPENAI_DEPLOYMENT')!

  // Build corpus from all resumes
  const detailedResumeText = resumes.map((resume, index) => {
    return `=== RESUME ${index + 1} ===
FILE: ${resume.filename}
FULL TEXT (COPY VERBATIM):
${resume.content}
=== END RESUME ${index + 1} ===`
  }).join('\n\n')

  console.log(`Processing ${resumes.length} files for ${currentUser}`)
  console.log(`Total input length: ${detailedResumeText.length} chars`)

  const userPrompt = `TASK: Create a MAXIMALLY COMPLETE professional JSON profile for ${currentUser} for Norwegian job applications.

${ENHANCED_RULES}

CONTEXT: This profile will be used for automated job applications in Norway, so ensure:
- Phone numbers follow Norwegian format (+47 XXX XX XXX)
- Include Norwegian language skills (minimum B1 level)
- Address should be Norwegian city unless clearly stated otherwise
- Industries should include relevant Norwegian market sectors
- All technical skills should be comprehensively categorized

INPUT DATA - ${resumes.length} RESUME FILES:
${detailedResumeText}

OUTPUT REQUIREMENTS:
1. COMPLETE JSON profile with ALL fields populated
2. NO empty strings, null values, or missing data
3. Intelligent inference where data is missing
4. Norwegian job market optimized formatting
5. Combine ALL information from ALL resumes into ONE comprehensive profile

GENERATE COMPLETE JSON PROFILE (NO CODE FENCES):

{
  "personalInfo": {
    "fullName": "[EXTRACT or use currentUser]",
    "email": "[EXTRACT or construct]",
    "phone": "[EXTRACT or use +47 format]",
    "website": "[EXTRACT or construct LinkedIn URL]",
    "address": {
      "city": "[EXTRACT or use Oslo]",
      "country": "[EXTRACT or use Norway]"
    }
  },
  "professionalSummary": "[CREATE compelling 2-3 sentence summary from ALL resumes]",
  "workExperience": [
    {
      "company": "[NEVER empty]",
      "position": "[EXTRACT exact title]",
      "startDate": "[EXTRACT or estimate]",
      "endDate": "[EXTRACT, use 'Present' if current]",
      "responsibilities": "[MINIMUM 2-3 items]",
      "achievements": "[EXTRACT or infer]",
      "technologiesUsed": "[ALL tools mentioned]"
    }
  ],
  "technicalSkills": {
    "aiTools": "[Extract all AI tools from ALL resumes]",
    "programmingLanguages": "[Extract all languages from ALL resumes]",
    "frameworks": "[Extract all frameworks from ALL resumes]",
    "databases": "[Extract all databases from ALL resumes]",
    "cloudPlatforms": "[Extract all cloud from ALL resumes]",
    "developmentTools": "[Extract all dev tools from ALL resumes]",
    "other": "[Everything else from ALL resumes]"
  },
  "softSkills": "[EXTRACT all soft skills from ALL resumes]",
  "languages": [
    {
      "language": "Norwegian",
      "proficiencyLevel": "B1"
    },
    {
      "language": "English",
      "proficiencyLevel": "B1"
    }
  ],
  "education": [
    {
      "institution": "[EXTRACT from ALL resumes]",
      "degree": "[EXTRACT including NOKUT-godkjent]",
      "field": "[EXTRACT or infer]",
      "graduationYear": "[EXTRACT or estimate]"
    }
  ],
  "certifications": "[EXTRACT all from ALL resumes]",
  "interests": "[EXTRACT as array, minimum 3 items]",
  "careerStats": {
    "totalExperienceYears": "[CALCULATE from ALL work experience]",
    "currentRole": "[Latest position title]",
    "industries": "[ALL industries from ALL resumes]"
  },
  "location": "[City, Country format]",
  "preferredWorkFormat": "[Infer: Remote/Hybrid/On-site/Flexible]"
}

CRITICAL: Return ONLY the complete JSON object with ALL fields populated. Combine information from ALL ${resumes.length} resumes.`

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
          { role: 'system', content: ENHANCED_PROMPT_SYSTEM },
          { role: 'user', content: userPrompt }
        ],
        temperature: 0.3,
        max_tokens: 8000,
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

async function extractTextFromPDF(fileUrl: string): Promise<string> {
  console.log('Downloading file from:', fileUrl)

  try {
    const response = await fetch(fileUrl)
    if (!response.ok) {
      throw new Error(`Failed to download file: ${response.statusText}`)
    }

    const arrayBuffer = await response.arrayBuffer()
    const uint8Array = new Uint8Array(arrayBuffer)

    // Convert to text (basic extraction - for production use proper PDF parser)
    const decoder = new TextDecoder('utf-8')
    let text = decoder.decode(uint8Array)

    // Basic text cleaning
    text = text.replace(/[^\x20-\x7E\n\r\t\u00A0-\uFFFF]/g, ' ')

    return text
  } catch (error) {
    console.error('PDF extraction error:', error)
    return `[Error extracting text from ${fileUrl}]`
  }
}

serve(async (req) => {
  if (req.method === 'OPTIONS') {
    return new Response('ok', { headers: corsHeaders })
  }

  try {
    const supabaseClient = createClient(
      Deno.env.get('SUPABASE_URL') ?? '',
      Deno.env.get('SUPABASE_SERVICE_ROLE_KEY') ?? '',
    )

    const body = await req.json()
    const { userId, user_id, resumeUrls, resumeUrl, storagePaths, storagePath, currentUser } = body

    // Support both old and new parameter names
    const finalUserId = userId || user_id
    const finalCurrentUser = currentUser || finalUserId

    if (!finalUserId) {
      throw new Error('Missing userId or user_id parameter')
    }

    // Support both single and multiple resumes
    let urls: string[] = []
    let paths: string[] = []

    if (resumeUrls && Array.isArray(resumeUrls)) {
      urls = resumeUrls
      paths = storagePaths || []
    } else if (resumeUrl) {
      urls = [resumeUrl]
      paths = storagePath ? [storagePath] : []
    } else {
      throw new Error('Missing resumeUrl(s) parameter')
    }

    console.log(`Parsing ${urls.length} resume(s) for user: ${finalUserId}`)

    // Extract text from all PDFs
    const resumes = await Promise.all(
      urls.map(async (url, index) => ({
        content: await extractTextFromPDF(url),
        filename: paths[index] || `resume_${index + 1}.pdf`
      }))
    )

    // Parse with Azure OpenAI (combine all resumes)
    const parsedProfile = await parseMultipleResumesWithAI(resumes, finalCurrentUser)

    // Map to database schema
    const profileData = {
      user_id: finalUserId,
      full_name: parsedProfile.personalInfo?.fullName || '',
      email: parsedProfile.personalInfo?.email || '',
      phone: parsedProfile.personalInfo?.phone || '',
      location: parsedProfile.personalInfo?.address?.city || '',
      professional_summary: parsedProfile.professionalSummary || '',
      career_objective: parsedProfile.careerStats?.currentRole || '',
      total_experience_years: parsedProfile.careerStats?.totalExperienceYears || 0,
      work_experience: parsedProfile.workExperience || [],
      education: parsedProfile.education || [],
      technical_skills: [
        ...(parsedProfile.technicalSkills?.programmingLanguages || []),
        ...(parsedProfile.technicalSkills?.frameworks || []),
        ...(parsedProfile.technicalSkills?.databases || []),
        ...(parsedProfile.technicalSkills?.aiTools || []),
        ...(parsedProfile.technicalSkills?.other || [])
      ],
      languages: parsedProfile.languages?.map((l: any) => `${l.language} (${l.proficiencyLevel})`) || [],
      soft_skills: parsedProfile.softSkills || [],
      certifications: parsedProfile.certifications || [],
      resume_file_url: urls[0], // Store first resume URL
      parsed_at: new Date().toISOString(),
    }

    // Save to database
    const { data, error } = await supabaseClient
      .from('user_profiles')
      .upsert(profileData, { onConflict: 'user_id' })
      .select()
      .single()

    if (error) {
      console.error('Database error:', error)
      throw error
    }

    return new Response(
      JSON.stringify({
        success: true,
        profile: data,
        resumesProcessed: resumes.length,
        message: `Successfully parsed ${resumes.length} resume(s) and created comprehensive profile`
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
        error: error.message || 'Unknown error'
      }),
      {
        headers: { ...corsHeaders, 'Content-Type': 'application/json' },
        status: 400,
      },
    )
  }
})
