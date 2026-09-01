"""Local Ollama client -- same generate_json(prompt, response_schema) contract as
gemini_client.py, so it's a drop-in swap behind app/llm/client.py. Picked for
iterative demo-building on 2026-09-02 after Gemini's free-tier rate limits made
every extraction test an unpredictable wait -- local inference has no rate limit,
just a slower, predictable one (CPU-only on this machine, no discrete GPU).

Uses Ollama's native structured-output mode (`format: <json schema>`), which
constrains decoding to valid JSON matching the schema -- the same job Gemini's
responseSchema does. The schemas defined in the ingestion/generation modules are
plain JSON Schema already, so they're reused unchanged, not duplicated.
"""

import json
import os

import httpx

OLLAMA_BASE_URL = os.environ.get("OLLAMA_BASE_URL", "http://127.0.0.1:11434")
# qwen2.5:7b over llama3.2:3b -- empirically compared on this app's actual extraction
# task (see CONTEXT.md, 2026-09-02): same reliability, qwen followed the "skip
# rate/logistics-only blocks" instruction correctly where llama3.2:3b didn't, and
# per-call latency was roughly a wash on this machine (16GB RAM, no discrete GPU).
MODEL = os.environ.get("OLLAMA_MODEL", "qwen2.5:7b")


def generate_json(prompt: str, response_schema: dict, timeout: float = 300.0) -> dict:
    payload = {
        "model": MODEL,
        "messages": [{"role": "user", "content": prompt}],
        "stream": False,
        "format": response_schema,
        # Greedy decoding, not the ~0.8 sampling default -- found empirically that at
        # default temperature this small a model would sometimes decide, non-
        # deterministically, that NONE of a batch of obviously-evidence-bearing blocks
        # qualified (same prompt, same schema, 0 claims one run and 5 the next).
        # Structured extraction wants the model's single best judgment, not variety.
        "options": {"temperature": 0},
    }
    resp = httpx.post(f"{OLLAMA_BASE_URL}/api/chat", json=payload, timeout=timeout)
    resp.raise_for_status()
    data = resp.json()
    return json.loads(data["message"]["content"])
