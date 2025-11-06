-- JobBot Norway - Initial Database Schema
-- Migration: 001
-- Created: 2025-11-06

-- Enable UUID extension
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

-- =====================================================
-- 1. USER PROFILES (extends Supabase Auth)
-- =====================================================

CREATE TABLE public.profiles (
  id UUID REFERENCES auth.users(id) PRIMARY KEY,
  username TEXT UNIQUE NOT NULL,
  full_name TEXT,
  email TEXT,
  phone TEXT,
  fnr TEXT, -- Norwegian ID (encrypted)
  avatar_url TEXT,
  created_at TIMESTAMPTZ DEFAULT NOW(),
  updated_at TIMESTAMPTZ DEFAULT NOW()
);

-- Enable RLS
ALTER TABLE public.profiles ENABLE ROW LEVEL SECURITY;

-- Policies
CREATE POLICY "Users can view own profile"
  ON public.profiles FOR SELECT
  USING (auth.uid() = id);

CREATE POLICY "Users can update own profile"
  ON public.profiles FOR UPDATE
  USING (auth.uid() = id);

-- =====================================================
-- 2. USER SETTINGS
-- =====================================================

CREATE TABLE public.user_settings (
  id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
  user_id UUID REFERENCES public.profiles(id) ON DELETE CASCADE UNIQUE,

  -- Search settings
  nav_search_urls TEXT[] DEFAULT '{}',
  finn_search_urls TEXT[] DEFAULT '{}',
  keywords TEXT[] DEFAULT '{}',
  exclude_keywords TEXT[] DEFAULT '{}',
  preferred_locations TEXT[] DEFAULT '{}',

  -- Resume & Profile
  resume_storage_path TEXT,
  unified_profile JSONB,
  skills TEXT[] DEFAULT '{}',
  experience_years INT DEFAULT 0,

  -- Application settings
  min_relevance_score INT DEFAULT 70,
  auto_apply_threshold INT DEFAULT 85,
  max_applications_per_day INT DEFAULT 5,
  require_manual_approval BOOLEAN DEFAULT true,

  -- NAV credentials (will be encrypted in application layer)
  nav_fnr TEXT,
  nav_password_encrypted TEXT,

  -- Telegram notifications
  telegram_chat_id TEXT,
  telegram_enabled BOOLEAN DEFAULT false,

  -- Monitoring
  auto_scan_enabled BOOLEAN DEFAULT false,
  scan_interval_hours INT DEFAULT 6,
  last_scan_at TIMESTAMPTZ,

  created_at TIMESTAMPTZ DEFAULT NOW(),
  updated_at TIMESTAMPTZ DEFAULT NOW()
);

-- Enable RLS
ALTER TABLE public.user_settings ENABLE ROW LEVEL SECURITY;

-- Policies
CREATE POLICY "Users can view own settings"
  ON public.user_settings FOR SELECT
  USING (auth.uid() = user_id);

CREATE POLICY "Users can update own settings"
  ON public.user_settings FOR UPDATE
  USING (auth.uid() = user_id);

CREATE POLICY "Users can insert own settings"
  ON public.user_settings FOR INSERT
  WITH CHECK (auth.uid() = user_id);

-- =====================================================
-- 3. JOBS
-- =====================================================

CREATE TABLE public.jobs (
  id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
  user_id UUID REFERENCES public.profiles(id) ON DELETE CASCADE,

  -- Job details
  url TEXT NOT NULL,
  title TEXT NOT NULL,
  company TEXT,
  description TEXT,
  location TEXT,
  source TEXT, -- 'arbeidsplassen.nav.no', 'finn.no'
  posted_date DATE,

  -- AI Analysis
  relevance_score INT DEFAULT 0,
  ai_analysis JSONB, -- Full AI response with reasoning
  match_reasons TEXT[] DEFAULT '{}',
  concerns TEXT[] DEFAULT '{}',
  recommendation TEXT, -- 'APPLY', 'SKIP', 'REVIEW'

  -- Status tracking
  status TEXT DEFAULT 'NEW', -- NEW, ANALYZED, APPROVED, APPLIED, REJECTED, REPORTED

  -- Form data
  application_form_html TEXT,
  skyvern_task_id TEXT,

  -- Metadata
  created_at TIMESTAMPTZ DEFAULT NOW(),
  updated_at TIMESTAMPTZ DEFAULT NOW(),
  analyzed_at TIMESTAMPTZ,
  applied_at TIMESTAMPTZ,

  -- Unique constraint per user
  UNIQUE(user_id, url)
);

