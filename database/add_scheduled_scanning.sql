-- Add scheduled scanning fields to user_settings table

ALTER TABLE user_settings
ADD COLUMN IF NOT EXISTS scan_schedule_enabled BOOLEAN DEFAULT false,
ADD COLUMN IF NOT EXISTS scan_schedule_cron VARCHAR(50) DEFAULT '0 9 * * *', -- Default: Every day at 9 AM
ADD COLUMN IF NOT EXISTS scan_schedule_timezone VARCHAR(50) DEFAULT 'Europe/Oslo',
ADD COLUMN IF NOT EXISTS last_scheduled_scan_at TIMESTAMPTZ,
ADD COLUMN IF NOT EXISTS next_scheduled_scan_at TIMESTAMPTZ;

-- Create function to calculate next scan time based on cron
CREATE OR REPLACE FUNCTION calculate_next_scan_time(cron_expr VARCHAR, tz VARCHAR)
RETURNS TIMESTAMPTZ AS $$
DECLARE
  next_run TIMESTAMPTZ;
BEGIN
  -- Simple cron parser for common patterns
  -- Format: minute hour day month dayofweek
  -- Examples:
  -- '0 9 * * *' = Every day at 9:00 AM
  -- '0 9,18 * * *' = Every day at 9:00 AM and 6:00 PM
  -- '0 */6 * * *' = Every 6 hours
  -- '0 9 * * 1' = Every Monday at 9:00 AM

  -- For now, return current time + 24 hours as default
  -- TODO: Implement full cron parsing
  next_run := NOW() AT TIME ZONE tz + INTERVAL '24 hours';

  RETURN next_run;
END;
$$ LANGUAGE plpgsql;

-- Create scheduled_scans table to track scan history
CREATE TABLE IF NOT EXISTS scheduled_scans (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  user_id UUID NOT NULL REFERENCES auth.users(id) ON DELETE CASCADE,
  scheduled_at TIMESTAMPTZ NOT NULL,
  started_at TIMESTAMPTZ,
  completed_at TIMESTAMPTZ,
  status VARCHAR(20) NOT NULL DEFAULT 'pending',
  jobs_found INTEGER DEFAULT 0,
  jobs_analyzed INTEGER DEFAULT 0,
  error_message TEXT,
  created_at TIMESTAMPTZ DEFAULT NOW(),
  CONSTRAINT chk_scheduled_scan_status CHECK (status IN ('pending', 'running', 'completed', 'failed'))
);

CREATE INDEX IF NOT EXISTS idx_scheduled_scans_user_id ON scheduled_scans(user_id);
CREATE INDEX IF NOT EXISTS idx_scheduled_scans_status ON scheduled_scans(status);
CREATE INDEX IF NOT EXISTS idx_scheduled_scans_scheduled_at ON scheduled_scans(scheduled_at);

-- Enable RLS
ALTER TABLE scheduled_scans ENABLE ROW LEVEL SECURITY;

-- RLS Policies
DROP POLICY IF EXISTS "Users can view own scheduled scans" ON scheduled_scans;
CREATE POLICY "Users can view own scheduled scans" ON scheduled_scans FOR SELECT USING (auth.uid() = user_id);

DROP POLICY IF EXISTS "Service role has full access to scheduled_scans" ON scheduled_scans;
CREATE POLICY "Service role has full access to scheduled_scans" ON scheduled_scans USING (auth.role() = 'service_role');

-- Comment
COMMENT ON TABLE scheduled_scans IS 'Tracks history of automated scheduled scans';
COMMENT ON COLUMN user_settings.scan_schedule_enabled IS 'Enable/disable automatic scheduled scanning';
COMMENT ON COLUMN user_settings.scan_schedule_cron IS 'Cron expression for scan schedule (e.g., "0 9 * * *" for daily at 9 AM)';
COMMENT ON COLUMN user_settings.scan_schedule_timezone IS 'Timezone for schedule (e.g., Europe/Oslo)';
