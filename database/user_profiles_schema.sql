-- User Profiles Table
-- Stores parsed resume data and user professional information

CREATE TABLE IF NOT EXISTS user_profiles (
  id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
  user_id UUID REFERENCES auth.users NOT NULL,

  -- Personal Information
  full_name TEXT,
  email TEXT,
  phone TEXT,
  location TEXT,

  -- Professional Summary
  professional_summary TEXT,
  career_objective TEXT,
  total_experience_years INTEGER DEFAULT 0,

  -- Work Experience (JSON array)
  -- Example: [{"company": "ABC Inc", "position": "Developer", "duration": "2020-2023", "responsibilities": ["..."]}]
  work_experience JSONB DEFAULT '[]'::jsonb,

  -- Education (JSON array)
  -- Example: [{"degree": "Bachelor", "institution": "University", "year": "2020"}]
  education JSONB DEFAULT '[]'::jsonb,

  -- Skills
  technical_skills TEXT[] DEFAULT ARRAY[]::TEXT[],
  languages TEXT[] DEFAULT ARRAY[]::TEXT[],
  soft_skills TEXT[] DEFAULT ARRAY[]::TEXT[],
  certifications TEXT[] DEFAULT ARRAY[]::TEXT[],

  -- Metadata
  resume_file_url TEXT,
  parsed_at TIMESTAMPTZ DEFAULT NOW(),
  updated_at TIMESTAMPTZ DEFAULT NOW(),

  -- Ensure one profile per user
  UNIQUE(user_id)
);

-- RLS Policies
ALTER TABLE user_profiles ENABLE ROW LEVEL SECURITY;

-- Users can read their own profile
CREATE POLICY "Users can read own profile"
  ON user_profiles
  FOR SELECT
  USING (auth.uid() = user_id);

-- Users can insert their own profile
CREATE POLICY "Users can insert own profile"
  ON user_profiles
  FOR INSERT
  WITH CHECK (auth.uid() = user_id);

-- Users can update their own profile
CREATE POLICY "Users can update own profile"
  ON user_profiles
  FOR UPDATE
  USING (auth.uid() = user_id);

-- Users can delete their own profile
CREATE POLICY "Users can delete own profile"
  ON user_profiles
  FOR DELETE
  USING (auth.uid() = user_id);

-- Indexes for performance
CREATE INDEX IF NOT EXISTS idx_user_profiles_user_id ON user_profiles(user_id);
CREATE INDEX IF NOT EXISTS idx_user_profiles_email ON user_profiles(email);

-- Trigger to update updated_at timestamp
CREATE OR REPLACE FUNCTION update_user_profiles_updated_at()
RETURNS TRIGGER AS $$
BEGIN
  NEW.updated_at = NOW();
  RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER user_profiles_updated_at_trigger
  BEFORE UPDATE ON user_profiles
  FOR EACH ROW
  EXECUTE FUNCTION update_user_profiles_updated_at();

-- Comments
COMMENT ON TABLE user_profiles IS 'Stores user professional profiles parsed from resumes';
COMMENT ON COLUMN user_profiles.work_experience IS 'Array of work experience entries in JSON format';
COMMENT ON COLUMN user_profiles.education IS 'Array of education entries in JSON format';
COMMENT ON COLUMN user_profiles.technical_skills IS 'Array of technical skills (e.g., Python, JavaScript)';
COMMENT ON COLUMN user_profiles.languages IS 'Array of languages spoken (e.g., Norwegian, English)';
