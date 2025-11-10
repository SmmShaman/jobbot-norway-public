-- Fix RLS policies for user_settings to allow resume_files updates
-- This ensures users can update their own settings including resume_files array

-- Drop existing policies if they're too restrictive
DROP POLICY IF EXISTS "Users can update own settings" ON user_settings;
DROP POLICY IF EXISTS "Users can insert own settings" ON user_settings;
DROP POLICY IF EXISTS "Users can read own settings" ON user_settings;

-- Recreate policies with proper permissions
CREATE POLICY "Users can read own settings"
ON user_settings FOR SELECT
USING (auth.uid() = user_id);

CREATE POLICY "Users can insert own settings"
ON user_settings FOR INSERT
WITH CHECK (auth.uid() = user_id);

CREATE POLICY "Users can update own settings"
ON user_settings FOR UPDATE
USING (auth.uid() = user_id)
WITH CHECK (auth.uid() = user_id);

-- Verify the column exists
SELECT column_name, data_type, is_nullable
FROM information_schema.columns
WHERE table_name = 'user_settings'
AND column_name IN ('resume_files', 'resume_storage_path');

-- Check if there are any rows for the current user
SELECT id, user_id, resume_storage_path, resume_files
FROM user_settings
WHERE user_id = auth.uid();
