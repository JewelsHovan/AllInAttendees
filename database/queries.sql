-- Useful queries for All In 2025 attendee database

-- =====================================================
-- NEW ATTENDEES (signed up in last 24 hours)
-- =====================================================
-- This shows attendees who first appeared in today's run
SELECT 
    first_name,
    last_name,
    email,
    organization,
    job_title,
    detail_country,
    detail_industry,
    first_seen_at,
    DATE(first_seen_at) as signup_date
FROM attendees
WHERE first_seen_at >= CURRENT_DATE - INTERVAL '1 day'
ORDER BY first_seen_at DESC;

-- Count of new attendees by day
SELECT 
    DATE(first_seen_at) as signup_date,
    COUNT(*) as new_attendees
FROM attendees
GROUP BY DATE(first_seen_at)
ORDER BY signup_date DESC;

-- =====================================================
-- NEW ATTENDEES FROM SPECIFIC RUN
-- =====================================================
-- Get attendees that were newly inserted in a specific run
SELECT 
    a.first_name,
    a.last_name,
    a.email,
    a.organization,
    a.detail_country,
    a.first_seen_at
FROM attendees a
JOIN scraper_runs sr ON a.last_seen_run_id = sr.id
WHERE sr.run_timestamp = '2025-09-13 00:00:00'::timestamp  -- Replace with your run timestamp
  AND a.first_seen_at = sr.run_timestamp;

-- =====================================================
-- GROWTH METRICS
-- =====================================================
-- Daily growth statistics
WITH daily_stats AS (
    SELECT 
        DATE(first_seen_at) as date,
        COUNT(*) as new_signups
    FROM attendees
    GROUP BY DATE(first_seen_at)
),
cumulative AS (
    SELECT 
        date,
        new_signups,
        SUM(new_signups) OVER (ORDER BY date) as total_attendees
    FROM daily_stats
)
SELECT 
    date,
    new_signups,
    total_attendees,
    ROUND(100.0 * new_signups / LAG(total_attendees) OVER (ORDER BY date), 2) as growth_rate_pct
FROM cumulative
ORDER BY date DESC
LIMIT 30;

-- =====================================================
-- RECENT CHANGES
-- =====================================================
-- Find attendees who updated their profiles recently
SELECT 
    first_name,
    last_name,
    organization,
    last_updated_at,
    update_count
FROM attendees
WHERE last_updated_at > first_seen_at  -- Has been updated since first seen
  AND last_updated_at >= CURRENT_DATE - INTERVAL '1 day'
ORDER BY last_updated_at DESC;

-- =====================================================
-- RUN COMPARISON
-- =====================================================
-- Compare two runs to see what changed
WITH run1 AS (
    SELECT COUNT(*) as count FROM attendees 
    WHERE last_seen_run_id = 1  -- First run ID
),
run2 AS (
    SELECT COUNT(*) as count FROM attendees 
    WHERE last_seen_run_id = 2  -- Second run ID
),
new_in_run2 AS (
    SELECT COUNT(*) as count FROM attendees 
    WHERE first_seen_at = (SELECT run_timestamp FROM scraper_runs WHERE id = 2)
)
SELECT 
    r1.count as run1_total,
    r2.count as run2_total,
    n.count as new_attendees,
    r2.count - n.count as updated_attendees
FROM run1 r1, run2 r2, new_in_run2 n;

-- =====================================================
-- INTERESTING INSIGHTS
-- =====================================================
-- Companies with most attendees
SELECT 
    organization,
    COUNT(*) as attendee_count,
    STRING_AGG(DISTINCT detail_country, ', ') as countries
FROM attendees
WHERE organization IS NOT NULL
GROUP BY organization
HAVING COUNT(*) > 5
ORDER BY attendee_count DESC;

-- New companies (all attendees from company are new)
SELECT 
    organization,
    COUNT(*) as attendee_count,
    MIN(first_seen_at) as first_appearance
FROM attendees
WHERE organization IS NOT NULL
  AND first_seen_at >= CURRENT_DATE - INTERVAL '7 days'
GROUP BY organization
ORDER BY first_appearance DESC;