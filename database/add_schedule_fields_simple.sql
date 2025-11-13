-- Simple version: Just add the required fields to user_settings
-- Run this in Supabase Dashboard -> SQL Editor

ALTER TABLE user_settings
ADD COLUMN IF NOT EXISTS scan_schedule_enabled BOOLEAN DEFAULT false,
ADD COLUMN IF NOT EXISTS scan_schedule_cron VARCHAR(50) DEFAULT '0 9 * * *',
ADD COLUMN IF NOT EXISTS scan_schedule_timezone VARCHAR(50) DEFAULT 'Europe/Oslo';
