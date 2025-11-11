/**
 * Extract Text Edge Function
 * Uses unpdf to extract clean text from PDF files for preview
 * Does NOT analyze with AI - just returns raw text
 */

import { serve } from "https://deno.land/std@0.168.0/http/server.ts"
import { createClient } from 'https://esm.sh/@supabase/supabase-js@2'
import { extractText, getDocumentProxy } from 'https://esm.sh/unpdf@0.12.1'

const corsHeaders = {
  'Access-Control-Allow-Origin': '*',
  'Access-Control-Allow-Headers': 'authorization, x-client-info, apikey, content-type',
}

async function extractTextFromPDF(fileUrl: string): Promise<{ text: string; pages: number }> {
  console.log('Downloading PDF from:', fileUrl)

  const response = await fetch(fileUrl)
  if (!response.ok) {
    throw new Error(`Failed to download file: ${response.statusText}`)
  }

  const arrayBuffer = await response.arrayBuffer()
  const uint8Array = new Uint8Array(arrayBuffer)

  console.log('Parsing PDF with unpdf...')

  // Parse PDF with unpdf
  const pdf = await getDocumentProxy(uint8Array)

  // Extract text from all pages
  const { totalPages, text } = await extractText(pdf, { mergePages: true })

  console.log(`Extracted ${text.length} characters from ${totalPages} pages`)

  return { text, pages: totalPages }
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
    const { user_id, resume_urls } = body

    if (!user_id || !resume_urls || !Array.isArray(resume_urls)) {
      throw new Error('Missing user_id or resume_urls')
    }

    console.log(`Extracting text from ${resume_urls.length} PDFs for user: ${user_id}`)

    // Extract text from all PDFs
    const results = await Promise.all(
      resume_urls.map(async (url: string) => {
        try {
          const { text, pages } = await extractTextFromPDF(url)
          const fileName = url.split('/').pop() || 'unknown.pdf'

          return {
            fileName,
            url,
            text,
            pages,
            success: true
          }
        } catch (error) {
          console.error(`Error extracting from ${url}:`, error)
          return {
            fileName: url.split('/').pop() || 'unknown.pdf',
            url,
            text: `[Error: ${error.message}]`,
            pages: 0,
            success: false,
            error: error.message
          }
        }
      })
    )

    // Combine all texts
    const combinedText = results.map(r =>
      `\n\n=== РЕЗЮМЕ: ${r.fileName} (${r.pages} сторінок) ===\n${r.text}\n=== КІНЕЦЬ ===\n`
    ).join('\n\n---\n\n')

    const totalChars = results.reduce((sum, r) => sum + r.text.length, 0)
    const successCount = results.filter(r => r.success).length

    return new Response(
      JSON.stringify({
        success: true,
        combinedText,
        results,
        stats: {
          totalResumes: resume_urls.length,
          successCount,
          failedCount: resume_urls.length - successCount,
          totalCharacters: totalChars
        }
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
