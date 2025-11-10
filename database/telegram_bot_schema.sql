-- Telegram Conversations Table
-- Stores conversation state for Telegram bot interactions

CREATE TABLE IF NOT EXISTS telegram_conversations (
  id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
  user_id UUID REFERENCES auth.users NOT NULL,

  -- Telegram info
  chat_id TEXT NOT NULL,
  telegram_user_id TEXT NOT NULL,

  -- Conversation state
  state TEXT NOT NULL DEFAULT 'IDLE',
  -- IDLE, WAITING_JOB_SELECTION, WAITING_APPLICATION_APPROVAL, WAITING_FEEDBACK, WAITING_EDIT

  current_job_id UUID REFERENCES jobs,
  current_application_id UUID,

  -- Context data
  context JSONB DEFAULT '{}'::jsonb,
  -- Stores: selected_jobs, feedback_type, edit_attempts, etc.

  -- Timestamps
  last_message_at TIMESTAMPTZ DEFAULT NOW(),
  created_at TIMESTAMPTZ DEFAULT NOW(),
  updated_at TIMESTAMPTZ DEFAULT NOW(),

  UNIQUE(user_id, chat_id)
);

-- Index for fast lookups
CREATE INDEX IF NOT EXISTS idx_telegram_conversations_chat_id ON telegram_conversations(chat_id);
CREATE INDEX IF NOT EXISTS idx_telegram_conversations_user_id ON telegram_conversations(user_id);
CREATE INDEX IF NOT EXISTS idx_telegram_conversations_state ON telegram_conversations(state);

-- RLS Policies
ALTER TABLE telegram_conversations ENABLE ROW LEVEL SECURITY;

CREATE POLICY "Users can manage own conversations"
  ON telegram_conversations
  FOR ALL
  USING (auth.uid() = user_id);

-- Application Versions Table
-- Stores different versions of cover letters during editing process

CREATE TABLE IF NOT EXISTS application_versions (
  id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
  application_id UUID REFERENCES applications NOT NULL,
  job_id UUID REFERENCES jobs NOT NULL,
  user_id UUID REFERENCES auth.users NOT NULL,

  version_number INTEGER NOT NULL DEFAULT 1,

  -- Cover letter content
  cover_letter_uk TEXT, -- Ukrainian version
  cover_letter_no TEXT, -- Norwegian version

  -- Generation details
  generation_type TEXT NOT NULL,
  -- INITIAL, LLM_REVISED, USER_EDITED, GRAMMAR_CORRECTED

  feedback_reason TEXT,
  -- "wrong_data", "inaccuracies", "user_comment"

  user_feedback TEXT,
  -- User's comment for revision

  -- AI metadata
  ai_model TEXT DEFAULT 'gpt-4.1-mini',
  prompt_used TEXT,
  tokens_used INTEGER,

  -- Status
  is_approved BOOLEAN DEFAULT false,
  is_current BOOLEAN DEFAULT true,

  created_at TIMESTAMPTZ DEFAULT NOW(),

  UNIQUE(application_id, version_number)
);

CREATE INDEX IF NOT EXISTS idx_application_versions_application_id ON application_versions(application_id);
CREATE INDEX IF NOT EXISTS idx_application_versions_is_current ON application_versions(is_current);

-- RLS Policies
ALTER TABLE application_versions ENABLE ROW LEVEL SECURITY;

CREATE POLICY "Users can view own application versions"
  ON application_versions
  FOR SELECT
  USING (auth.uid() = user_id);

CREATE POLICY "Users can insert own application versions"
  ON application_versions
  FOR INSERT
  WITH CHECK (auth.uid() = user_id);

-- Telegram Reports Table
-- Stores daily/weekly/monthly reports sent to users

CREATE TABLE IF NOT EXISTS telegram_reports (
  id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
  user_id UUID REFERENCES auth.users NOT NULL,
  chat_id TEXT NOT NULL,

  report_type TEXT NOT NULL, -- DAILY, WEEKLY, MONTHLY
  report_date DATE NOT NULL,

  -- Statistics
  jobs_found INTEGER DEFAULT 0,
  jobs_relevant INTEGER DEFAULT 0,
  applications_generated INTEGER DEFAULT 0,
  applications_sent INTEGER DEFAULT 0,
  applications_approved INTEGER DEFAULT 0,
  applications_rejected INTEGER DEFAULT 0,

  -- Report content
  summary_text TEXT,

  -- Status
  sent_at TIMESTAMPTZ,
  telegram_message_id TEXT,

  created_at TIMESTAMPTZ DEFAULT NOW(),

  UNIQUE(user_id, report_type, report_date)
);

CREATE INDEX IF NOT EXISTS idx_telegram_reports_user_id ON telegram_reports(user_id);
CREATE INDEX IF NOT EXISTS idx_telegram_reports_report_date ON telegram_reports(report_date DESC);

-- RLS Policies
ALTER TABLE telegram_reports ENABLE ROW LEVEL SECURITY;

CREATE POLICY "Users can view own reports"
  ON telegram_reports
  FOR SELECT
  USING (auth.uid() = user_id);

-- Update trigger for conversations
CREATE OR REPLACE FUNCTION update_telegram_conversations_timestamp()
RETURNS TRIGGER AS $$
BEGIN
  NEW.updated_at = NOW();
  RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER telegram_conversations_updated_at_trigger
  BEFORE UPDATE ON telegram_conversations
  FOR EACH ROW
  EXECUTE FUNCTION update_telegram_conversations_timestamp();

-- Comments
COMMENT ON TABLE telegram_conversations IS 'Stores conversation state for Telegram bot interactions';
COMMENT ON TABLE application_versions IS 'Stores different versions of cover letters during editing process';
COMMENT ON TABLE telegram_reports IS 'Stores daily/weekly/monthly reports sent to users via Telegram';