-- Indexes
CREATE INDEX idx_jobs_user_status ON public.jobs(user_id, status);
CREATE INDEX idx_jobs_relevance ON public.jobs(user_id, relevance_score DESC);
CREATE INDEX idx_jobs_created ON public.jobs(user_id, created_at DESC);

-- Enable RLS
ALTER TABLE public.jobs ENABLE ROW LEVEL SECURITY;

-- Policies
CREATE POLICY "Users can view own jobs"
  ON public.jobs FOR SELECT
  USING (auth.uid() = user_id);

CREATE POLICY "Users can insert own jobs"
  ON public.jobs FOR INSERT
  WITH CHECK (auth.uid() = user_id);

CREATE POLICY "Users can update own jobs"
  ON public.jobs FOR UPDATE
  USING (auth.uid() = user_id);

CREATE POLICY "Users can delete own jobs"
  ON public.jobs FOR DELETE
  USING (auth.uid() = user_id);

-- =====================================================
-- 4. COVER LETTERS
-- =====================================================

CREATE TABLE public.cover_letters (
  id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
  user_id UUID REFERENCES public.profiles(id) ON DELETE CASCADE,
  job_id UUID REFERENCES public.jobs(id) ON DELETE CASCADE,

  -- Content
  content TEXT NOT NULL,
  language TEXT DEFAULT 'norwegian',
  word_count INT,

  -- Storage paths (Supabase Storage)
  pdf_path TEXT,
  txt_path TEXT,

  -- Generation metadata
  ai_model TEXT DEFAULT 'gpt-4',
  generation_prompt TEXT,
  custom_edited BOOLEAN DEFAULT false,

  created_at TIMESTAMPTZ DEFAULT NOW(),
  updated_at TIMESTAMPTZ DEFAULT NOW()
);

-- Indexes
CREATE INDEX idx_cover_letters_job ON public.cover_letters(job_id);

-- Enable RLS
ALTER TABLE public.cover_letters ENABLE ROW LEVEL SECURITY;

-- Policies
CREATE POLICY "Users can view own cover letters"
  ON public.cover_letters FOR SELECT
  USING (auth.uid() = user_id);

CREATE POLICY "Users can insert own cover letters"
  ON public.cover_letters FOR INSERT
  WITH CHECK (auth.uid() = user_id);

CREATE POLICY "Users can update own cover letters"
  ON public.cover_letters FOR UPDATE
  USING (auth.uid() = user_id);

CREATE POLICY "Users can delete own cover letters"
  ON public.cover_letters FOR DELETE
  USING (auth.uid() = user_id);

-- =====================================================
-- 5. APPLICATIONS
-- =====================================================

CREATE TABLE public.applications (
  id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
  user_id UUID REFERENCES public.profiles(id) ON DELETE CASCADE,
  job_id UUID REFERENCES public.jobs(id) ON DELETE CASCADE,
  cover_letter_id UUID REFERENCES public.cover_letters(id),

  -- Application details
  application_url TEXT,
  status TEXT DEFAULT 'PENDING', -- PENDING, SUCCESS, FAILED, REPORTED

  -- Form filling results (Skyvern)
  skyvern_result JSONB,
  screenshot_path TEXT, -- Supabase Storage path

  -- NAV reporting
  nav_reported BOOLEAN DEFAULT false,
  nav_report_date TIMESTAMPTZ,
  nav_response JSONB,

  -- Error tracking
  error_message TEXT,
  retry_count INT DEFAULT 0,
  last_retry_at TIMESTAMPTZ,

  -- Timestamps
  submitted_at TIMESTAMPTZ,
  created_at TIMESTAMPTZ DEFAULT NOW(),
  updated_at TIMESTAMPTZ DEFAULT NOW()
);

