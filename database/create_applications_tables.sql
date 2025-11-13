-- Create applications table for storing job applications (søknad)
CREATE TABLE IF NOT EXISTS applications (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  job_id UUID NOT NULL REFERENCES jobs(id) ON DELETE CASCADE,
  user_id UUID NOT NULL REFERENCES auth.users(id) ON DELETE CASCADE,
  cover_letter_no TEXT NOT NULL,  -- Norwegian søknad
  cover_letter_uk TEXT NOT NULL,  -- Ukrainian translation
  status TEXT NOT NULL DEFAULT 'draft' CHECK (status IN ('draft', 'approved', 'rejected', 'submitted')),
  created_at TIMESTAMPTZ DEFAULT NOW(),
  updated_at TIMESTAMPTZ DEFAULT NOW(),
  approved_at TIMESTAMPTZ,
  submitted_at TIMESTAMPTZ,
  UNIQUE(job_id, user_id)  -- One application per job per user
);

-- Create telegram_conversations table for tracking bot conversation state
CREATE TABLE IF NOT EXISTS telegram_conversations (
  chat_id TEXT PRIMARY KEY,
  telegram_user_id TEXT NOT NULL,
  state TEXT NOT NULL DEFAULT 'IDLE' CHECK (state IN ('IDLE', 'WAITING_EDIT', 'WAITING_FEEDBACK')),
  current_application_id UUID REFERENCES applications(id) ON DELETE SET NULL,
  context JSONB,  -- Additional context data
  created_at TIMESTAMPTZ DEFAULT NOW(),
  updated_at TIMESTAMPTZ DEFAULT NOW()
);

-- Add indexes for better query performance
CREATE INDEX IF NOT EXISTS idx_applications_user_id ON applications(user_id);
CREATE INDEX IF NOT EXISTS idx_applications_job_id ON applications(job_id);
CREATE INDEX IF NOT EXISTS idx_applications_status ON applications(status);
CREATE INDEX IF NOT EXISTS idx_telegram_conversations_state ON telegram_conversations(state);

-- Add application_prompt field to user_settings for custom prompts
ALTER TABLE user_settings
ADD COLUMN IF NOT EXISTS application_prompt TEXT;

-- Add comments for documentation
COMMENT ON TABLE applications IS 'Stores job applications (søknad) generated for vacancies';
COMMENT ON COLUMN applications.cover_letter_no IS 'Application letter in Norwegian (Bokmål)';
COMMENT ON COLUMN applications.cover_letter_uk IS 'Application letter translated to Ukrainian';
COMMENT ON COLUMN applications.status IS 'Status: draft, approved, rejected, submitted';

COMMENT ON TABLE telegram_conversations IS 'Tracks Telegram bot conversation states for interactive editing';
COMMENT ON COLUMN telegram_conversations.state IS 'Current conversation state: IDLE, WAITING_EDIT, WAITING_FEEDBACK';
COMMENT ON COLUMN telegram_conversations.current_application_id IS 'Application being edited in current conversation';

COMMENT ON COLUMN user_settings.application_prompt IS 'Custom AI prompt for generating job applications';

-- Create function to auto-update updated_at timestamp
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
  NEW.updated_at = NOW();
  RETURN NEW;
END;
$$ LANGUAGE plpgsql;

-- Add trigger to applications table
DROP TRIGGER IF EXISTS update_applications_updated_at ON applications;
CREATE TRIGGER update_applications_updated_at
  BEFORE UPDATE ON applications
  FOR EACH ROW
  EXECUTE FUNCTION update_updated_at_column();

-- Add trigger to telegram_conversations table
DROP TRIGGER IF EXISTS update_telegram_conversations_updated_at ON telegram_conversations;
CREATE TRIGGER update_telegram_conversations_updated_at
  BEFORE UPDATE ON telegram_conversations
  FOR EACH ROW
  EXECUTE FUNCTION update_updated_at_column();

-- Grant permissions (adjust based on your RLS policies)
ALTER TABLE applications ENABLE ROW LEVEL SECURITY;
ALTER TABLE telegram_conversations ENABLE ROW LEVEL SECURITY;

-- RLS policy for applications - users can only see their own applications
CREATE POLICY "Users can view own applications"
  ON applications FOR SELECT
  USING (auth.uid() = user_id);

CREATE POLICY "Users can create own applications"
  ON applications FOR INSERT
  WITH CHECK (auth.uid() = user_id);

CREATE POLICY "Users can update own applications"
  ON applications FOR UPDATE
  USING (auth.uid() = user_id);

CREATE POLICY "Users can delete own applications"
  ON applications FOR DELETE
  USING (auth.uid() = user_id);

-- Service role can do everything
CREATE POLICY "Service role has full access to applications"
  ON applications
  USING (auth.role() = 'service_role');

CREATE POLICY "Service role has full access to telegram_conversations"
  ON telegram_conversations
  USING (auth.role() = 'service_role');
