-- Add resume_files array column to user_settings table
-- Allows storing multiple resume file paths (up to 5)

ALTER TABLE user_settings
ADD COLUMN IF NOT EXISTS resume_files TEXT[] DEFAULT ARRAY[]::TEXT[];

-- Add comment to document the column
COMMENT ON COLUMN user_settings.resume_files IS 'Array of uploaded resume file paths (max 5). Files are stored in Supabase storage resumes bucket.';

-- Add index for faster queries
CREATE INDEX IF NOT EXISTS idx_user_settings_resume_files ON user_settings USING GIN (resume_files);