-- Indexes
CREATE INDEX idx_applications_user ON public.applications(user_id, created_at DESC);
CREATE INDEX idx_applications_job ON public.applications(job_id);
CREATE INDEX idx_applications_status ON public.applications(user_id, status);

-- Enable RLS
ALTER TABLE public.applications ENABLE ROW LEVEL SECURITY;

-- Policies
CREATE POLICY "Users can view own applications"
  ON public.applications FOR SELECT
  USING (auth.uid() = user_id);

CREATE POLICY "Users can insert own applications"
  ON public.applications FOR INSERT
  WITH CHECK (auth.uid() = user_id);

CREATE POLICY "Users can update own applications"
  ON public.applications FOR UPDATE
  USING (auth.uid() = user_id);

-- =====================================================
-- 6. MONITORING LOGS
-- =====================================================

CREATE TABLE public.monitoring_logs (
  id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
  user_id UUID REFERENCES public.profiles(id) ON DELETE CASCADE,

  -- Scan info
  scan_type TEXT, -- 'MANUAL', 'SCHEDULED', 'WEBHOOK'
  jobs_found INT DEFAULT 0,
  jobs_analyzed INT DEFAULT 0,
  jobs_relevant INT DEFAULT 0,
  applications_sent INT DEFAULT 0,
  nav_reports_sent INT DEFAULT 0,

  -- Status
  status TEXT DEFAULT 'RUNNING', -- RUNNING, COMPLETED, FAILED
  error_message TEXT,
  details JSONB,

  -- Performance
  duration_seconds INT,

  -- Timestamps
  started_at TIMESTAMPTZ DEFAULT NOW(),
  completed_at TIMESTAMPTZ
);

-- Indexes
CREATE INDEX idx_monitoring_user ON public.monitoring_logs(user_id, started_at DESC);

-- Enable RLS
ALTER TABLE public.monitoring_logs ENABLE ROW LEVEL SECURITY;

-- Policies
CREATE POLICY "Users can view own logs"
  ON public.monitoring_logs FOR SELECT
  USING (auth.uid() = user_id);

CREATE POLICY "Users can insert own logs"
  ON public.monitoring_logs FOR INSERT
  WITH CHECK (auth.uid() = user_id);

-- =====================================================
-- 7. FUNCTIONS & TRIGGERS
-- =====================================================

-- Auto-update updated_at timestamp
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
  NEW.updated_at = NOW();
  RETURN NEW;
END;
$$ LANGUAGE plpgsql;

-- Apply to all tables with updated_at
CREATE TRIGGER update_profiles_updated_at BEFORE UPDATE ON public.profiles
  FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_user_settings_updated_at BEFORE UPDATE ON public.user_settings
  FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_jobs_updated_at BEFORE UPDATE ON public.jobs
  FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_cover_letters_updated_at BEFORE UPDATE ON public.cover_letters
  FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_applications_updated_at BEFORE UPDATE ON public.applications
  FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

-- Auto-create user_settings when profile is created
CREATE OR REPLACE FUNCTION create_user_settings()
RETURNS TRIGGER AS $$
BEGIN
  INSERT INTO public.user_settings (user_id)
  VALUES (NEW.id);
  RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER on_profile_created AFTER INSERT ON public.profiles
  FOR EACH ROW EXECUTE FUNCTION create_user_settings();

-- =====================================================
-- 8. VIEWS FOR ANALYTICS
-- =====================================================

-- Dashboard overview per user
CREATE OR REPLACE VIEW user_dashboard_stats AS
SELECT
  u.id AS user_id,
  u.username,
  COUNT(DISTINCT j.id) AS total_jobs,
  COUNT(DISTINCT CASE WHEN j.status = 'NEW' THEN j.id END) AS new_jobs,
  COUNT(DISTINCT CASE WHEN j.status = 'ANALYZED' THEN j.id END) AS analyzed_jobs,
  COUNT(DISTINCT CASE WHEN j.relevance_score >= s.min_relevance_score THEN j.id END) AS relevant_jobs,
  COUNT(DISTINCT a.id) AS total_applications,
  COUNT(DISTINCT CASE WHEN a.status = 'SUCCESS' THEN a.id END) AS successful_applications,
  COUNT(DISTINCT CASE WHEN a.nav_reported = true THEN a.id END) AS nav_reports,
  MAX(s.last_scan_at) AS last_scan_at
