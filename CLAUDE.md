# Project instructions

Solo demo project: AI5K Profile Intelligence System. Free-tier-only stack (no production infra). See `PROJECT_PLAN.md` for the full spec and `CONTEXT.md` for what's actually been done and why.

## Session context log — read this first, update it last

- **At the start of a session**, read `CONTEXT.md` (top entry = most recent) before making changes. It has the current state and the reasoning behind recent decisions — don't re-derive or re-litigate what's already settled there. **Check for a `PENDING` line right below the "How this file works" header** — if one exists, that's unfinished work from a prior session (usually something blocked on an external condition like a rate limit) that should be picked up now if the blocker has cleared, without waiting to be asked. Clear the line once it's resolved.
- **At the end of a session that made real changes** (files edited, decisions made, findings discovered — not just Q&A), add a new entry at the top of `CONTEXT.md` with:
  - **What changed** — concrete: files touched, decisions made, findings discovered
  - **Why** — the reasoning, especially anything non-obvious or that reversed an earlier assumption
  - **Next steps** — what's queued up for next time
- Skip the update if nothing actually changed this session.
- Periodically (the user will prompt for this, or do it proactively if the log is getting long) re-read the whole file and consider trimming or consolidating old entries once they stop being load-bearing for current decisions — this is a working log, not a permanent archive.

## Gemini API call discipline

Free-tier rate limits get eaten fast by iterative testing (hit this repeatedly on 2026-09-01 — see CONTEXT.md). Default behavior:

- **While building or debugging**, don't call the real Gemini API to check whether code runs. Use fake/synthetic data instead — construct `Claim`/`Benchmark`/`Result` objects directly (see the existing `*/smoke_test*.py` files for the pattern) to test schemas, scoring math, routing, template rendering, etc. Almost everything in this codebase *except* `app/llm/gemini_client.py` itself and the two parsers that call it doesn't need a live call to verify.
- **Make a real call when**: verifying a new or changed prompt/extraction schema for the first time, doing one deliberate end-to-end pass at the end of a phase or a meaningful chunk of work, or the user explicitly asks to run something real through the system.
- **Batch it**: when a real call is needed, cover everything that changed in one deliberate test, not one call per small tweak. Treat each call as worth spending, not free to retry casually.
- **This is a floor, not a ceiling**: at least one real end-to-end call before calling a phase done — several real bugs this session (an async/sync threading bug, a Docling API mismatch, a model-name 404, the 503 rate-limit pattern itself) only ever showed up under a live call, never from reading the code. Cutting real calls to zero would trade a rate-limit annoyance for shipping untested integration points.
