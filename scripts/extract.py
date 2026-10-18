"""
EXTRACT STAGE
=============
This is the "E" in ETL (Extract, Transform, Load).

JARGON: "Extract" means pulling raw data from a SOURCE SYSTEM — anything that
holds data you don't own the storage for. Here, our source is a public REST API
(REST = REpresentational State Transfer, a common style for web APIs where you
send an HTTP request to a URL and get data back, usually as JSON).

We use CoinGecko's free API because:
- It requires NO API KEY for basic endpoints (fewer things that can break).
- It has a generous free rate limit (enough for one call a day).
- It returns clean JSON (JavaScript Object Notation — a text format for
  structured data that looks like Python dictionaries/lists).

This script's ONLY job is to fetch raw data and hand it off untouched.
We deliberately do NOT clean or reshape anything here — that's the Transform
stage's job. Keeping stages separate is called SEPARATION OF CONCERNS: each
piece of code has one clear responsibility, which makes pipelines easier to
debug and test.
"""

import os
import time
import requests  # third-party library for making HTTP requests
from datetime import datetime, timezone


# The coins we're tracking. CoinGecko IDs, not ticker symbols.
COIN_IDS = ["bitcoin", "ethereum", "solana"]

# vs_currencies = "against which currencies" — we want USD prices.
VS_CURRENCY = "usd"

API_URL = "https://api.coingecko.com/api/v3/simple/price"


def extract_raw_prices() -> dict:
    """
    Calls the CoinGecko API and returns the raw JSON response as a Python dict.

    JARGON: an API ENDPOINT is a specific URL that does one job (here: give
    current prices). PARAMS (parameters) are the query options we send along
    with the URL, like which coins and which currency we want.

    Returns
    -------
    dict
        Raw, unprocessed data straight from the API. Example shape:
        {
            "bitcoin": {"usd": 65000.0, "usd_24h_change": 1.23, ...},
            "ethereum": {"usd": 3400.0, "usd_24h_change": -0.5, ...},
        }
    """
    params = {
        "ids": ",".join(COIN_IDS),
        "vs_currencies": VS_CURRENCY,
        "include_market_cap": "true",
        "include_24hr_vol": "true",
        "include_24hr_change": "true",
        "include_last_updated_at": "true",
    }

    # Optional: CoinGecko's free "Demo" API key (set as the GitHub secret
    # COINGECKO_API_KEY). Not required, but GitHub-hosted runners share IP
    # addresses with many other users, so the keyless endpoint can
    # occasionally rate-limit (HTTP 429). A key avoids that.
    headers = {}
    api_key = os.environ.get("COINGECKO_API_KEY")
    if api_key:
        headers["x-cg-demo-api-key"] = api_key

    # RETRY WITH BACKOFF: on "too many requests" (429) or a temporary server
    # error (5xx), wait and try again instead of failing the whole daily run
    # on a one-off hiccup. timeout=15 means we never hang forever.
    last_error = None
    for attempt in range(1, 5):
        response = requests.get(API_URL, params=params, headers=headers, timeout=15)
        if response.status_code == 429 or response.status_code >= 500:
            last_error = f"HTTP {response.status_code}"
            time.sleep(10 * attempt)
            continue
        # raise_for_status() throws on other error codes (404 etc.) instead
        # of silently continuing with bad/missing data.
        response.raise_for_status()
        break
    else:
        raise RuntimeError(f"CoinGecko API failed after 4 attempts ({last_error})")

    raw_data = response.json()

    # We stamp our OWN extraction timestamp too (separate from CoinGecko's
    # "last_updated_at"), so we know exactly when OUR pipeline ran — useful
    # for debugging if the pipeline is ever late or skipped a day.
    extraction_metadata = {
        "extracted_at_utc": datetime.now(timezone.utc).isoformat(),
        "data": raw_data,
    }

    return extraction_metadata


if __name__ == "__main__":
    # This block only runs if you execute this file directly
    # (python extract.py), not when it's imported by another script.
    # Handy for quickly testing this stage on its own.
    result = extract_raw_prices()
    print(result)