FROM public.profiles u
LEFT JOIN public.user_settings s ON u.id = s.user_id
LEFT JOIN public.jobs j ON u.id = j.user_id
LEFT JOIN public.applications a ON u.id = a.user_id
GROUP BY u.id, u.username;

-- Recent activity per user (last 30 days)
CREATE OR REPLACE VIEW user_recent_activity AS
SELECT
  user_id,
  DATE(created_at) AS activity_date,
  COUNT(*) FILTER (WHERE status IN ('NEW', 'ANALYZED')) AS jobs_found,
  COUNT(*) FILTER (WHERE status = 'APPLIED') AS applications_sent
FROM public.jobs
WHERE created_at >= NOW() - INTERVAL '30 days'
GROUP BY user_id, DATE(created_at)
ORDER BY user_id, activity_date DESC;

-- =====================================================
-- INITIAL DATA
-- =====================================================

-- Create a function to handle new user signup
CREATE OR REPLACE FUNCTION handle_new_user()
RETURNS TRIGGER AS $$
BEGIN
  INSERT INTO public.profiles (id, username, email, full_name)
  VALUES (
    NEW.id,
    COALESCE(NEW.raw_user_meta_data->>'username', split_part(NEW.email, '@', 1)),
    NEW.email,
    COALESCE(NEW.raw_user_meta_data->>'full_name', '')
  );
  RETURN NEW;
END;
$$ LANGUAGE plpgsql SECURITY DEFINER;

-- Trigger on auth.users
CREATE TRIGGER on_auth_user_created
  AFTER INSERT ON auth.users
  FOR EACH ROW EXECUTE FUNCTION handle_new_user();

-- =====================================================
-- STORAGE BUCKETS (Run these in Supabase Dashboard → Storage)
-- =====================================================

-- Note: These should be created via Supabase Dashboard or CLI
-- Buckets needed:
-- 1. 'resumes' - Private, file size limit 10MB
-- 2. 'cover-letters' - Private, file size limit 5MB
-- 3. 'screenshots' - Private, file size limit 5MB

-- Storage policies will be created after buckets:

/*
-- Resumes bucket policies
CREATE POLICY "Users can upload own resume"
ON storage.objects FOR INSERT
TO authenticated
WITH CHECK (bucket_id = 'resumes' AND auth.uid()::text = (storage.foldername(name))[1]);

CREATE POLICY "Users can view own resume"
ON storage.objects FOR SELECT
TO authenticated
USING (bucket_id = 'resumes' AND auth.uid()::text = (storage.foldername(name))[1]);

-- Similar policies for cover-letters and screenshots buckets
*/

-- =====================================================
-- COMMENTS
-- =====================================================

COMMENT ON TABLE public.profiles IS 'Extended user profiles linked to Supabase Auth';
COMMENT ON TABLE public.user_settings IS 'User-specific configuration and preferences';
COMMENT ON TABLE public.jobs IS 'Scraped job listings with AI analysis';
COMMENT ON TABLE public.cover_letters IS 'AI-generated cover letters for job applications';
COMMENT ON TABLE public.applications IS 'Submitted job applications with status tracking';
COMMENT ON TABLE public.monitoring_logs IS 'System monitoring and scan history';

-- =====================================================
-- SUCCESS MESSAGE
-- =====================================================

DO $$
BEGIN
  RAISE NOTICE '✅ JobBot Norway database schema created successfully!';
  RAISE NOTICE '📊 Tables: profiles, user_settings, jobs, cover_letters, applications, monitoring_logs';
  RAISE NOTICE '🔒 RLS policies enabled on all tables';
  RAISE NOTICE '⚡ Triggers created for auto-updates';
  RAISE NOTICE '📈 Analytics views created';
  RAISE NOTICE '';
  RAISE NOTICE '🔧 Next steps:';
  RAISE NOTICE '1. Create Storage buckets: resumes, cover-letters, screenshots';
  RAISE NOTICE '2. Setup Storage policies';
  RAISE NOTICE '3. Configure Supabase Auth providers';
  RAISE NOTICE '4. Get Supabase URL and Keys for .env';
END $$;
