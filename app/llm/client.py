"""Picks the active LLM backend by env var so ingestion/generation modules don't
need to know which one is live. Default stays Gemini -- see CLAUDE.md's Gemini
call discipline for why the real API is still the one-deliberate-pass-per-phase
target; LLM_PROVIDER=ollama is for rate-limit-free local iteration in between.
"""

import os

from dotenv import load_dotenv

# Must run here, not just in gemini_client.py -- this is the dispatch point that
# reads LLM_PROVIDER, and whichever backend loses the check never gets imported,
# so its own load_dotenv() call (if it had one) would never run either. Found this
# by observing a live Gemini 429 despite .env correctly setting LLM_PROVIDER=ollama
# -- the env var was never actually loaded before this check ran.
load_dotenv()

if os.environ.get("LLM_PROVIDER", "gemini").lower() == "ollama":
    from app.llm.ollama_client import generate_json
else:
    from app.llm.gemini_client import generate_json

__all__ = ["generate_json"]
