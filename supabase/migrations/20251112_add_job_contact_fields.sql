-- Add contact and deadline fields to jobs table
ALTER TABLE jobs
ADD COLUMN IF NOT EXISTS contact_person TEXT,
ADD COLUMN IF NOT EXISTS contact_email TEXT,
ADD COLUMN IF NOT EXISTS contact_phone TEXT,
ADD COLUMN IF NOT EXISTS deadline TEXT,
ADD COLUMN IF NOT EXISTS posted_date TEXT;

-- Add comment
COMMENT ON COLUMN jobs.contact_person IS 'Contact person name and title';
COMMENT ON COLUMN jobs.contact_email IS 'Contact email address';
COMMENT ON COLUMN jobs.contact_phone IS 'Contact phone number';
COMMENT ON COLUMN jobs.deadline IS 'Application deadline (Norwegian format: DD.MM.YYYY)';
COMMENT ON COLUMN jobs.posted_date IS 'Job posting date';
