# Session Context Log

Running log for the AI5K Profile Intelligence System build. Read the top entry first when picking this project back up — it has the current state and the reasoning behind it, so we don't have to re-derive decisions from scrollback or re-litigate something already settled.

**How this file works:**
- Newest entry at the top.
- Each entry: what changed, why, what's next. Not a transcript — skip sessions that made no real change.
- Update this at the end of every session (see `CLAUDE.md` — it's a standing instruction now, not something to remember manually).
- Revisit it at the start of any session, even a small one, before making changes.

---

## 2026-09-01 — Real Upwork-paste ingestion built; async/sync bug caught and fixed

**What changed:**
- User provided a real sample of Upwork profile text (their own — an automation/n8n/Make.com specialist profile) specifically as a test fixture for the Upwork-paste ingestion field, not as a competitor-benchmark data point (confirmed via clarifying question — the wording was ambiguous at first). Built `app/ingestion/text_segmentation.py` (paragraph segmentation with exact offsets into the original pasted string) and `app/ingestion/upwork_parser.py`, mirroring the CV parser's grounding-by-construction pattern.
- Tier assignment for Upwork paste is deliberately more conservative than the CV parser's: only an actual quoted client testimonial counts as corroborated (T1); everything else — including detailed project narrative with hard metrics — defaults to T8, since Upwork profile prose is unverified self-authored marketing copy with no employer name attached the way a CV entry has. Confirmed this works correctly on the real sample: the one sentence containing `one client wrote, "..."` was correctly tagged T1, all four project-description paragraphs correctly defaulted to T8.
- Wired both CV and Upwork-paste into the actual running page (`app/main.py`), replacing both stub paths. Only GitHub is still stubbed now (`app/stub_data.py` trimmed to just `stub_github_claim`).
- **Caught and fixed a real bug via the browser test, not by reasoning about it in advance**: `/analyze` was declared `async def` but calls blocking sync code (Docling, sync HTTP to Gemini) directly inside it — on FastAPI that runs straight on the single event loop, so it would've stalled every other request once this app has more than one concurrent user. Found it because a real request hung past a 30-second Playwright timeout. Fixed by making the endpoint a plain `def` (Starlette auto-runs sync endpoints in a thread pool) and switching the upload read from `await cv_file.read()` to the sync `cv_file.file.read()`.
- Fixed a stale label on the results page ("Claims used (stub ingestion)") that had gone factually wrong the moment real parsing landed.

**Why:**
- Confirming intent before building saved real rework — the Upwork sample text could plausibly have meant "change the niche" instead, and those are very different amounts of work.
- The async/sync bug is exactly the kind of thing that looks fine on a single manual test (one request, no contention) and only shows up as a hang under real conditions — worth the browser test specifically because it's what surfaced this, not a curl-based check.

**Next steps:**
- Phase A's one remaining item is unchanged: the 30-profile competitor benchmark for the AI/ML engineering freelance niche, still needs the user (niche is locked, awaiting the actual profile data).
- Once that lands: replace `app/stub_data.py`'s `STUB_BENCHMARK` with the real one, build GitHub API pull (last real ingestion source for Phase A/B), and start on the five still-placeholder scoring dimensions.
- Dev server still running on port 8000 in the background.

---

## 2026-09-01 — Phase A: walking skeleton, scoring engine, and real CV parsing all working end to end

**What changed:**
- Built the scoring engine (`app/scoring/`): `dimensions.py` implements the two dimensions Section 2 fully specifies with real formulas (`evidence_quality` — strongest claim per skill, capped at 30 when everything's self-declared; `keyword_coverage` — presence-based, synonym table first per the earlier embedding finding). The other five dimensions (positioning, portfolio_quality, completeness, conversion, pricing_strategy) take caller-supplied placeholder scores until Phase B/C ingestion and generation exist to compute them for real — documented inline so this isn't mistaken for finished work. `gap_ranking.py` implements Section 2's gain/priority formula plus Section 3's three rules (blocking items excluded, dependency gating, balanced top-five). `efficacy.py` holds the starter efficacy/effort lookup as a versioned file, not inline guesses. Proved correct with `app/scoring/smoke_test.py`, including confirming the overall-readiness cap actually clamps a self-declared-only profile from ~44 down to 30 — the exact scenario Section 2 describes.
- Built the walking skeleton (`app/main.py`, FastAPI + Jinja2 templates): a real page at `/` posts to `/analyze` and renders a result page. Hit a real bug doing this — Starlette 1.6.0 (much newer than any version I knew) changed `TemplateResponse`'s signature to take `request` as the first positional arg instead of inside the context dict; fixed by checking the installed version's actual signature via `inspect`, not by guessing from memory.
- Built real CV ingestion (`app/ingestion/`): `file_router.py` classifies files and rejects scanned PDFs loudly (OCR is out of scope) using Docling — verified Docling's actual current API live against a generated test PDF before writing code against it, rather than trusting training-data knowledge of the library (same lesson as the Starlette issue). `cv_parser.py` calls Gemini 3.6 Flash (`app/llm/gemini_client.py`, a thin REST wrapper — deliberately not an SDK, since the package name would be just as likely to have moved as the model names did) to classify which text blocks carry evidence and what skills they support, then builds each `Claim`'s text and source span from our own authoritative block list, never from anything the model wrote — grounding by construction, not just validation after the fact. Tier assignment (`assign_tier`) is a separate deterministic rules pass, flagged in its own docstring as an approximate first cut that needs sanity-checking against real CVs.
- Wired real CV upload into the actual page (file input, not pasted text) and browser-tested the whole path with Playwright against a real generated PDF: upload → Docling → Gemini → real span-grounded claims → scoring engine → rendered result page. Confirmed the math by hand (evidence_quality landed at exactly the value the strongest-per-skill formula predicts).
- GitHub and Upwork-paste ingestion are still stub claims — that's genuinely Phase B scope, not a gap in this pass.

**Why:**
- The user's team is one person now (see the entry below) with "no stones unturned" as the explicit instruction — so where a Section 2 formula is fully specified, it got built for real in Phase A rather than stubbed, instead of waiting for Phase B.
- Two live-API-verification lessons repeated themselves today (Starlette's TemplateResponse signature, Docling's actual document/text-block API) — worth calling out because it's now a pattern, not a one-off: don't write integration code against a fast-moving library from memory, check its real current shape first, same as the earlier Gemini model-name lesson.

**Next steps:**
- Phase A's one remaining item is the 30-profile benchmark read-through, and it's blocked on the user: needs (a) a niche picked, and (b) real Upwork profile text, since the plan explicitly forbids scraping platforms on the user's behalf (PROJECT_PLAN.md line 104) — asked the user directly, awaiting an answer.
- Once the benchmark file exists for a real niche, Phase B can start: GitHub API pull, Upwork-paste parsing, wiring the benchmark's real `required_terms`/`dimension_targets` in place of `app/stub_data.py`, and building formulas for the five still-placeholder dimensions.
- The dev server is left running in the background on port 8000 if the user wants to try the page themselves.

---

## 2026-09-01 — Solo pivot, schemas locked, model decision corrected via live testing

**What changed:**
- Reviewed `PROJECT_PLAN.md` and picked a model stack: Gemini free tier for extraction/generation, local `sentence-transformers` for embeddings (avoids spending API budget on similarity checks).
- Set up `.env` with a real Gemini API key, added `.gitignore` (`.env`, `.venv/`) before any git history exists, so the key is never at risk of being pushed.
- **Corrected the model choice by testing the live key instead of trusting docs/blogs**: `gemini-2.5-flash` 404s for new API keys ("no longer available to new users"). Confirmed `gemini-3.6-flash` works. Plan updated everywhere it named a model.
- Installed `sentence-transformers` (Python 3.12 venv — not 3.14, for library compatibility) and load-tested the plan's own worked example ("Pinecone" should match "vector database"). **It failed** — both `all-MiniLM-L6-v2` and `BAAI/bge-small-en-v1.5` gave near-zero or backwards similarity margins. General embeddings don't reliably encode product→category world-knowledge at this scale; bigger models only help marginally. Fixed the plan: known tool/product terms are matched via a small hand-curated synonym table (built alongside the benchmark file), with embeddings as fallback only for genuinely free-text matches.
- **The rest of the team quit — this is now a solo project.** Rewrote Section 5 of `PROJECT_PLAN.md`: no more 4-person roles or 3-day deadline. Workstreams still exist (ingestion / benchmark / scoring / platform) but run sequentially, paced by the person, not the calendar. Reframed risk table in Section 6 to match — the new top risk is scope creep now that deadline pressure isn't providing a natural brake, not missed handoffs.
- Wrote the three schema files as real Pydantic code (`schemas/claim.py`, `schemas/benchmark.py`, `schemas/result.py`, `schemas/__init__.py`), matching the shapes sketched in Section 5. Notable design choices baked in structurally rather than left as convention: `Claim.weight` is a computed field derived from `tier` (can't drift out of sync with the Section 2 tier table), `Result` refuses to construct unless all seven scoring dimensions are present, `RequiredTerm` carries a `synonyms` list per the finding above. Proved all three work against fake data with `schemas/smoke_test.py`, including a deliberate failure case to confirm validation actually rejects bad input, not just accepts good input.
- Created this file and `CLAUDE.md`.

**Why:**
- Plan called the schema-lock step the entire critical path — worth getting right before any other code exists, since everything else builds against these shapes.
- Live-testing beats cached knowledge for anything API/model-related right now — the field is moving fast enough that even recent web search results contradicted each other and Google's own docs.
- Solo execution needed the plan's own language rewritten, not just tolerated — a plan still describing four people and a countdown clock would actively mislead future-me about what's actually happening.

**Next steps:**
- Read `schemas/result.py` once more against Section 2/5 of `PROJECT_PLAN.md` to sanity check field choices before building on top of it (asked for, not yet confirmed done).
- Start Phase A (see `PROJECT_PLAN.md` Section 5): walking skeleton — a stub API + page that runs the whole path on fake data — plus CV parsing and the 30-profile hand-read benchmark notes for the chosen niche.
- Niche hasn't been picked yet in writing anywhere — needs to happen before the benchmark read-through can start.
