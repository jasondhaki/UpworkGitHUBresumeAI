# AI5K Profile Intelligence System

A demo AI analyzer for freelancer profiles: feed it a CV, a GitHub username, and Upwork profile text, and it returns a readiness score, a ranked list of gaps, and a rewritten title/overview — where every number is traced back to a specific source and nothing unproven ever gets published.

Full spec: [PROJECT_PLAN.md](PROJECT_PLAN.md). Build history and decisions: [CONTEXT.md](CONTEXT.md). What the scoring benchmark is and how it was built: [BENCHMARK.md](BENCHMARK.md).

## Status

Solo demo build, no fixed deadline. Phase A and B are complete; Phase C (real-input hardening) is in progress. See the top entry of [CONTEXT.md](CONTEXT.md) for exactly what's done and what's pending right now.

## Setup

Requires Python 3.12 (not 3.14 — some dependencies here don't have wheels for it yet).

```bash
python -m venv .venv
.venv\Scripts\pip install -r requirements.txt      # Windows
# .venv/bin/pip install -r requirements.txt         # macOS/Linux
```

You'll also need a Gemini API key (free tier — see [ai.google.dev](https://ai.google.dev)). Create a `.env` file in the project root:

```
GEMINI_API_KEY="your-key-here"
```

Optionally, a `GITHUB_TOKEN` in the same file raises GitHub API rate limits from 60/hour to 5000/hour (unauthenticated works fine for occasional use).

### Swapping the LLM backend (local model, Gemini, or a future paid API)

Gemini's free tier rate-limits hard under iterative testing (see `CLAUDE.md`). For local demo/dev sessions where you'd rather not fight that, set:

```
LLM_PROVIDER=ollama
OLLAMA_MODEL=qwen2.5:7b   # optional, this is the default
```

in `.env` and have [Ollama](https://ollama.com) running locally (`ollama pull qwen2.5:7b` once, then `ollama serve` or just let the desktop app run). `qwen2.5:7b` beat `llama3.2:3b` head-to-head on this app's real extraction task — same reliability, but it actually respected the "skip rate/logistics-only blocks" instruction where llama3.2:3b didn't, at roughly the same per-call latency on this machine (16GB RAM, no discrete GPU; no GPU is required either way, just expect slower per-call latency than an unthrottled Gemini call).

For Gemini, the model is also swappable without a code change: `GEMINI_MODEL` in `.env` overrides the default (`gemini-3.6-flash`) — useful once a newer/better Gemini model is worth moving to.

`app/llm/client.py` is the one place that picks the backend, by `LLM_PROVIDER` (`gemini` by default, `ollama` for local) — every ingestion/generation module imports `generate_json` from there, not from a specific provider, so none of them need to know or care which backend is live. This is deliberately the seam for a future paid-tier move (e.g. Anthropic): implement the same `generate_json(prompt, response_schema) -> dict` contract in a new `app/llm/<provider>_client.py`, add one `elif` branch in `client.py`, done — no ingestion/generation code changes, and the default (Gemini today) only changes when someone explicitly sets `LLM_PROVIDER`, so nothing about the current demo path is at risk from adding it.

## Running it

```bash
.venv\Scripts\python -m uvicorn app.main:app --port 8000
```

Then open `http://127.0.0.1:8000/` — upload a CV (native PDF or DOCX, not a scan), optionally add a GitHub username and/or paste Upwork profile text, and submit.

## Running the tests

There's no single test runner — each module has its own `smoke_test.py`, runnable directly and designed to be read, not just executed:

```bash
.venv\Scripts\python -m app.scoring.smoke_test           # no Gemini calls
.venv\Scripts\python -m app.scoring.smoke_test_blocking   # no Gemini calls
.venv\Scripts\python -m app.storage.smoke_test            # no Gemini calls
.venv\Scripts\python -m app.ingestion.smoke_test_github   # no Gemini calls
.venv\Scripts\python -m app.ingestion.smoke_test          # real CV, calls Gemini
.venv\Scripts\python -m app.ingestion.smoke_test_upwork   # real Upwork paste, calls Gemini
.venv\Scripts\python -m app.generation.smoke_test         # grounding logic, no Gemini calls
.venv\Scripts\python -m app.generation.smoke_test_live    # real generation, calls Gemini
```

For the ones that call Gemini: this project deliberately keeps real API calls rare (see `CLAUDE.md`'s API call discipline) — most logic is tested against fake data first, with a real call reserved for verifying something new actually works end to end. Install `requirements-dev.txt` for the browser-based integration test in `scripts/test_walking_skeleton.py`.

## Deployment

Two deployed versions exist, because the two hosts have different constraints:

- **Static preview (marketing pages only):** https://jasondhaki.github.io/UpworkGitHUBresumeAI/ — GitHub Pages, built by `scripts/build_static.py` into `docs/`. No backend: the intake form is replaced with a "run locally" card. Re-run the build script and commit `docs/` after any template/CSS change meant to reach this page.
- **Live app (real analysis):** deployed via Render, using `render.yaml` as a Blueprint. Render was chosen over Vercel because Docling's CV-parsing dependencies (torch + layout models, 1.5–3GB) exceed Vercel's 250MB serverless function cap; Render runs a real container instead. In Render's dashboard: New → Blueprint → select this repo → it reads `render.yaml` and prompts for `GEMINI_API_KEY` (required) and `GITHUB_TOKEN` (optional, raises GitHub API rate limits) as secrets — enter them there, never commit them. Free-tier caveats: the instance sleeps after 15 minutes idle (cold start on wake), has 512MB RAM (Docling's torch dependency is the thing most likely to feel that ceiling), and has no persistent disk, so `data/app.db` and uploaded CVs survive between requests only while the instance stays warm — a redeploy or a sleep/wake cycle resets them.

## Project layout

```
app/
  ingestion/    CV (Docling + Gemini), Upwork-paste (Gemini), GitHub (no Gemini — structured API data)
  scoring/      Seven scoring dimensions, both evidence caps, gap ranking, blocking-item detection
  generation/   Title/overview generation, grounded by construction — a number that can't be
                traced to a real claim never gets published
  storage/      SQLite persistence + uploaded-file storage
  llm/          Thin Gemini REST client (deliberately not the official SDK — see its docstring)
  templates/    The one page, plus a results page and run history
schemas/        The three core record shapes: Claim, Benchmark, Result
benchmarks/     The actual benchmark data for the "ai-engineering-freelance" niche
scripts/        Test fixtures and the browser-based integration test
```

## What's real vs. still a placeholder

Everything in the pipeline runs on real data and real formulas — no stubs remain in the main path. The one thing still evolving: the benchmark's `dimension_targets` (the 0-100 target score per scoring dimension) are reasoned estimates, not directly derived from real profile data; see [BENCHMARK.md](BENCHMARK.md)'s Confidence Level section for exactly which parts of the benchmark are solid and which aren't yet.
