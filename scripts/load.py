"""
LOAD STAGE (GitHub-hosted version)
==================================
This is the "L" in ETL.

The pipeline originally loaded into Google BigQuery (see legacy_gcp/). It
now loads into a plain CSV file inside this repository: data/daily_prices.csv.
The GitHub Actions workflow commits that file back to the repo after each
run, so the repository itself is the storage layer and the full price
history is versioned by git.

JARGON:
- APPEND: add new rows to the end of the file instead of overwriting it, so
  we build a growing history of daily prices.
- IDEMPOTENT: running the pipeline twice on the same day does not create
  duplicate rows. We skip any (coin_id, UTC date) already in the file.
"""

from pathlib import Path

import pandas as pd

DATA_FILE = Path(__file__).resolve().parent.parent / "data" / "daily_prices.csv"

COLUMNS = [
    "coin_id",
    "price_usd",
    "market_cap_usd",
    "volume_24h_usd",
    "change_24h_pct",
    "coingecko_updated_at",
    "extracted_at_utc",
]


def load_to_csv(df: pd.DataFrame, path: Path = DATA_FILE) -> int:
    """
    Appends new rows to the CSV, skipping coins already loaded for the same
    UTC date. Returns the number of rows actually written.
    """
    df = df[COLUMNS].copy()
    # Store timestamps as ISO-8601 text so the file is human-readable and
    # SQLite / BigQuery / pandas can all parse it.
    for col in ("coingecko_updated_at", "extracted_at_utc"):
        df[col] = pd.to_datetime(df[col], utc=True).dt.strftime("%Y-%m-%dT%H:%M:%SZ")
    df["_date"] = df["extracted_at_utc"].str[:10]

    if path.exists() and path.stat().st_size > 0:
        existing = pd.read_csv(path)
        seen = set(zip(existing["coin_id"], existing["extracted_at_utc"].str[:10]))
        keep = [(c, d) not in seen for c, d in zip(df["coin_id"], df["_date"])]
        df = df[keep]
        write_header = False
    else:
        path.parent.mkdir(parents=True, exist_ok=True)
        write_header = True

    df = df.drop(columns="_date")
    if df.empty:
        print("No new rows to load (already loaded for today).")
        return 0

    df.to_csv(path, mode="a", header=write_header, index=False)
    print(f"Loaded {len(df)} rows into {path.name}")
    return len(df)


if __name__ == "__main__":
    from extract import extract_raw_prices
    from transform import transform_to_dataframe

    load_to_csv(transform_to_dataframe(extract_raw_prices()))
