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
