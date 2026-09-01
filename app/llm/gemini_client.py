"""Thin REST wrapper around the Gemini API — deliberately not the official SDK.

Raw HTTP against the endpoint we already verified live (see CONTEXT.md,
2026-09-01: gemini-2.5-flash 404s for new keys, gemini-3.6-flash works) avoids
betting on a Python SDK package name/API that's just as likely to have moved
as the model names did. If this gets replaced with an SDK later, verify its
current API against a real call first — don't assume from training data.
"""

import json
import os

import httpx
from dotenv import load_dotenv

load_dotenv()

MODEL = "gemini-3.6-flash"
BASE_URL = f"https://generativelanguage.googleapis.com/v1beta/models/{MODEL}:generateContent"


def generate_json(prompt: str, response_schema: dict, timeout: float = 60.0) -> dict:
    api_key = os.environ["GEMINI_API_KEY"]
    payload = {
        "contents": [{"parts": [{"text": prompt}]}],
        "generationConfig": {
            "responseMimeType": "application/json",
            "responseSchema": response_schema,
        },
    }
    resp = httpx.post(BASE_URL, params={"key": api_key}, json=payload, timeout=timeout)
    resp.raise_for_status()
    data = resp.json()
    text = data["candidates"][0]["content"]["parts"][0]["text"]
    return json.loads(text)
