-- Create saved_profiles table for storing multiple user profile versions
-- Used for job relevance analysis and application automation

CREATE TABLE IF NOT EXISTS saved_profiles (
  id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
  user_id UUID REFERENCES auth.users(id) ON DELETE CASCADE NOT NULL,

  -- Profile metadata
  profile_name TEXT NOT NULL,
  description TEXT,
  is_active BOOLEAN DEFAULT false,

  -- Profile data (complete snapshot from user_profiles)
  profile_data JSONB NOT NULL,

  -- Source information
  source_resumes TEXT[] DEFAULT ARRAY[]::TEXT[],
  total_resumes_analyzed INTEGER DEFAULT 0,

  -- Timestamps
  created_at TIMESTAMPTZ DEFAULT NOW(),
  updated_at TIMESTAMPTZ DEFAULT NOW(),

  -- Constraints
  UNIQUE(user_id, profile_name)
);

-- Create index for faster queries
CREATE INDEX IF NOT EXISTS idx_saved_profiles_user_id ON saved_profiles(user_id);
CREATE INDEX IF NOT EXISTS idx_saved_profiles_is_active ON saved_profiles(user_id, is_active);
CREATE INDEX IF NOT EXISTS idx_saved_profiles_created_at ON saved_profiles(created_at DESC);

-- Enable Row Level Security
ALTER TABLE saved_profiles ENABLE ROW LEVEL SECURITY;

-- RLS Policies: Users can only access their own profiles
CREATE POLICY "Users can read own profiles"
ON saved_profiles FOR SELECT
USING (auth.uid() = user_id);

CREATE POLICY "Users can insert own profiles"
ON saved_profiles FOR INSERT
WITH CHECK (auth.uid() = user_id);

CREATE POLICY "Users can update own profiles"
ON saved_profiles FOR UPDATE
USING (auth.uid() = user_id)
WITH CHECK (auth.uid() = user_id);

CREATE POLICY "Users can delete own profiles"
ON saved_profiles FOR DELETE
USING (auth.uid() = user_id);

-- Add comments for documentation
COMMENT ON TABLE saved_profiles IS 'Stores multiple versions of user profiles for job matching and application automation';
COMMENT ON COLUMN saved_profiles.profile_name IS 'User-defined name or auto-generated with timestamp';
COMMENT ON COLUMN saved_profiles.is_active IS 'Only one profile can be active per user - used for job relevance scoring';
COMMENT ON COLUMN saved_profiles.profile_data IS 'Complete profile snapshot from user_profiles table in JSONB format';
COMMENT ON COLUMN saved_profiles.source_resumes IS 'Array of resume file paths used to generate this profile';

-- Function to auto-update updated_at timestamp
CREATE OR REPLACE FUNCTION update_saved_profiles_updated_at()
RETURNS TRIGGER AS $$
BEGIN
  NEW.updated_at = NOW();
  RETURN NEW;
END;
$$ LANGUAGE plpgsql;

-- Trigger to automatically update updated_at
CREATE TRIGGER set_saved_profiles_updated_at
  BEFORE UPDATE ON saved_profiles
  FOR EACH ROW
  EXECUTE FUNCTION update_saved_profiles_updated_at();

-- Function to ensure only one active profile per user
CREATE OR REPLACE FUNCTION ensure_single_active_profile()
RETURNS TRIGGER AS $$
BEGIN
  IF NEW.is_active = true THEN
    -- Deactivate all other profiles for this user
    UPDATE saved_profiles
    SET is_active = false
    WHERE user_id = NEW.user_id
      AND id != NEW.id
      AND is_active = true;
  END IF;
  RETURN NEW;
END;
$$ LANGUAGE plpgsql;

-- Trigger to ensure only one active profile
CREATE TRIGGER ensure_single_active_profile_trigger
  BEFORE INSERT OR UPDATE ON saved_profiles
  FOR EACH ROW
  EXECUTE FUNCTION ensure_single_active_profile();

-- Verify table creation
SELECT
  table_name,
  (SELECT COUNT(*) FROM information_schema.columns WHERE table_name = 'saved_profiles') as column_count
FROM information_schema.tables
WHERE table_name = 'saved_profiles';
