-- Create processed_updates table for Telegram webhook deduplication
-- Prevents processing the same update multiple times

CREATE TABLE IF NOT EXISTS processed_updates (
  update_id BIGINT PRIMARY KEY,
  processed_at TIMESTAMPTZ DEFAULT NOW()
);

-- Create index for faster cleanup queries
CREATE INDEX IF NOT EXISTS idx_processed_updates_processed_at
ON processed_updates(processed_at);

-- Function to automatically cleanup old updates (>24 hours)
CREATE OR REPLACE FUNCTION cleanup_old_updates()
RETURNS void AS $$
BEGIN
  DELETE FROM processed_updates
  WHERE processed_at < NOW() - INTERVAL '24 hours';
END;
$$ LANGUAGE plpgsql;

-- Schedule cron job to run cleanup every 6 hours
-- NOTE: Requires pg_cron extension to be enabled in Supabase
SELECT cron.schedule(
  'cleanup-processed-updates',
  '0 */6 * * *',
  'SELECT cleanup_old_updates();'
);

-- Verify table creation
SELECT
  table_name,
  (SELECT COUNT(*) FROM information_schema.columns WHERE table_name = 'processed_updates') as column_count
FROM information_schema.tables
WHERE table_name = 'processed_updates';

-- Add comment for documentation
COMMENT ON TABLE processed_updates IS 'Stores Telegram update IDs to prevent duplicate processing (TTL: 24 hours)';
COMMENT ON COLUMN processed_updates.update_id IS 'Unique identifier from Telegram webhook update';
COMMENT ON COLUMN processed_updates.processed_at IS 'Timestamp when the update was processed';
