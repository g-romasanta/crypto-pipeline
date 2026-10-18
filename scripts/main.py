"""
ORCHESTRATION SCRIPT
=====================
Single entry point that runs Extract -> Transform -> Load, then the SQL
analysis. GitHub Actions runs this once a day (see
.github/workflows/daily_pipeline.yml).
"""

from extract import extract_raw_prices
from transform import transform_to_dataframe
from load import load_to_csv
from analyze import run_analysis


def run_pipeline() -> None:
    print("Starting pipeline run...")

    print("Step 1/4: Extracting raw data from CoinGecko API...")
    raw_data = extract_raw_prices()

    print("Step 2/4: Transforming raw data into a clean table...")
    clean_df = transform_to_dataframe(raw_data)
    print(clean_df)

    print("Step 3/4: Loading into data/daily_prices.csv...")
    load_to_csv(clean_df)

    print("Step 4/4: Running SQL analysis...")
    run_analysis()

    print("Pipeline run complete.")


if __name__ == "__main__":
    run_pipeline()
