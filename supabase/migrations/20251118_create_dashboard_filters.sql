-- Create table for storing users' dashboard filter preferences
CREATE TABLE IF NOT EXISTS dashboard_filters (
  id UUID DEFAULT gen_random_uuid() PRIMARY KEY,
  user_id UUID NOT NULL REFERENCES auth.users(id) ON DELETE CASCADE,
  title TEXT DEFAULT '',
  company TEXT DEFAULT '',
  location TEXT DEFAULT '',
  status TEXT DEFAULT '',
  added_date DATE,
  added_interval INTEGER,
  updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
  UNIQUE(user_id)
);

CREATE INDEX IF NOT EXISTS idx_dashboard_filters_user_id ON dashboard_filters(user_id);

ALTER TABLE dashboard_filters ENABLE ROW LEVEL SECURITY;

CREATE POLICY "Users can read their own dashboard filters"
  ON dashboard_filters FOR SELECT
  USING (auth.uid() = user_id);

CREATE POLICY "Users can insert/update their own dashboard filters"
  ON dashboard_filters FOR INSERT, UPDATE
  WITH CHECK (auth.uid() = user_id)
  USING (auth.uid() = user_id);

CREATE POLICY "Users can delete their own dashboard filters"
  ON dashboard_filters FOR DELETE
  USING (auth.uid() = user_id);

CREATE POLICY "Service role can manage all dashboard filters"
  ON dashboard_filters FOR ALL
  USING (true)
  WITH CHECK (true);
