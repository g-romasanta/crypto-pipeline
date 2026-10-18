"""
ANALYSIS STAGE
==============
Loads data/daily_prices.csv into an in-memory SQLite database, runs the SQL
in sql/analysis_queries.sql (window functions: ROW_NUMBER, LAG, moving
average), and writes:
  - reports/latest_summary.md   (latest snapshot + data quality checks:
                                 duplicates and missing days)
  - reports/price_trends.csv    (per-day price, 7-day average, day-over-day %)

JARGON: SQLite is a small SQL database engine built into Python (the
sqlite3 module). ":memory:" means the database lives only in RAM for the
run - the CSV stays the single source of truth.
"""

import re
import sqlite3
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parent.parent
DATA_FILE = ROOT / "data" / "daily_prices.csv"
SQL_FILE = ROOT / "sql" / "analysis_queries.sql"
REPORT_DIR = ROOT / "reports"


def _load_queries() -> dict:
    text = SQL_FILE.read_text()
    parts = re.split(r"^-- name: (\w+)\s*$", text, flags=re.M)
    # parts = [preamble, name1, body1, name2, body2, ...]
    return {parts[i]: parts[i + 1].strip() for i in range(1, len(parts), 2)}


def run_analysis() -> None:
    if not DATA_FILE.exists():
        print("No data file yet - skipping analysis.")
        return

    REPORT_DIR.mkdir(exist_ok=True)
    conn = sqlite3.connect(":memory:")
    pd.read_csv(DATA_FILE).to_sql("daily_prices", conn, index=False)
    q = _load_queries()

    latest = pd.read_sql_query(q["latest_price_per_coin"], conn)
    trends = pd.read_sql_query(q["day_over_day_change"], conn)
    ma = pd.read_sql_query(q["moving_average_7day"], conn)
    dupes = pd.read_sql_query(q["duplicate_check"], conn)
    gaps = pd.read_sql_query(q["missing_days"], conn)
    conn.close()

    trends = trends.merge(
        ma[["coin_id", "extracted_at_utc", "moving_avg_7day"]],
        on=["coin_id", "extracted_at_utc"],
    )
    trends.to_csv(REPORT_DIR / "price_trends.csv", index=False)

    lines = [
        "# Latest crypto price snapshot", "",
        "| coin | price (USD) | 24h change (%) | extracted (UTC) |",
        "|---|---|---|---|",
    ]
    for r in latest.itertuples():
        lines.append(
            f"| {r.coin_id} | {r.price_usd:,.2f} | "
            f"{r.change_24h_pct:+.2f} | {r.extracted_at_utc} |"
        )
    missing = gaps["missing_day"].tolist()
    lines += ["", f"Rows in history: {len(trends)}",
              f"Duplicate coin/day loads: {len(dupes)}",
              f"Days with no data: {len(missing)}"]
    if missing:
        lines.append(f"Missing dates (UTC): {', '.join(missing)}")
        print(f"WARNING: no data for {len(missing)} day(s): {', '.join(missing)}")
    lines.append("")
    (REPORT_DIR / "latest_summary.md").write_text("\n".join(lines))
    print((REPORT_DIR / "latest_summary.md").read_text())


if __name__ == "__main__":
    run_analysis()
