#!/usr/bin/env python3
"""
fetch_results.py
----------------
Fetches the latest second-round election results from the ONPE API
and appends a timestamped row to results.csv.

Designed to be executed by a GitHub Actions cron workflow every 30 minutes.
"""

import csv
import sys
import os
from datetime import datetime, timezone, timedelta

import requests

# ---------------------------------------------------------------------------
# Configuration
# ---------------------------------------------------------------------------

API_URL = (
    "https://resultadosegundavuelta.onpe.gob.pe/"
    "presentacion-backend/resumen-general/participantes"
    "?idEleccion=10&tipoFiltro=eleccion"
)

BASE_URL = "https://resultadosegundavuelta.onpe.gob.pe/"

# CSV file path (relative to repo root)
CSV_FILE = os.path.join(os.path.dirname(os.path.abspath(__file__)), "results.csv")

# Timezone: UTC-5 (Peru)
TZ_PERU = timezone(timedelta(hours=-5))

# Expected number of participants in the API response
EXPECTED_PARTICIPANTS = 2

# HTTP request timeout in seconds
REQUEST_TIMEOUT = 30

REQUEST_HEADERS = {
    "Accept": "application/json, text/plain, */*",
    "Accept-Language": "es-ES,es;q=0.9,en;q=0.8",
    "Cache-Control": "no-cache",
    "Pragma": "no-cache",
    "Referer": BASE_URL,
    "Sec-Fetch-Dest": "empty",
    "Sec-Fetch-Mode": "cors",
    "Sec-Fetch-Site": "same-origin",
    "User-Agent": (
        "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/125.0.0.0 Safari/537.36"
    ),
}

# CSV column headers
HEADERS = [
    "Date",
    "nombreAgrupacionPolitica1",
    "totalVotosValidos1",
    "porcentajeVotosValidos1",
    "porcentajeVotosEmitidos1",
    "nombreAgrupacionPolitica2",
    "totalVotosValidos2",
    "porcentajeVotosValidos2",
    "porcentajeVotosEmitidos2",
]


# ---------------------------------------------------------------------------
# Helper functions
# ---------------------------------------------------------------------------


def fetch_data() -> dict:
    """Call the ONPE API and return the parsed JSON response."""
    try:
        session = requests.Session()
        session.get(BASE_URL, timeout=REQUEST_TIMEOUT, headers=REQUEST_HEADERS)
        response = session.get(API_URL, timeout=REQUEST_TIMEOUT, headers=REQUEST_HEADERS)
        response.raise_for_status()
    except requests.exceptions.RequestException as exc:
        print(f"[ERROR] HTTP request failed: {exc}", file=sys.stderr)
        sys.exit(1)

    try:
        data = response.json()
    except ValueError:
        print("[ERROR] Response is not valid JSON.", file=sys.stderr)
        print(
            f"[ERROR] Content-Type: {response.headers.get('content-type', 'unknown')}",
            file=sys.stderr,
        )
        print(f"[ERROR] Response preview: {response.text[:500]}", file=sys.stderr)
        sys.exit(1)

    return data


def validate_response(data: dict) -> list:
    """Validate the API response structure and return the participants list."""
    if not isinstance(data, dict):
        print("[ERROR] Unexpected response format (not a JSON object).", file=sys.stderr)
        sys.exit(1)

    if not data.get("success"):
        print(
            f"[ERROR] API returned success=false. Message: {data.get('message', 'N/A')}",
            file=sys.stderr,
        )
        sys.exit(1)

    participants = data.get("data")

    if not participants or not isinstance(participants, list):
        print("[ERROR] 'data' field is missing or empty.", file=sys.stderr)
        sys.exit(1)

    if len(participants) != EXPECTED_PARTICIPANTS:
        print(
            f"[ERROR] Expected {EXPECTED_PARTICIPANTS} participants, "
            f"got {len(participants)}.",
            file=sys.stderr,
        )
        sys.exit(1)

    # Verify that each participant has the required keys
    required_keys = [
        "nombreAgrupacionPolitica",
        "totalVotosValidos",
        "porcentajeVotosValidos",
        "porcentajeVotosEmitidos",
    ]
    for i, participant in enumerate(participants):
        for key in required_keys:
            if key not in participant:
                print(
                    f"[ERROR] Participant {i + 1} is missing key '{key}'.",
                    file=sys.stderr,
                )
                sys.exit(1)

    return participants


def build_row(participants: list) -> list:
    """Build a flat CSV row from the two participants."""
    now = datetime.now(TZ_PERU).strftime("%Y-%m-%d %H:%M:%S")
    row = [now]
    for p in participants:
        row.extend(
            [
                p["nombreAgrupacionPolitica"],
                p["totalVotosValidos"],
                p["porcentajeVotosValidos"],
                p["porcentajeVotosEmitidos"],
            ]
        )
    return row


def append_to_csv(row: list) -> None:
    """Append a row to the CSV file, creating the header if needed."""
    file_exists = os.path.isfile(CSV_FILE)
    write_header = not file_exists or os.path.getsize(CSV_FILE) == 0

    with open(CSV_FILE, mode="a", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        if write_header:
            writer.writerow(HEADERS)
        writer.writerow(row)


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------


def main() -> None:
    """Entry point: fetch, validate, and append results."""
    print("[INFO] Fetching election results from ONPE API...")
    data = fetch_data()

    print("[INFO] Validating response...")
    participants = validate_response(data)

    row = build_row(participants)
    append_to_csv(row)

    print(f"[INFO] Row appended to {CSV_FILE}")
    print(f"       Date : {row[0]}")
    print(f"       {row[1]}: {row[2]} votes ({row[3]}%)")
    print(f"       {row[5]}: {row[6]} votes ({row[7]}%)")


if __name__ == "__main__":
    main()
