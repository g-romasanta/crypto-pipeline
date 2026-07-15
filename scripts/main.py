"""
ORCHESTRATION SCRIPT
=====================
JARGON: "Orchestration" means controlling the ORDER and TIMING of pipeline
stages — making sure Extract finishes before Transform starts, Transform
finishes before Load starts, and the whole thing runs on a schedule (daily).

Real-world data engineering teams often use dedicated orchestration tools
like Apache Airflow or Dagster for this. For a project this size, a single
Python script run on a schedule (via GitHub Actions, see the README) is a
perfectly legitimate and common lightweight alternative — you don't need
heavy tooling until your pipeline has many interdependent steps.

This file is the single ENTRY POINT (the one command you actually run) that
ties the three stages together.
"""

from extract import extract_raw_prices
from transform import transform_to_dataframe
from load import load_to_bigquery


def run_pipeline() -> None:
    print("Starting pipeline run...")

    print("Step 1/3: Extracting raw data from CoinGecko API...")
    raw_data = extract_raw_prices()

    print("Step 2/3: Transforming raw data into a clean table...")
    clean_df = transform_to_dataframe(raw_data)
    print(clean_df)

    print("Step 3/3: Loading clean data into BigQuery...")
    load_to_bigquery(clean_df)

    print("Pipeline run complete.")


if __name__ == "__main__":
    run_pipeline()
