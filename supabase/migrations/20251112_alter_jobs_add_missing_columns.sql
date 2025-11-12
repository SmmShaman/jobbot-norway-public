-- Add missing columns to existing jobs table
-- Note: Table was created earlier with different structure

-- Add contact fields if they don't exist
ALTER TABLE jobs ADD COLUMN IF NOT EXISTS contact_person TEXT;
ALTER TABLE jobs ADD COLUMN IF NOT EXISTS contact_email TEXT;
ALTER TABLE jobs ADD COLUMN IF NOT EXISTS contact_phone TEXT;
ALTER TABLE jobs ADD COLUMN IF NOT EXISTS deadline TEXT;
ALTER TABLE jobs ADD COLUMN IF NOT EXISTS posted_date TEXT;

-- Add scraped_at if it doesn't exist (different from discovered_at)
ALTER TABLE jobs ADD COLUMN IF NOT EXISTS scraped_at TIMESTAMPTZ;

-- Set scraped_at to discovered_at for existing rows
UPDATE jobs SET scraped_at = discovered_at WHERE scraped_at IS NULL;

-- Add index on scraped_at if it doesn't exist
CREATE INDEX IF NOT EXISTS idx_jobs_scraped_at ON jobs(scraped_at DESC);

-- Add comments
COMMENT ON COLUMN jobs.contact_person IS 'Contact person name and title';
COMMENT ON COLUMN jobs.contact_email IS 'Contact email address';
COMMENT ON COLUMN jobs.contact_phone IS 'Contact phone number';
COMMENT ON COLUMN jobs.deadline IS 'Application deadline (Norwegian format: DD.MM.YYYY)';
COMMENT ON COLUMN jobs.posted_date IS 'Job posting date';
COMMENT ON COLUMN jobs.scraped_at IS 'When job details were last scraped';
