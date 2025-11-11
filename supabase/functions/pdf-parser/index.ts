/**
 * ENHANCED PDF Parser Edge Function
 * Supports MULTIPLE resumes (up to 5) and creates comprehensive profile
 * Uses customizable AI prompt for complete profile generation
 * Uses unpdf library for high-quality PDF text extraction
 */

import { serve } from "https://deno.land/std@0.168.0/http/server.ts"
import { createClient } from 'https://esm.sh/@supabase/supabase-js@2'
import { extractText, getDocumentProxy } from 'https://esm.sh/unpdf@0.12.1'

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

async function parseMultipleResumesWithAI(
  resumes: Array<{ content: string; filename: string }>,
  currentUser: string,
  customSystemPrompt?: string,
  customUserPrompt?: string
): Promise<any> {
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

  // ============================================================
  // CUSTOM PROMPT LOGIC: If user provides custom prompts, use ONLY those
  // Otherwise, use default comprehensive JSON generation
  // ============================================================

  let systemPrompt: string
  let finalUserPrompt: string

  if (customUserPrompt) {
    // USER CUSTOM MODE: Use ONLY custom prompts without any defaults
    systemPrompt = customSystemPrompt || ENHANCED_PROMPT_SYSTEM

    // Build simple user prompt with ONLY custom instructions
    finalUserPrompt = `${customUserPrompt}

INPUT DATA - ${resumes.length} RESUME FILES:
${detailedResumeText}`

    console.log('🎨 CUSTOM PROMPT MODE: Using user-defined prompts WITHOUT default JSON structure')

  } else {
    // DEFAULT MODE: Use comprehensive JSON generation with all rules
    systemPrompt = customSystemPrompt || ENHANCED_PROMPT_SYSTEM

    const userPromptPrefix = `Create a MAXIMALLY COMPLETE professional JSON profile for Norwegian job applications.

This profile will be used for automated job applications in Norway, so ensure:
- Phone numbers follow Norwegian format (+47 XXX XX XXX)
- Include Norwegian language skills (minimum B1 level)
- Address should be Norwegian city unless clearly stated otherwise
- Industries should include relevant Norwegian market sectors
- All technical skills should be comprehensively categorized
- Combine ALL information from ALL resumes into ONE comprehensive profile`

    finalUserPrompt = `TASK: Create a MAXIMALLY COMPLETE professional JSON profile for ${currentUser} for Norwegian job applications.

${userPromptPrefix}

${ENHANCED_RULES}

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

    console.log('📋 DEFAULT MODE: Using comprehensive JSON structure generation')
  }

  // ============ DETAILED LOGGING FOR DEBUGGING ============
  console.log('========================================')
  console.log('📋 AI PROMPTS BEING SENT TO AZURE OPENAI:')
  console.log('========================================')

  console.log('🔧 Prompt Mode:', customUserPrompt ? '🎨 CUSTOM (User-defined)' : '📋 DEFAULT (JSON structure)')
  console.log('  - customSystemPrompt exists:', !!customSystemPrompt)
  console.log('  - customUserPrompt exists:', !!customUserPrompt)

  console.log('\n✏️ SYSTEM PROMPT:')
  console.log('First 300 chars:', systemPrompt.substring(0, 300) + '...')

  console.log('\n✏️ USER PROMPT:')
  console.log('First 500 chars:', finalUserPrompt.substring(0, 500) + '...')

  if (customUserPrompt) {
    console.log('\n⚠️  IMPORTANT: Custom prompt mode - NO default JSON structure enforced')
    console.log('AI will follow ONLY the custom instructions provided by user')
  }

  console.log('\n📊 FINAL PROMPTS STATS:')
  console.log('  - System prompt length:', systemPrompt.length, 'chars')
  console.log('  - User prompt length:', finalUserPrompt.length, 'chars')
  console.log('  - Total prompt length:', systemPrompt.length + finalUserPrompt.length, 'chars')

  console.log('\n🚀 SENDING TO AZURE OPENAI:')
  console.log('  - Endpoint:', azureEndpoint)
  console.log('  - Deployment:', deploymentName)
  console.log('  - Temperature: 0.3')
  console.log('  - Max tokens: 8000')
  console.log('========================================')
  // ============ END LOGGING ============

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
          { role: 'system', content: systemPrompt },
          { role: 'user', content: finalUserPrompt }
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

  // If using custom prompts, ALWAYS return raw content (preserve user's structure)
  if (customUserPrompt) {
    console.log('🎨 Custom prompt mode: Returning RAW AI response')
    console.log('Response preview (first 500 chars):', content.substring(0, 500))

    // ALWAYS return as raw response for custom prompts
    // Even if it's valid JSON, we want to preserve the exact structure user requested
    return {
      rawResponse: content,
      customPromptUsed: true,
      note: 'Custom prompt response - preserving exact AI output'
    }
  }

  // Default mode: expect JSON
  const cleanedContent = content
    .replace(/```json\n?/g, '')
    .replace(/```\n?/g, '')
    .trim()

  return JSON.parse(cleanedContent)
}

async function extractTextFromPDF(fileUrl: string): Promise<string> {
  console.log('Downloading PDF from:', fileUrl)

  try {
    // Download PDF file
    const response = await fetch(fileUrl)
    if (!response.ok) {
      throw new Error(`Failed to download file: ${response.statusText}`)
    }

    const arrayBuffer = await response.arrayBuffer()
    const uint8Array = new Uint8Array(arrayBuffer)

    console.log('Parsing PDF with unpdf library...')

    // Parse PDF with unpdf (industry-standard PDF.js based parser)
    const pdf = await getDocumentProxy(uint8Array)

    // Extract text from all pages
    const { totalPages, text } = await extractText(pdf, { mergePages: true })

    console.log(`Successfully extracted text from ${totalPages} pages`)
    console.log(`Extracted ${text.length} characters`)

    return text
  } catch (error) {
    console.error('PDF extraction error:', error)
    // Fallback error message with more context
    throw new Error(`Failed to extract text from PDF: ${error.message}`)
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

    // Fetch user settings to get custom AI prompts
    const { data: userSettings } = await supabaseClient
      .from('user_settings')
      .select('custom_system_prompt, custom_user_prompt')
      .eq('user_id', finalUserId)
      .single()

    const customSystemPrompt = userSettings?.custom_system_prompt
    const customUserPrompt = userSettings?.custom_user_prompt

    console.log('Using custom prompts:', {
      hasCustomSystem: !!customSystemPrompt,
      hasCustomUser: !!customUserPrompt
    })

    // Extract text from all PDFs
    const resumes = await Promise.all(
      urls.map(async (url, index) => ({
        content: await extractTextFromPDF(url),
        filename: paths[index] || `resume_${index + 1}.pdf`
      }))
    )

    // Parse with Azure OpenAI (combine all resumes)
    const parsedProfile = await parseMultipleResumesWithAI(
      resumes,
      finalCurrentUser,
      customSystemPrompt,
      customUserPrompt
    )

    // Map to database schema
    let profileData: any

    // Check if this is a custom prompt response (non-standard format)
    if (parsedProfile.customPromptUsed && parsedProfile.rawResponse) {
      console.log('⚠️  Custom prompt response detected - storing as raw text in professional_summary')

      // Store raw response in professional_summary for custom prompts
      profileData = {
        user_id: finalUserId,
        full_name: finalCurrentUser,
        email: '',
        phone: '',
        location: '',
        professional_summary: parsedProfile.rawResponse, // Store full AI response here
        career_objective: 'Custom AI Profile Analysis',
        total_experience_years: 0,
        work_experience: [],
        education: [],
        technical_skills: [],
        languages: [],
        soft_skills: [],
        certifications: [],
        resume_file_url: urls[0],
        parsed_at: new Date().toISOString(),
      }
    } else {
      // Standard JSON profile format
      profileData = {
        user_id: finalUserId,
        full_name: parsedProfile.personalInfo?.fullName || parsedProfile.fullName || '',
        email: parsedProfile.personalInfo?.email || parsedProfile.email || '',
        phone: parsedProfile.personalInfo?.phone || parsedProfile.phone || '',
        location: parsedProfile.personalInfo?.address?.city || parsedProfile.location || '',
        professional_summary: parsedProfile.professionalSummary || parsedProfile.professional_summary || '',
        career_objective: parsedProfile.careerStats?.currentRole || parsedProfile.career_objective || '',
        total_experience_years: parsedProfile.careerStats?.totalExperienceYears || parsedProfile.total_experience_years || 0,
        work_experience: parsedProfile.workExperience || parsedProfile.work_experience || [],
        education: parsedProfile.education || [],
        technical_skills: parsedProfile.technical_skills || [
          ...(parsedProfile.technicalSkills?.programmingLanguages || []),
          ...(parsedProfile.technicalSkills?.frameworks || []),
          ...(parsedProfile.technicalSkills?.databases || []),
          ...(parsedProfile.technicalSkills?.aiTools || []),
          ...(parsedProfile.technicalSkills?.other || [])
        ],
        languages: parsedProfile.languages?.map((l: any) =>
          typeof l === 'string' ? l : `${l.language} (${l.proficiencyLevel})`
        ) || [],
        soft_skills: parsedProfile.softSkills || parsedProfile.soft_skills || [],
        certifications: parsedProfile.certifications || [],
        resume_file_url: urls[0], // Store first resume URL
        parsed_at: new Date().toISOString(),
      }
    }

    // Save to database using upsert (handles both INSERT and UPDATE)
    console.log('Attempting to save profile for user:', finalUserId)

    // First, delete existing profile to avoid conflicts
    const { error: deleteError } = await supabaseClient
      .from('user_profiles')
      .delete()
      .eq('user_id', finalUserId)

    if (deleteError) {
      console.log('Delete error (might not exist):', deleteError.message)
    } else {
      console.log('Existing profile deleted')
    }

    // Insert new profile
    const { data, error } = await supabaseClient
      .from('user_profiles')
      .insert(profileData)
      .select()
      .single()

    if (error) {
      console.error('Database error:', error)
      throw error
    }

    console.log('Profile saved successfully:', data?.id)

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
