# Daily Crypto Price Pipeline

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)

An end-to-end ETL pipeline that extracts live cryptocurrency prices, transforms them, and loads them into a cloud data warehouse — fully automated, serverless, and running on a daily schedule with no manual intervention.

## What it does

Every day at 6:00 AM UTC, this pipeline automatically:

1. **Extracts** current prices for Bitcoin, Ethereum, and Solana from the CoinGecko API
2. **Transforms** the data with pandas — cleaning, validating, and reshaping it into a structured schema
3. **Loads** it into Google BigQuery, building a growing historical dataset over time

The result is a queryable, cloud-hosted table used for SQL-based trend analysis — moving averages, day-over-day price changes, and more.

## Architecture

```
Cloud Scheduler (daily, 6:00 AM UTC)
        │
        │  triggers via HTTPS (OIDC-authenticated, no static keys)
        ▼
Cloud Function (Python, serverless)
        │
        ▼
CoinGecko API → extract → transform → load → BigQuery
```

The entire pipeline runs inside Google Cloud Platform — no external server, no laptop required, and no downloadable credentials anywhere in the flow. Authentication is handled through GCP's own service account identity system.

## Tech stack

- **Python** — extraction, transformation, and load logic
- **pandas** — data cleaning and validation
- **Google BigQuery** — cloud data warehouse
- **Cloud Functions** — serverless compute
- **Cloud Scheduler** — daily automation trigger
- **SQL** — window functions, moving averages, trend analysis

## Sample output

![BigQuery table showing accumulated daily crypto price rows across multiple days](assets/bigquery_table_sample.png)

**Latest price snapshot (July 14, 2026):**

| coin_id | price_usd | change_24h_pct | extracted_at_utc |
|---|---|---|---|
| bitcoin | 62,388.00 | -0.63 | 2026-07-14 03:32:42 UTC |
| ethereum | 1,777.91 | -0.11 | 2026-07-14 03:32:42 UTC |
| solana | 74.65 | -1.47 | 2026-07-14 03:32:42 UTC |

The table has accumulated rows across multiple days of runs, confirming the pipeline correctly builds historical data rather than overwriting it on each run.

## What this project demonstrates

- Designing and deploying a real, unattended ETL pipeline (not a one-off script)
- Working with a cloud data warehouse and writing analytical SQL (window functions, moving averages)
- Deploying serverless infrastructure (Cloud Functions) and scheduling it (Cloud Scheduler)
- Authenticating securely without static keys, using service account identity end to end
- Debugging real IAM/permissions issues across multiple GCP services — a realistic slice of cloud data engineering work
- Basic data quality validation and defensive coding practices

## Project structure

```
crypto-pipeline/
├── scripts/            # Local/manual-run version of the pipeline
├── cloud_function/      # Deployed version (entry point: run_pipeline)
├── sql/                 # Analysis queries (trends, moving averages, QA checks)
├── .github/workflows/   # Alternative orchestration approach (see SETUP.md)
├── assets/              # Screenshots
├── requirements.txt
└── LICENSE
```

## Documentation

For the full step-by-step build guide — every command used, a jargon glossary, and a log of every real error encountered and fixed along the way — see **[SETUP.md](SETUP.md)**.

## License

MIT — see [LICENSE](LICENSE).
