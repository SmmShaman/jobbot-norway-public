-- ====================================================================
-- ШВИДКЕ ОЧИЩЕННЯ: Видалити всі старі дані за 30 секунд
-- ====================================================================
-- Скопіюй ці команди в Supabase SQL Editor і запусти (F5)
-- URL: https://supabase.com/dashboard/project/ptrmidlhfdbybxmyovtm/sql/new
-- ====================================================================

-- 1️⃣ ПЕРЕВІРКА: Скільки є зараз?
SELECT
    'scan_tasks' as table_name,
    COUNT(*) as total_records,
    COUNT(CASE WHEN status = 'PENDING' THEN 1 END) as pending,
    COUNT(CASE WHEN status = 'PROCESSING' THEN 1 END) as processing,
    COUNT(CASE WHEN status = 'COMPLETED' THEN 1 END) as completed,
    COUNT(CASE WHEN status = 'FAILED' THEN 1 END) as failed
FROM scan_tasks

UNION ALL

SELECT
    'jobs' as table_name,
    COUNT(*) as total_records,
    COUNT(CASE WHEN skyvern_status = 'PENDING' THEN 1 END) as pending,
    COUNT(CASE WHEN skyvern_status = 'PROCESSING' THEN 1 END) as processing,
    COUNT(CASE WHEN skyvern_status = 'COMPLETED' THEN 1 END) as completed,
    COUNT(CASE WHEN skyvern_status = 'FAILED' THEN 1 END) as failed
FROM jobs;

-- ====================================================================
-- 2️⃣ ВИДАЛЕННЯ (розкоментуй ці рядки щоб видалити):
-- ====================================================================

-- ВАРІАНТ А: Видалити ВСЕ (почати з нуля)
-- DELETE FROM jobs;
-- DELETE FROM scan_tasks;

-- ВАРІАНТ Б: Видалити тільки завершені та помилкові
-- DELETE FROM jobs WHERE skyvern_status IN ('COMPLETED', 'FAILED');
-- DELETE FROM scan_tasks WHERE status IN ('COMPLETED', 'FAILED');

-- ВАРІАНТ В: Видалити тільки старіші за сьогодні
-- DELETE FROM jobs WHERE created_at < CURRENT_DATE;
-- DELETE FROM scan_tasks WHERE created_at < CURRENT_DATE;

-- ====================================================================
-- 3️⃣ ПЕРЕВІРКА: Що залишилось?
-- ====================================================================

SELECT
    'scan_tasks' as table_name,
    COUNT(*) as remaining_records
FROM scan_tasks

UNION ALL

SELECT
    'jobs' as table_name,
    COUNT(*) as remaining_records
FROM jobs;

-- ====================================================================
-- ✅ ГОТОВО! Тепер можна створювати нові scan_tasks
-- ====================================================================
