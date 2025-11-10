-- ============================================================
-- User Settings Table Schema
-- Stores user configuration for job search URLs
-- ============================================================

CREATE TABLE IF NOT EXISTS user_settings (
    -- Primary key
    user_id UUID PRIMARY KEY REFERENCES auth.users(id) ON DELETE CASCADE,

    -- Search URLs
    finn_search_urls TEXT[] DEFAULT '{}', -- Array of FINN.no search URLs
    nav_search_urls TEXT[] DEFAULT '{}',  -- Array of NAV.no search URLs

    -- Timestamps
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

-- ============================================================
-- Indexes
-- ============================================================

CREATE INDEX IF NOT EXISTS idx_user_settings_user_id ON user_settings(user_id);

-- ============================================================
-- Row Level Security (RLS)
-- ============================================================

ALTER TABLE user_settings ENABLE ROW LEVEL SECURITY;

DROP POLICY IF EXISTS "Users can view own settings" ON user_settings;
DROP POLICY IF EXISTS "Users can insert own settings" ON user_settings;
DROP POLICY IF EXISTS "Users can update own settings" ON user_settings;
DROP POLICY IF EXISTS "Users can delete own settings" ON user_settings;

CREATE POLICY "Users can view own settings"
    ON user_settings FOR SELECT
    USING (auth.uid() = user_id);

CREATE POLICY "Users can insert own settings"
    ON user_settings FOR INSERT
    WITH CHECK (auth.uid() = user_id);

CREATE POLICY "Users can update own settings"
    ON user_settings FOR UPDATE
    USING (auth.uid() = user_id)
    WITH CHECK (auth.uid() = user_id);

CREATE POLICY "Users can delete own settings"
    ON user_settings FOR DELETE
    USING (auth.uid() = user_id);

-- ============================================================
-- Trigger for updated_at
-- ============================================================

DROP TRIGGER IF EXISTS update_user_settings_updated_at ON user_settings;
CREATE TRIGGER update_user_settings_updated_at
    BEFORE UPDATE ON user_settings
    FOR EACH ROW
    EXECUTE FUNCTION update_updated_at_column();

-- ============================================================
-- Comments
-- ============================================================

COMMENT ON TABLE user_settings IS 'User configuration for job search URLs and preferences';
COMMENT ON COLUMN user_settings.finn_search_urls IS 'Array of FINN.no search URLs to monitor';
COMMENT ON COLUMN user_settings.nav_search_urls IS 'Array of NAV.no search URLs to monitor';
