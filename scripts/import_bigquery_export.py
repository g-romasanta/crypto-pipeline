"""
ONE-TIME MIGRATION HELPER
=========================
Converts a CSV exported from the old BigQuery table into
data/daily_prices.csv (same columns, ISO-8601 timestamps), so the
historical rows carry over.

Usage:
    python scripts/import_bigquery_export.py path/to/bigquery_export.csv

Run it once, BEFORE the first GitHub Actions run, then commit the result.
"""

import sys
from pathlib import Path

import pandas as pd

from load import COLUMNS, DATA_FILE


def main(src: str) -> None:
    df = pd.read_csv(src)
    missing = [c for c in COLUMNS if c not in df.columns]
    if missing:
        raise SystemExit(f"Export is missing columns: {missing}")
    df = df[COLUMNS].copy()
    for col in ("coingecko_updated_at", "extracted_at_utc"):
        df[col] = pd.to_datetime(df[col], utc=True).dt.strftime("%Y-%m-%dT%H:%M:%SZ")
    df = df.sort_values(["extracted_at_utc", "coin_id"])

    # The early history has several test runs on the same day. Keep only the
    # LAST run per coin per UTC date so the history is one row per coin per
    # day (what the moving-average and day-over-day queries assume).
    before = len(df)
    df["_date"] = df["extracted_at_utc"].str[:10]
    df = df.drop_duplicates(subset=["coin_id", "_date"], keep="last").drop(columns="_date")
    print(f"Dropped {before - len(df)} extra same-day rows")
    DATA_FILE.parent.mkdir(parents=True, exist_ok=True)
    df.to_csv(DATA_FILE, index=False)
    print(f"Wrote {len(df)} rows to {DATA_FILE}")


if __name__ == "__main__":
    if len(sys.argv) != 2:
        raise SystemExit(__doc__)
    main(sys.argv[1])
