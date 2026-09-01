"""Thin REST wrapper around the Gemini API — deliberately not the official SDK.

Raw HTTP against the endpoint we already verified live (see CONTEXT.md,
2026-09-01: gemini-2.5-flash 404s for new keys, gemini-3.6-flash works) avoids
betting on a Python SDK package name/API that's just as likely to have moved
as the model names did. If this gets replaced with an SDK later, verify its
current API against a real call first — don't assume from training data.

Retries on 503 ("high demand" — seen repeatedly during this build, including
during initial setup) and other 5xx/429 responses, since those are Google-side
transient overload, not something a caller can fix by changing the request.
"""

import json
import os
import time

import httpx
from dotenv import load_dotenv

load_dotenv()

MODEL = "gemini-3.6-flash"
BASE_URL = f"https://generativelanguage.googleapis.com/v1beta/models/{MODEL}:generateContent"

RETRYABLE_STATUS_CODES = {429, 500, 502, 503, 504}
MAX_ATTEMPTS = 3
BACKOFF_SECONDS = (2, 5)  # wait before attempt 2, then before attempt 3


def generate_json(prompt: str, response_schema: dict, timeout: float = 90.0) -> dict:
    api_key = os.environ["GEMINI_API_KEY"]
    payload = {
        "contents": [{"parts": [{"text": prompt}]}],
        "generationConfig": {
            "responseMimeType": "application/json",
            "responseSchema": response_schema,
        },
    }

    last_error: Exception | None = None
    for attempt in range(MAX_ATTEMPTS):
        if attempt > 0:
            time.sleep(BACKOFF_SECONDS[attempt - 1])
        try:
            resp = httpx.post(BASE_URL, params={"key": api_key}, json=payload, timeout=timeout)
            if resp.status_code in RETRYABLE_STATUS_CODES:
                last_error = httpx.HTTPStatusError(
                    f"{resp.status_code} from Gemini (attempt {attempt + 1}/{MAX_ATTEMPTS})",
                    request=resp.request,
                    response=resp,
                )
                continue
            resp.raise_for_status()
            data = resp.json()
            text = data["candidates"][0]["content"]["parts"][0]["text"]
            return json.loads(text)
        except httpx.TimeoutException as e:
            last_error = e
            continue

    raise last_error
