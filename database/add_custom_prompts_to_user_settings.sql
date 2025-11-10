-- Add custom AI prompt columns to user_settings table
-- This allows users to customize the AI prompts used for resume parsing

ALTER TABLE user_settings
ADD COLUMN IF NOT EXISTS custom_system_prompt TEXT,
ADD COLUMN IF NOT EXISTS custom_user_prompt TEXT;

-- Add comments to document the columns
COMMENT ON COLUMN user_settings.custom_system_prompt IS 'Custom system prompt for Azure OpenAI GPT-4 resume parsing (AI role and instructions)';
COMMENT ON COLUMN user_settings.custom_user_prompt IS 'Custom user prompt for Azure OpenAI GPT-4 resume parsing (task instructions)';

-- These fields are optional - if NULL, the Edge Function will use default prompts
