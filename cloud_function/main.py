"""
CLOUD FUNCTION ENTRY POINT
===========================
JARGON: an ENTRY POINT is the one specific function Google Cloud calls when
your Cloud Function is triggered — everything else in this file (and the
imported extract/transform/load modules) is just supporting code that this
one function calls into.

This function is triggered by an HTTP TRIGGER — meaning Google Cloud gives
this deployed function its own unique URL, and calling that URL (with an
HTTP request, the same mechanism your browser uses to load web pages) runs
the code. Cloud Scheduler will be the one calling that URL every day.

Note this reuses the EXACT SAME extract.py, transform.py, and load.py files
from the scripts/ folder — no pipeline logic was rewritten, just wrapped in
a shape Cloud Functions understands.
"""

from extract import extract_raw_prices
from transform import transform_to_dataframe
from load import load_to_bigquery


def run_pipeline(request):
    """
    Cloud Functions' Python runtime always calls your entry point with one
    argument (conventionally named `request`) representing the incoming
    HTTP request. We don't need any data FROM the request here — Cloud
    Scheduler just needs to successfully "ping" this URL to kick things off
    — but the parameter must still be accepted, or Cloud Functions will
    error out expecting it.

    Returning a (message, status_code) tuple is how Cloud Functions expects
    you to respond to the HTTP call — 200 is the standard HTTP status code
    for "success."
    """
    try:
        raw_data = extract_raw_prices()
        clean_df = transform_to_dataframe(raw_data)
        load_to_bigquery(clean_df)
        return (f"Pipeline run complete. Loaded {len(clean_df)} rows.", 200)
    except Exception as e:
        # Returning a 500 (server error) status ensures Cloud Scheduler's
        # own logs will show this run as FAILED rather than silently
        # succeeding — important so you notice if something breaks.
        return (f"Pipeline run failed: {str(e)}", 500)
