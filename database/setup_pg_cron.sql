-- Setup Supabase pg_cron for automatic scheduled scanning
-- This will check every 5 minutes if any user's schedule matches and run scan

-- 1. Enable pg_cron extension (if not already enabled)
CREATE EXTENSION IF NOT EXISTS pg_cron;

-- 2. Grant permissions to postgres user
GRANT USAGE ON SCHEMA cron TO postgres;

-- 3. Schedule the job to run every 5 minutes
-- This will call the scheduled-scanner Edge Function
SELECT cron.schedule(
  'run-scheduled-scans', -- Job name
  '*/5 * * * *',         -- Every 5 minutes
  $$
  SELECT
    net.http_post(
      url := 'https://ptrmidlhfdbybxmyovtm.supabase.co/functions/v1/scheduled-scanner',
      headers := jsonb_build_object(
        'Content-Type', 'application/json',
        'Authorization', 'Bearer ' || current_setting('app.settings.service_role_key')
      ),
      body := '{}'::jsonb
    ) AS request_id;
  $$
);

-- View scheduled jobs
SELECT * FROM cron.job;

-- Unschedule job (if needed):
-- SELECT cron.unschedule('run-scheduled-scans');
