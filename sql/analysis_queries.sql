-- ============================================================
-- ANALYSIS QUERIES (SQLite dialect)
-- ============================================================
-- scripts/analyze.py loads data/daily_prices.csv into an in-memory SQLite
-- database (table: daily_prices) and runs each query below. Queries are
-- separated by lines starting with "-- name:".
-- (The original BigQuery versions are in legacy_gcp/.)
-- ============================================================

-- name: latest_price_per_coin
-- ROW_NUMBER() window function: rank each coin's rows by recency, keep #1.
WITH ranked_prices AS (
  SELECT
    coin_id, price_usd, change_24h_pct, extracted_at_utc,
    ROW_NUMBER() OVER (
      PARTITION BY coin_id ORDER BY extracted_at_utc DESC
    ) AS recency_rank
  FROM daily_prices
)
SELECT coin_id, price_usd, change_24h_pct, extracted_at_utc
FROM ranked_prices
WHERE recency_rank = 1
ORDER BY coin_id;

-- name: moving_average_7day
-- 7-row rolling average (one row per coin per day = 7-day window).
SELECT
  coin_id, extracted_at_utc, price_usd,
  ROUND(AVG(price_usd) OVER (
    PARTITION BY coin_id
    ORDER BY extracted_at_utc
    ROWS BETWEEN 6 PRECEDING AND CURRENT ROW
  ), 2) AS moving_avg_7day
FROM daily_prices
ORDER BY coin_id, extracted_at_utc;

-- name: day_over_day_change
-- LAG() looks at the previous row for the same coin. NULLIF avoids
-- dividing by zero (SQLite's equivalent of BigQuery's SAFE_DIVIDE).
SELECT
  coin_id, extracted_at_utc, price_usd,
  LAG(price_usd) OVER (
    PARTITION BY coin_id ORDER BY extracted_at_utc
  ) AS previous_day_price,
  ROUND(
    (price_usd - LAG(price_usd) OVER (PARTITION BY coin_id ORDER BY extracted_at_utc))
    / NULLIF(LAG(price_usd) OVER (PARTITION BY coin_id ORDER BY extracted_at_utc), 0)
    * 100, 2
  ) AS day_over_day_pct_change
FROM daily_prices
ORDER BY coin_id, extracted_at_utc;

-- name: duplicate_check
-- Data quality check: any coin loaded more than once on the same UTC day?
SELECT
  coin_id,
  substr(extracted_at_utc, 1, 10) AS load_date,
  COUNT(*) AS row_count
FROM daily_prices
GROUP BY coin_id, load_date
HAVING COUNT(*) > 1;

-- name: missing_days
-- Data quality check: which calendar days (UTC) have NO data at all?
-- A RECURSIVE CTE generates one row per day from the first load date up to
-- yesterday, then we keep the days that never appear in daily_prices.
WITH RECURSIVE days(d) AS (
  SELECT MIN(substr(extracted_at_utc, 1, 10)) FROM daily_prices
  UNION ALL
  SELECT date(d, '+1 day') FROM days WHERE d < date('now', '-1 day')
)
SELECT d AS missing_day
FROM days
WHERE d NOT IN (SELECT DISTINCT substr(extracted_at_utc, 1, 10) FROM daily_prices)
ORDER BY d;
