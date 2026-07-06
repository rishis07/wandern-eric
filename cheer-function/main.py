import json
import logging
import os
import time
from datetime import datetime, timezone

import functions_framework
import requests
from flask import jsonify
from google.api_core.exceptions import PreconditionFailed
from google.cloud import storage

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

GCP_PROJECT_ID = os.getenv("GCP_PROJECT_ID")
GCP_BUCKET_NAME = os.getenv("GCP_BUCKET_NAME")

MAX_APPEND_RETRIES = 5


def _cheers_blob_name(month_key):
    # One file per calendar month under cheers/ (e.g. cheers/2026-07.json) so
    # a monthly count only ever needs to read one small file, not filter an
    # ever-growing log.
    return f"cheers/{month_key}.json"


# specs/0006: same origins as the bucket's cors.json, plus POST.
ALLOWED_ORIGINS = {
    "http://localhost:5173",
    "https://wandern-eric.github.io",
    "https://rishis07.github.io",
    "https://wandern-eric.de",
}


def _cors_headers(origin):
    headers = {"Vary": "Origin"}
    if origin in ALLOWED_ORIGINS:
        headers["Access-Control-Allow-Origin"] = origin
        headers["Access-Control-Allow-Methods"] = "POST, OPTIONS"
        headers["Access-Control-Allow-Headers"] = "Content-Type"
        headers["Access-Control-Max-Age"] = "3600"
    return headers


def _client_ip(request):
    # Cloud Run's front end appends the address it actually observed as the
    # LAST entry in X-Forwarded-For; anything before that could be spoofed by
    # the client, so the last entry is the only one worth trusting.
    forwarded = request.headers.get("X-Forwarded-For", "")
    parts = [p.strip() for p in forwarded.split(",") if p.strip()]
    return parts[-1] if parts else request.remote_addr


def _geolocate_country(ip):
    # Best-effort only — a cheer must still count even if this fails, so we
    # deliberately swallow any error here and fall back to country: None.
    # Logged (not silent) so failures are diagnosable — but the IP itself
    # must NEVER be logged (it's the one thing this feature promises not to
    # persist). That also rules out exc_info=True / str(exc): requests'
    # error messages embed the full request URL, which contains the IP
    # (e.g. "...for url: https://ipapi.co/1.2.3.4/json/") — only the
    # exception's type name is safe to log.
    if not ip:
        logger.warning("geolocation skipped: no client IP resolved")
        return None
    try:
        resp = requests.get(f"https://ipapi.co/{ip}/json/", timeout=3)
        resp.raise_for_status()
        data = resp.json()
        code = data.get("country_code")
        if not code or len(code) != 2:
            logger.warning("geolocation returned no usable country_code (reason=%s)", data.get("reason") or data.get("error"))
            return None
        logger.info("geolocation resolved country=%s", code)
        return code
    except Exception as exc:
        logger.warning("geolocation request failed: %s", type(exc).__name__)
        return None


def _append_cheer(bucket, country):
    month_key = datetime.now(timezone.utc).strftime("%Y-%m")
    blob = bucket.blob(_cheers_blob_name(month_key))

    for attempt in range(MAX_APPEND_RETRIES):
        if blob.exists():
            blob.reload()
            generation = blob.generation
            content = json.loads(blob.download_as_text())
        else:
            generation = 0  # only succeed if the object still doesn't exist
            content = []

        content.append(
            {
                "timestamp": datetime.now(timezone.utc).isoformat(),
                "country": country,
                "source": "organic",
            }
        )

        try:
            blob.upload_from_string(
                json.dumps(content),
                content_type="application/json",
                if_generation_match=generation,
            )
            return content
        except PreconditionFailed:
            time.sleep(0.1 * (attempt + 1))

    raise RuntimeError("Failed to append cheer after retries")


@functions_framework.http
def cheer(request):
    origin = request.headers.get("Origin", "")
    headers = _cors_headers(origin)

    if request.method == "OPTIONS":
        return ("", 204, headers)

    if request.method != "POST":
        return (jsonify({"error": "method not allowed"}), 405, headers)

    country = _geolocate_country(_client_ip(request))

    bucket = storage.Client(project=GCP_PROJECT_ID).bucket(GCP_BUCKET_NAME)
    _append_cheer(bucket, country)

    return (jsonify({"ok": True}), 200, headers)
