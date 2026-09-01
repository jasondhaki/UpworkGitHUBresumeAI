"""Picks the active LLM backend by env var so ingestion/generation modules don't
need to know which one is live. Default stays Gemini -- see CLAUDE.md's Gemini
call discipline for why the real API is still the one-deliberate-pass-per-phase
target; LLM_PROVIDER=ollama is for rate-limit-free local iteration in between.
"""

import os

if os.environ.get("LLM_PROVIDER", "gemini").lower() == "ollama":
    from app.llm.ollama_client import generate_json
else:
    from app.llm.gemini_client import generate_json

__all__ = ["generate_json"]
