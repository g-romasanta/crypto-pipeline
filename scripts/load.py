"""
LOAD STAGE
==========
This is the "L" in ETL.

JARGON: "Load" means writing the transformed data into its final destination
— usually a DATA WAREHOUSE (a database built for analysis/reporting rather
than for running an app). We're using Google BigQuery, GCP's fully-managed,
serverless (you don't manage any servers yourself — Google handles that)
data warehouse.

Some vocabulary you'll see below:
- PROJECT: the top-level container in GCP that everything (billing,
  resources, permissions) lives under. Like a workspace.
- DATASET: in BigQuery, a dataset is a folder-like grouping of tables.
  (Confusingly, "dataset" here just means "a collection of tables," not
  "a single spreadsheet of data" like in general data science speak.)
- TABLE: same concept as a SQL table — rows and typed columns.
- SERVICE ACCOUNT: a non-human Google Cloud identity (like a robot user)
  that your code authenticates as, instead of using your personal Google
  login. You give it only the specific permissions it needs
  (PRINCIPLE OF LEAST PRIVILEGE — never grant more access than required).
- CREDENTIALS / KEY FILE: a JSON file containing the secret "password" for
  a service account. This file must NEVER be committed to GitHub — it goes
  in GitHub Secrets instead (explained in the README).
- IDEMPOTENT / APPEND: our load here APPENDS new rows every run rather than
  overwriting the table, since we want a growing history of daily prices,
  not just the latest snapshot.
"""

import os
import pandas as pd
from google.cloud import bigquery


# These identify exactly which table in which dataset in which project
# we're writing to. Set as environment variables so the same code works
# in different environments (your laptop vs. GitHub Actions) without
# editing the code itself.
PROJECT_ID = os.environ["GCP_PROJECT_ID"]
DATASET_ID = os.environ.get("BQ_DATASET_ID", "crypto_pipeline")
TABLE_ID = os.environ.get("BQ_TABLE_ID", "daily_prices")


def load_to_bigquery(df: pd.DataFrame) -> None:
    """
    Appends the given DataFrame as new rows into a BigQuery table.

    JARGON: the "client" object below is our authenticated connection to
    BigQuery — every request to Google's servers goes through it.
    Authentication happens automatically here via the
    GOOGLE_APPLICATION_CREDENTIALS environment variable, which should point
    to your service account's JSON key file.
    """
    client = bigquery.Client(project=PROJECT_ID)

    # Fully-qualified table name: project.dataset.table
    # This is the exact same three-level naming convention BigQuery's SQL
    # editor uses when you query this table later.
    full_table_id = f"{PROJECT_ID}.{DATASET_ID}.{TABLE_ID}"

    job_config = bigquery.LoadJobConfig(
        # WRITE_APPEND = add these rows to whatever's already in the table.
        # The alternative, WRITE_TRUNCATE, would delete existing rows first
        # — we don't want that, since we're building up daily history.
        write_disposition=bigquery.WriteDisposition.WRITE_APPEND,
        # autodetect lets BigQuery infer column types (string, float,
        # timestamp) from the DataFrame automatically on the table's very
        # first run. After the table exists, its schema is locked in.
        autodetect=True,
    )

    # load_table_from_dataframe kicks off a LOAD JOB — an asynchronous
    # background task on Google's servers. .result() blocks (waits) until
    # that job finishes, so we know for certain the data landed before the
    # script exits.
    load_job = client.load_table_from_dataframe(
        df, full_table_id, job_config=job_config
    )
    load_job.result()

    print(f"Loaded {len(df)} rows into {full_table_id}")


if __name__ == "__main__":
    from extract import extract_raw_prices
    from transform import transform_to_dataframe

    raw = extract_raw_prices()
    clean_df = transform_to_dataframe(raw)
    load_to_bigquery(clean_df)
