-- ============================================================
-- ANALYSIS QUERIES
-- ============================================================
-- Run these directly in the BigQuery Console's Query Editor.
-- Replace `your-project-id` with your actual GCP project ID.
-- ============================================================


-- 1. LATEST PRICE PER COIN
-- JARGON: a WINDOW FUNCTION (like ROW_NUMBER() OVER (...)) lets you
-- rank/number rows within groups without collapsing them into one row
-- per group the way GROUP BY does. Here we rank each coin's rows by
-- most recent extraction, then keep only rank #1 (the latest one).
WITH ranked_prices AS (
  SELECT
    coin_id,
    price_usd,
    change_24h_pct,
    extracted_at_utc,
    ROW_NUMBER() OVER (
      PARTITION BY coin_id
      ORDER BY extracted_at_utc DESC
    ) AS recency_rank
  FROM `your-project-id.crypto_pipeline.daily_prices`
)
SELECT coin_id, price_usd, change_24h_pct, extracted_at_utc
FROM ranked_prices
WHERE recency_rank = 1
ORDER BY coin_id;


-- 2. 7-DAY MOVING AVERAGE PRICE
-- JARGON: a MOVING AVERAGE smooths out day-to-day noise by averaging
-- each day with the N days before it. "ROWS BETWEEN 6 PRECEDING AND
-- CURRENT ROW" means "average this row plus the 6 rows before it" = a
-- 7-row (7-day, since we load once daily) rolling window.
SELECT
  coin_id,
  extracted_at_utc,
  price_usd,
  AVG(price_usd) OVER (
    PARTITION BY coin_id
    ORDER BY extracted_at_utc
    ROWS BETWEEN 6 PRECEDING AND CURRENT ROW
  ) AS moving_avg_7day
FROM `your-project-id.crypto_pipeline.daily_prices`
ORDER BY coin_id, extracted_at_utc;


-- 3. DAY-OVER-DAY PRICE CHANGE (self-calculated, independent of
-- CoinGecko's own change_24h_pct field — useful as a cross-check)
-- JARGON: LAG() looks BACKWARD to a previous row within the same
-- partition (here, the previous day's price for the same coin).
-- This is a common pattern for period-over-period comparisons.
SELECT
  coin_id,
  extracted_at_utc,
  price_usd,
  LAG(price_usd) OVER (
    PARTITION BY coin_id
    ORDER BY extracted_at_utc
  ) AS previous_day_price,
  ROUND(
    SAFE_DIVIDE(
      price_usd - LAG(price_usd) OVER (
        PARTITION BY coin_id ORDER BY extracted_at_utc
      ),
      LAG(price_usd) OVER (
        PARTITION BY coin_id ORDER BY extracted_at_utc
      )
    ) * 100,
    2
  ) AS day_over_day_pct_change
  -- SAFE_DIVIDE returns NULL instead of throwing an error if you ever
  -- divide by zero (e.g. on the very first row, where there's no
  -- previous price to compare against). This is a defensive-SQL habit,
  -- same principle as the .get() calls in transform.py.
FROM `your-project-id.crypto_pipeline.daily_prices`
ORDER BY coin_id, extracted_at_utc;


-- 4. DATA QUALITY CHECK: any duplicate loads for the same coin/day?
-- Useful sanity check in case the GitHub Actions job ever ran twice
-- by accident.
SELECT
  coin_id,
  DATE(extracted_at_utc) AS load_date,
  COUNT(*) AS row_count
FROM `your-project-id.crypto_pipeline.daily_prices`
GROUP BY coin_id, load_date
HAVING COUNT(*) > 1;
