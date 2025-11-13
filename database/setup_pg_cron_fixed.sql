-- ВИПРАВЛЕНИЙ SQL для Supabase pg_cron
-- Замість current_setting використовуємо прямий service role key

-- 1. Видали старий job
SELECT cron.unschedule('run-scheduled-scans');

-- 2. Створи новий job з ПРАВИЛЬНИМ ключем
-- ВАЖЛИВО: Замість YOUR_SERVICE_ROLE_KEY_HERE вставте ваш реальний service role key
-- Його можна знайти в Supabase Dashboard → Settings → API → service_role key (secret)

SELECT cron.schedule(
  'run-scheduled-scans',
  '*/5 * * * *',  -- Кожні 5 хвилин (але функція сканує тільки якщо час співпадає!)
  $$
  SELECT net.http_post(
    url := 'https://ptrmidlhfdbybxmyovtm.supabase.co/functions/v1/scheduled-scanner',
    headers := jsonb_build_object(
      'Content-Type', 'application/json',
      'Authorization', 'Bearer YOUR_SERVICE_ROLE_KEY_HERE'
    ),
    body := '{}'::jsonb
  ) AS request_id;
  $$
);

-- 3. Перевір що job створено
SELECT jobid, schedule, jobname, active FROM cron.job;

-- 4. Подивись логи (якщо є помилки)
SELECT * FROM cron.job_run_details
ORDER BY start_time DESC
LIMIT 10;
