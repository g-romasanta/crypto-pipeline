# Daily Crypto Price Pipeline

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)

An end-to-end ETL pipeline that extracts cryptocurrency prices, transforms them, loads them into a versioned dataset, and runs SQL analysis, fully automated by GitHub Actions on a daily schedule.

## What it does

Every day at 6:00 AM UTC, a GitHub Actions workflow:

1. **Extracts** current prices for Bitcoin, Ethereum, and Solana from the CoinGecko API (with retry/backoff on rate limits)
2. **Transforms** the data with pandas: flattening, typing, and validating it into a tidy schema
3. **Loads** new rows into `data/daily_prices.csv`, skipping duplicates so re-runs are safe (idempotent)
4. **Analyzes** the history with SQL (window functions), runs data quality checks (duplicates and missing days), and writes `reports/latest_summary.md` and `reports/price_trends.csv`
5. **Commits** the updated data back to this repository

## Architecture

```
GitHub Actions (cron, daily 6:00 AM UTC)
        │
        ▼
CoinGecko API → extract → transform → load → data/daily_prices.csv
                                                   │
                                                   ▼
                              SQLite (in-memory) + SQL window functions
                                                   │
                                                   ▼
                                     reports/  →  committed to the repo
```

No cloud account and no stored credentials are required: the workflow uses GitHub's built-in `GITHUB_TOKEN` to commit data. A CoinGecko API key is optional (secret `COINGECKO_API_KEY`).

## Tech stack

- **Python**: extraction, transformation, load, orchestration
- **pandas**: cleaning and validation
- **SQL (SQLite)**: `ROW_NUMBER`, `LAG`, and 7-day moving-average window functions
- **GitHub Actions**: scheduling and automation

## Project history

The first version ran on Google Cloud (Cloud Scheduler → Cloud Function → BigQuery) using the GCP free trial. When the trial ended, the pipeline was migrated to run entirely on GitHub Actions. The original GCP code, BigQuery SQL, and build guide are kept in [`legacy_gcp/`](legacy_gcp/).

## Known issues and monitoring

- **Sept 11, 2026 (GCP version):** over about 90 days of daily runs, one run produced no data. BigQuery audit logs show no load job that day, while every neighboring day has one, so the failure happened before the load step. The exact cause is unknown because the Scheduler and function logs had expired. All three coins were missing, so the whole run was skipped, not one coin.
- **Gap after the GCP trial ended:** no data was collected between the end of the trial and the first GitHub Actions run (about a week in October 2026).
- **Monitoring:** every run checks for duplicate loads and for calendar days with no data, and lists any missing dates in `reports/latest_summary.md`. The extract step now retries on rate limits and server errors. Failed workflow runs are visible in the Actions tab, and GitHub can email you about them depending on your notification settings.
- Note: retry logic helps with temporary API errors, but it is not known whether that was the cause of the Sept 11 gap.

## Project structure

```
crypto-pipeline/
├── scripts/            # extract, transform, load, analyze, main
├── sql/                # analysis queries (SQLite)
├── data/               # daily_prices.csv (updated by the workflow)
├── reports/            # latest_summary.md, price_trends.csv
├── legacy_gcp/         # original BigQuery / Cloud Functions version
├── .github/workflows/  # daily_pipeline.yml
└── requirements.txt
```

## Running locally

```bash
pip install -r requirements.txt
python scripts/main.py
```

## Notes

- GitHub cron schedules run in UTC and can start a few minutes late.
- `data/daily_prices.csv` is the single source of truth; the SQLite database is rebuilt in memory on each run.

## License

MIT, see [LICENSE](LICENSE).
