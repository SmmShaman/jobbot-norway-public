-- Create jobs table for storing scraped job listings
CREATE TABLE IF NOT EXISTS jobs (
  id UUID DEFAULT gen_random_uuid() PRIMARY KEY,
  user_id UUID NOT NULL REFERENCES auth.users(id) ON DELETE CASCADE,

  -- Basic job info
  title TEXT NOT NULL,
  company TEXT,
  location TEXT,
  url TEXT NOT NULL,
  source TEXT NOT NULL DEFAULT 'FINN',

  -- Job details
  description TEXT,
  contact_person TEXT,
  contact_email TEXT,
  contact_phone TEXT,
  deadline TEXT,
  posted_date TEXT,

  -- Status tracking
  status TEXT DEFAULT 'NEW',
  relevance_score INTEGER,
  ai_recommendation TEXT,

  -- Metadata
  scraped_at TIMESTAMPTZ DEFAULT NOW(),
  created_at TIMESTAMPTZ DEFAULT NOW(),
  updated_at TIMESTAMPTZ DEFAULT NOW(),

  -- Unique constraint per user
  UNIQUE(user_id, url)
);

-- Create index for faster queries
CREATE INDEX IF NOT EXISTS idx_jobs_user_id ON jobs(user_id);
CREATE INDEX IF NOT EXISTS idx_jobs_status ON jobs(status);
CREATE INDEX IF NOT EXISTS idx_jobs_source ON jobs(source);
CREATE INDEX IF NOT EXISTS idx_jobs_scraped_at ON jobs(scraped_at DESC);

-- Enable RLS
ALTER TABLE jobs ENABLE ROW LEVEL SECURITY;

-- RLS Policies
CREATE POLICY "Users can view their own jobs"
  ON jobs FOR SELECT
  USING (auth.uid() = user_id);

CREATE POLICY "Users can insert their own jobs"
  ON jobs FOR INSERT
  WITH CHECK (auth.uid() = user_id);

CREATE POLICY "Users can update their own jobs"
  ON jobs FOR UPDATE
  USING (auth.uid() = user_id);

CREATE POLICY "Users can delete their own jobs"
  ON jobs FOR DELETE
  USING (auth.uid() = user_id);

-- Service role can do everything (for Edge Functions)
CREATE POLICY "Service role can manage all jobs"
  ON jobs FOR ALL
  USING (true)
  WITH CHECK (true);
