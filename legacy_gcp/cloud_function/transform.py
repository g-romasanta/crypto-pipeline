"""
TRANSFORM STAGE
================
This is the "T" in ETL.

JARGON: "Transform" means converting messy/raw data into a clean, structured
SCHEMA (a schema is the defined shape of your data: which columns exist, and
what data type each one is — e.g. price is a float/decimal number, coin_id is
text/string, recorded_at is a timestamp).

Raw API data is nested (a dictionary inside a dictionary) — great for
machines, bad for analysis. We flatten it into a TIDY TABLE: one row per
observation, one column per variable. This is the standard shape SQL and
BigQuery expect.

We use pandas (a Python library for working with tabular data — think of it
as "Excel, but as code") because it makes reshaping, renaming, and adding
columns fast and readable.
"""

import pandas as pd


def transform_to_dataframe(extraction_metadata: dict) -> pd.DataFrame:
    """
    Converts the raw nested API response into a tidy pandas DataFrame.

    JARGON: a DataFrame is pandas' core object — think of it as a table with
    rows and named columns, like a single sheet in Excel or a single SQL
    table.

    Parameters
    ----------
    extraction_metadata : dict
        The output of extract.extract_raw_prices() — contains our own
        extraction timestamp plus CoinGecko's raw nested price data.

    Returns
    -------
    pd.DataFrame
        One row per coin, with clean, flat columns:
        coin_id | price_usd | market_cap_usd | volume_24h_usd |
        change_24h_pct | coingecko_updated_at | extracted_at_utc
    """
    extracted_at = extraction_metadata["extracted_at_utc"]
    raw_prices = extraction_metadata["data"]

    rows = []
    for coin_id, price_info in raw_prices.items():
        rows.append({
            "coin_id": coin_id,
            "price_usd": price_info.get("usd"),
            "market_cap_usd": price_info.get("usd_market_cap"),
            "volume_24h_usd": price_info.get("usd_24h_vol"),
            # ".get()" is used instead of direct[] indexing so that if a key
            # is ever missing from the API response, we get None instead of
            # the whole script crashing. This is a form of DEFENSIVE CODING —
            # writing code that anticipates and gracefully handles bad/missing
            # input rather than assuming everything will always be perfect.
            "change_24h_pct": price_info.get("usd_24h_change"),
            "coingecko_updated_at": price_info.get("last_updated_at"),
            "extracted_at_utc": extracted_at,
        })

    df = pd.DataFrame(rows)

    # Convert CoinGecko's Unix timestamp (seconds since Jan 1 1970 — a very
    # common machine-readable time format) into a proper human-readable
    # datetime column.
    df["coingecko_updated_at"] = pd.to_datetime(
        df["coingecko_updated_at"], unit="s", utc=True
    )
    df["extracted_at_utc"] = pd.to_datetime(df["extracted_at_utc"], utc=True)

    # Basic DATA QUALITY CHECK (same principle as your Data Quality Auditor
    # project): make sure we didn't get any nulls in the price column before
    # we load this into the warehouse. Failing loudly and early here is
    # better than silently loading bad data.
    if df["price_usd"].isnull().any():
        raise ValueError(
            "One or more coins returned a null price_usd — "
            "check the API response before loading."
        )

    return df


if __name__ == "__main__":
    from extract import extract_raw_prices

    raw = extract_raw_prices()
    clean_df = transform_to_dataframe(raw)
    print(clean_df)
