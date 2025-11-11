-- Complete migration to add all missing columns to user_settings
-- This ensures the table has all required fields for resume management

-- Add resume_storage_path (for backward compatibility)
ALTER TABLE user_settings
ADD COLUMN IF NOT EXISTS resume_storage_path TEXT;

-- Add resume_files array (new format - up to 5 resumes)
ALTER TABLE user_settings
ADD COLUMN IF NOT EXISTS resume_files TEXT[] DEFAULT ARRAY[]::TEXT[];

-- Add custom AI prompts
ALTER TABLE user_settings
ADD COLUMN IF NOT EXISTS custom_system_prompt TEXT;

ALTER TABLE user_settings
ADD COLUMN IF NOT EXISTS custom_user_prompt TEXT;

-- Create index for better performance
CREATE INDEX IF NOT EXISTS idx_user_settings_resume_files
ON user_settings USING GIN (resume_files);

-- Add comments for documentation
COMMENT ON COLUMN user_settings.resume_storage_path IS 'Legacy single resume path (backward compatibility)';
COMMENT ON COLUMN user_settings.resume_files IS 'Array of resume file paths (max 5) - new format';
COMMENT ON COLUMN user_settings.custom_system_prompt IS 'Custom system prompt for Azure OpenAI resume parsing';
COMMENT ON COLUMN user_settings.custom_user_prompt IS 'Custom user prompt for Azure OpenAI resume parsing';

-- Verify columns were created
SELECT column_name, data_type, is_nullable, column_default
FROM information_schema.columns
WHERE table_name = 'user_settings'
AND column_name IN ('resume_storage_path', 'resume_files', 'custom_system_prompt', 'custom_user_prompt')
ORDER BY column_name;

-- Check current data for logged in user
SELECT id, user_id, resume_storage_path, resume_files,
       array_length(resume_files, 1) as resume_count
FROM user_settings
WHERE user_id = auth.uid();
