-- Update jobs table to add AI relevance fields
-- Run this after jobs table is created

-- Add relevance_score column (0-100)
ALTER TABLE jobs
ADD COLUMN IF NOT EXISTS relevance_score INTEGER DEFAULT 0 CHECK (relevance_score >= 0 AND relevance_score <= 100);

-- Add relevance_reasons array (why job is relevant)
ALTER TABLE jobs
ADD COLUMN IF NOT EXISTS relevance_reasons TEXT[] DEFAULT ARRAY[]::TEXT[];

-- Add AI recommendation (APPLY, REVIEW, SKIP)
ALTER TABLE jobs
ADD COLUMN IF NOT EXISTS ai_recommendation TEXT DEFAULT 'PENDING' CHECK (ai_recommendation IN ('APPLY', 'REVIEW', 'SKIP', 'PENDING'));

-- Add analyzed_at timestamp
ALTER TABLE jobs
ADD COLUMN IF NOT EXISTS analyzed_at TIMESTAMPTZ;

-- Create index for filtering by relevance
CREATE INDEX IF NOT EXISTS idx_jobs_relevance_score ON jobs(relevance_score DESC);
CREATE INDEX IF NOT EXISTS idx_jobs_ai_recommendation ON jobs(ai_recommendation);
CREATE INDEX IF NOT EXISTS idx_jobs_user_relevance ON jobs(user_id, relevance_score DESC);

-- Comments
COMMENT ON COLUMN jobs.relevance_score IS 'AI-calculated relevance score from 0-100%';
COMMENT ON COLUMN jobs.relevance_reasons IS 'Array of reasons why this job is relevant';
COMMENT ON COLUMN jobs.ai_recommendation IS 'AI recommendation: APPLY (80-100%), REVIEW (50-79%), SKIP (0-49%)';
COMMENT ON COLUMN jobs.analyzed_at IS 'Timestamp when AI analysis was completed';

-- Grant permissions (if needed for service role)
-- GRANT SELECT, UPDATE ON jobs TO service_role;
