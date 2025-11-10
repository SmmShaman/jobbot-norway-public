/**
 * PDF Parser Edge Function
 * Parses uploaded resume PDF/DOCX and extracts structured profile using Azure OpenAI
 */

import { serve } from "https://deno.land/std@0.168.0/http/server.ts"
import { createClient } from 'https://esm.sh/@supabase/supabase-js@2'

// CORS headers
const corsHeaders = {
  'Access-Control-Allow-Origin': '*',
  'Access-Control-Allow-Headers': 'authorization, x-client-info, apikey, content-type',
}

interface ParsedProfile {
  personal_info: {
    name: string
    email: string
    phone: string
    location: string
  }
  professional_summary: string
  work_experience: Array<{
    company: string
    position: string
    duration: string
    responsibilities: string[]
  }>
  education: Array<{
    degree: string
    institution: string
    year: string
  }>
  skills: {
    technical: string[]
    languages: string[]
    soft_skills: string[]
  }
  certifications: string[]
  career_objective: string
}

async function parseResumeWithAI(resumeText: string): Promise<ParsedProfile> {
  const azureEndpoint = Deno.env.get('AZURE_OPENAI_ENDPOINT')!
  const azureApiKey = Deno.env.get('AZURE_OPENAI_API_KEY')!
  const deploymentName = Deno.env.get('AZURE_OPENAI_DEPLOYMENT')!

  const prompt = `
Analyze this resume and extract structured information.

Resume text:
${resumeText.substring(0, 4000)}

Extract and return ONLY valid JSON with this structure:
{
  "personal_info": {
    "name": "Full Name",
    "email": "email@example.com",
    "phone": "phone number",
    "location": "current location"
  },
  "professional_summary": "Brief professional summary",
  "work_experience": [
    {
      "company": "Company Name",
      "position": "Job Title",
      "duration": "2020-2023",
      "responsibilities": ["responsibility1", "responsibility2"]
    }
  ],
  "education": [
    {
      "degree": "Degree Name",
      "institution": "University Name",
      "year": "2020"
    }
  ],
  "skills": {
    "technical": ["skill1", "skill2"],
    "languages": ["Norwegian", "English"],
    "soft_skills": ["leadership", "communication"]
  },
  "certifications": ["cert1", "cert2"],
  "career_objective": "What type of job they're seeking"
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

  // Clean JSON response (remove markdown formatting)
  const cleanedContent = content
    .replace(/```json\n?/g, '')
    .replace(/```\n?/g, '')
    .trim()

  return JSON.parse(cleanedContent)
}

async function extractTextFromPDF(fileUrl: string): Promise<string> {
  // For Edge Functions, we'll use a PDF parsing library
  // For now, return placeholder - will implement with proper PDF parser
  // Options: pdf-parse, pdfjs-dist, or call external service

  console.log('Downloading PDF from:', fileUrl)

  const response = await fetch(fileUrl)
  const arrayBuffer = await response.arrayBuffer()

  // TODO: Implement actual PDF parsing
  // For now, return mock text
  return "Sample resume text extracted from PDF"
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

    const { file_url, user_id } = await req.json()

    if (!file_url || !user_id) {
      throw new Error('Missing file_url or user_id')
    }

    console.log('Parsing resume for user:', user_id)

    // 1. Extract text from PDF
    const resumeText = await extractTextFromPDF(file_url)

    // 2. Parse with Azure OpenAI
    const parsedProfile = await parseResumeWithAI(resumeText)

    // 3. Save to database
    const { data, error } = await supabaseClient
      .from('user_profiles')
      .upsert({
        user_id,
        full_name: parsedProfile.personal_info.name,
        email: parsedProfile.personal_info.email,
        phone: parsedProfile.personal_info.phone,
        location: parsedProfile.personal_info.location,
        professional_summary: parsedProfile.professional_summary,
        career_objective: parsedProfile.career_objective,
        work_experience: parsedProfile.work_experience,
        education: parsedProfile.education,
        technical_skills: parsedProfile.skills.technical,
        languages: parsedProfile.skills.languages,
        soft_skills: parsedProfile.skills.soft_skills,
        certifications: parsedProfile.certifications,
        resume_file_url: file_url,
        parsed_at: new Date().toISOString(),
      })
      .select()
      .single()

    if (error) throw error

    return new Response(
      JSON.stringify({
        success: true,
        profile: data,
        message: 'Resume parsed successfully'
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
