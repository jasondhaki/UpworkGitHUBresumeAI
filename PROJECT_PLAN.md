# AI5K Profile Intelligence System — Project Plan

*How the system collects a freelancer's evidence, measures it against the top tier, and rebuilds their profile toward $5,000 a month.*

Consolidated from the system specification (Phase 1, July 2026) and the 3-day sprint plan. This is the single source of truth tying product vision to near-term execution.

---

## 1. Overview

The AI5K Profile Intelligence System is an AI analyzer for freelancer profiles (initially Upwork, extensible to Fiverr and others). A freelancer feeds it evidence — a CV, a GitHub username, their existing Upwork profile text, and more — and gets back:

- A **readiness score** (0–100) measuring how their profile stacks up against what actually wins in their niche
- A **ranked list of gaps**, ordered by score points returned per hour of effort
- A **rewritten title and overview** where every claim and number can be traced back to exactly where it came from

**The rule the whole system rests on:** every claim on a generated profile points to a specific source — a sentence, a commit, a line of an invoice. A claim with no source span is never published; it becomes a coaching prompt instead. This is what separates the system from keyword-matching tools that inflate profiles with unverifiable achievements — inflation that survives right up until the first client conversation, then destroys the private feedback score that controls everything else on the platform.

---

## 2. Core concepts

### The claim record

The unit of storage is a **claim**, not a profile field. Everything downstream — scoring, ranking, generation — reads from these.

```
claim { text, skill_ids[], source_type, source_span,
        tier, weight, observed_date, publishable }
```

Two consequences for the build: original source files are retained (not just extracted text), because grounding means re-reading the source at generation time; and every claim carries a date, so older evidence is discounted relative to recent evidence.

### Evidence tiers

Every claim is assigned a tier by how well it's corroborated. The tier sets its weight in scoring and whether it's allowed to appear on a public profile. A skill takes its **strongest** evidence, never the sum of weak evidence.

| Tier | Definition | Weight |
|---|---|---|
| T1 | Client-verified outcome, named in a review or testimonial | 1.00 |
| T2 | Project demonstrated: deployed repository, live application, published model | 0.85 |
| T3 | Platform-assessed: our own structured skills assessment | 0.80 |
| T4 | Certification, proctored and verifiable with the issuer | 0.75 |
| T5 | Certification, badge-only or self-paced course | 0.55 |
| T6 | Employer-confirmed: work history where the skill was used | 0.50 |
| T7 | Peer-endorsed: recommendation from a colleague | 0.30 |
| T8 | Self-declared, with no corroboration | 0.15 |

Certifications are deliberately split across two tiers (T4/T5) because a proctored certification and a self-paced badge are not comparable evidence. Shipped work (T2) outranks certification (T4) because a repository with months of commit history is materially harder to fabricate than a certificate, and it demonstrates the actual thing an AI buyer is paying for.

### The evidence cap

A profile with no proof cannot score well, by design. When every claim is self-declared, the evidence dimension is capped at 3/10 and the **overall readiness score is capped at 30**. Without this second cap, a user could reach the 70s on positioning, keywords, and completeness while proving nothing — exactly the inflated profile the system exists to prevent.

This produces a low first-time score for most early-career users, so the UI never leads with a bare number. It leads with position and a route out of it ("you have 11 claims and can prove 2 — here are the fastest ways to prove 3 more this week"). The arithmetic is unchanged; the framing isn't punitive.

### Scoring dimensions

Seven weighted dimensions produce the Profile Readiness Score (0–100). Positioning and evidence quality together account for 44% of the total.

| Dimension | What it measures | Weight |
|---|---|---|
| Positioning | Role, vertical, and outcome stated specifically enough to be found and believed | 22% |
| Evidence quality | Sum of tier weights across claimed skills, subject to the cap | 22% |
| Keyword coverage | Required terms present, plus semantic coverage of benchmark topics | 15% |
| Portfolio quality | Item count, quantified results, working links | 15% |
| Completeness | Checklist of essential profile elements | 10% |
| Conversion | Whether the opening addresses the buyer's problem rather than describing the seller | 8% |
| Pricing strategy | Whether the stated rate is defensible given the evidence tier | 8% |

Keyword coverage is scored on **presence, not frequency** — a term present once scores the same as one present nine times, so there's no way to game the score by repeating yourself. It's also matched by meaning, not string (e.g. "Pinecone" counts as "vector database"), because frequency-based similarity rewards stuffing and doesn't correlate with actual hire rates.

> **Implementation note (2026-09-01):** tested this exact "Pinecone" → "vector database" match against local `sentence-transformers` (`all-MiniLM-L6-v2` and `BAAI/bge-small-en-v1.5`) before building on it. Both failed to reliably separate it from the wrong pairing ("Pinecone" vs "relational database") — cosine similarity margins were near-zero or backwards regardless of phrasing. General-purpose embeddings don't reliably encode product→category world-knowledge ("Pinecone is a vector database") at this model scale; it's not a model-choice problem, bigger models only help marginally. **For the sprint, keyword matching for known tools/products uses a small hand-curated synonym table** (per required term, list known product names/aliases) built by M2 alongside the benchmark file, checked before any embedding fallback. Embeddings stay in the stack for genuinely free-text semantic matches where no fixed alias list is possible, but they are not the primary mechanism for the tool-name case the spec calls out.

Skill gaps the top tier holds that the user lacks are **reported, not scored** — it's a learning signal ("go build this next"), not a profile-writing fix, and penalizing someone for a skill they haven't acquired yet would be both unfair and useless.

---

## 3. System architecture

Six components. Ingestion and the benchmark feed scoring; scoring drives everything downstream.

```
1 INGESTION          Nine sources into one schema
2 BENCHMARK          What good looks like, per niche
3 EVIDENCE TIERS     How verified is each claim
4 SCORING & GAPS     Seven weighted dimensions
5 GENERATION         Titles, overviews, case studies
6 PRESENCE           Posts, calendar, external proof
```

### Ingestion — nine sources, one output shape

| Source | How it arrives | Yields |
|---|---|---|
| Onboarding form | Structured answers: target vertical, target earnings, hours available, biggest struggle | Context and goals |
| CV / resume | PDF or DOCX upload, layout-aware parse | Work history, skills |
| Portfolio site | User supplies URL, full crawl of their own asset | Projects |
| LinkedIn | Native ZIP export the user downloads and uploads | History, recommendations |
| Upwork / Fiverr | User selects and pastes their own profile text | Reviews naming outcomes |
| GitHub / GitLab | API pull: languages, topics, stars, commit recency | Strongest technical proof |
| Hugging Face | API pull: published models/datasets, download counts | Adoption signal |
| Demo videos | User supplies URLs, transcript extracted, tools/metrics pulled | Demonstration |
| Articles / threads | Crawled from URLs the user provides | Thought leadership |

**No scraper is ever used against a platform on the user's behalf.** The LinkedIn export and Upwork text-paste sources deliver high-value data with zero ToS exposure because the user performs the retrieval themselves and the system only parses what's handed over.

Files are classified before parsing (deterministic, no model involved) so expensive parsers only see documents that need them. A mandatory pre-parse check samples a PDF's extracted text — if it comes back empty or noisy, the file is a scan wearing a PDF extension and routes to OCR; skipping this check fills profiles with silent garbage.

Extraction runs as several small, specialized parallel calls (identity / work history / skills-and-proof) rather than one large prompt, since splitting improves accuracy and reduces latency. Every extracted field is nullable — forcing a required field when data doesn't exist is the most reliable way to make a model invent one. The model returns **indices into the source text**, and post-processing re-extracts the exact original block from those indices — this is what makes span grounding real rather than aspirational.

### Benchmark engine — two tracks, two speeds

| Track | Cadence | Does |
|---|---|---|
| Anchor | Monthly | Pulls top-performing profiles per niche, extracts structural patterns (title formula, overview length, portfolio counts, recurring terms, rate bands), then **discards the source profiles** — only aggregate patterns are kept |
| Radar | Daily | Watches for rising/fading terms, filters them, routes to a human before anything is added. Produces **tags only** — never alters scoring weights |

The anchor track's output is versioned by month and immutable once written, so a score computed in a given month can always be explained by that month's benchmark. Target: 100 profiles per niche for stable percentile statistics (accumulated over several refresh cycles). The radar track matters as much for catching *decline* as emergence — a profile in last year's vocabulary reads as stale, and nothing else in the system would detect that.

### Gap ranking

Each gap is ranked by score points returned per hour of effort:

```
gain     = weight × (benchmark_target − current) × efficacy
priority = gain / max(effort_hours, 0.5)
```

- `benchmark_target` is what the top tier actually reaches in that niche — not a perfect 100
- `efficacy` (expected share of the gap a fix actually closes) comes from a versioned lookup table, refined over time from outcome data — never re-guessed per run
- `effort_hours` is floored at 0.5 so trivial fixes can't dominate the ranking

Three rules on top of the raw ranking:

1. **Blocking items leave the ranking entirely.** Unproven claims, ToS risks, missing identity verification are liabilities, not optimization opportunities — they go in a separate fix-before-publishing list regardless of their return on effort.
2. **Dependencies gate what's shown.** A gap stays hidden until its prerequisites clear (no title rewrite before a vertical is chosen; no pricing advice before evidence exists to justify a rate).
3. **The top five stays balanced**, not pure ROI-sorted: top 3 by priority + the single largest available gain regardless of effort + anything blocking. Otherwise the list fills permanently with five-minute fixes and the user is never told to build the portfolio piece that actually moves their earnings.

### Content generation

Every generated asset is bounded by the evidence store; a validator re-reads the source span before any claim is allowed through.

| Asset | Structure | Hard constraint |
|---|---|---|
| Title | Role, vertical, measurable outcome | Every number traced to a stored source span |
| Overview | Hook on buyer's problem → proof → process → call to action | Proof section drawn only from T1–T4 claims |
| Case study | Problem, approach, result, evidence tier | Tier shown to the user, not hidden |
| Proposal draft | Job description matched to strongest relevant evidence | Draft only — never auto-submitted |

The constraint is enforced **structurally**, not by instruction: a number that can't be traced to a span never reaches the draft, so there's no opportunity for a plausible-sounding fabrication to survive review.

### Presence engine

Since enterprise buyers check a public footprint before hiring, an empty external presence is itself a gap. Generates drafts for LinkedIn/X/long-form publishing from the radar track and the user's own evidence, presents them for review, and syncs approved posts to a calendar. **Nothing is auto-posted** — the user reviews and publishes. Ships after the core loop works, since it depends on the radar track, evidence store, and generation layer all being in place.

---

## 4. Build order — the phased roadmap

The full system is not built in one pass. The first stage needs almost no engineering and decides whether the rest is worth building at all.

| Stage | Goal | Contents |
|---|---|---|
| **1. Prove the report lands** | Answer: does the gap report tell a working freelancer something they didn't already know, and do they act on it? | 3–4 sources handled by hand, benchmark read manually, gap reports semi-manually assembled for a small group of real freelancers. **This is the 3-day sprint — see Section 5.** |
| **2. Build the pipeline** | Automate what Stage 1 proved works | Router, parsing, schema extraction, evidence tiers, seven dimensions, gap ranking |
| **3. Widen the intake** | Add remaining sources | Portfolio crawl, LinkedIn export, video transcripts, published models, articles; benchmark refresh automated |
| **4. Once the core works** | Add the layers that depend on a working core | Presence engine, calendar sync, radar track, weight refit once outcome data justifies it |

Parsing is commodity work that keeps getting cheaper. The benchmark and the evidence model are the parts that are genuinely proprietary, and both can be validated by hand before any pipeline exists. **If the hand-assembled reports don't land with real users, no amount of parsing infrastructure will rescue the product** — so Stage 1 is gated on human judgment, not engineering completion.

---

## 5. Phase 1 execution plan: solo build

**Revised 2026-09-01 — solo, no fixed deadline.** Originally scoped for four people over a 3-day sprint (M1 ingestion, M2 benchmark/evidence, M3 scoring/generation, M4 platform/integration, working in parallel). The rest of the team is no longer on the project — it's one person, building sequentially, with no calendar deadline. The four workstreams below still exist and still matter as a way to keep concerns separate, but there's no one to hand off to and no clock forcing the order. The explicit call was: build it properly, integrate everything, don't rush — deadlines are being handled separately.

**One thing this doesn't mean: unlimited scope.** "No stones unturned" means *build every in-scope piece correctly and completely*, not *keep adding pieces*. The scope fence below still exists precisely because open-ended time is what lets a demo project quietly grow into a rebuild of the full spec. Treat it as a discipline tool, not a constraint you've outgrown now that the deadline pressure is off.

Goal, unchanged: a working vertical slice through the whole system, on one niche, tested on real people. *A freelancer uploads a CV, gives a GitHub username, and pastes their existing Upwork profile text. They get back a readiness score, a ranked list of gaps, and a rewritten title/overview where every number is traceable. That is the whole target — everything else in the spec is deliberately out of scope for this phase.*

### Workstreams (now sequential, one person)

| Stream | Area | Ships |
|---|---|---|
| Ingestion | Sourcing | File router, CV parsing, GitHub pull, Upwork text paste — everything that turns raw input into claim records |
| Benchmark & evidence | Grounding | Hand-built benchmark for one niche, required-terms list (+ synonym table, see §2), tier-assignment rules |
| Scoring & generation | Core logic | Seven dimensions, both caps, gap ranking with blocking/dependency rules, title and overview generation, span validation |
| Platform & integration | Wiring | Storage, API, results page — and continuous integration as each piece lands, since solo the risk isn't a missed handoff, it's building each piece in isolation and never actually running them together until the end |

### The critical path is still the schema

Before writing any other code, **write the three record shapes as actual files**:

- **Claim record** — a single piece of evidence: source span, tier, weight, date
- **Profile record** — how claims aggregate into skills, what the scorer reads
- **Benchmark record** — required terms, per-dimension targets, rate bands for the chosen niche

Build everything else against these, using fake data until the real thing lands. Solo, there's no one to catch schema drift for you — so treat any change to a locked schema as a deliberate, logged decision (a comment or commit message saying why), not a quick edit made mid-flow in a different file. Silent schema drift is still the single most expensive mistake available here, team or no team.

```
claim      { text, skill_ids[], source_type, source_span,
             tier, weight, observed_date, publishable }
benchmark  { niche, required_terms[], title_formula,
             overview_words, portfolio_min, rate_band,
             dimension_targets{} }
result     { readiness, capped, dimensions{}, blocking[],
             gaps[{dimension, current, target, gain,
             effort_hours, priority}], generated{} }
```

### Scope fence

| In scope | Out of scope (for this phase) |
|---|---|
| One niche only | Accounts and login (hardcode one user) |
| CV upload, GitHub, Upwork paste | OCR — native PDFs only, reject scans loudly |
| Hand-built benchmark, thirty profiles | LinkedIn, portfolio, video, articles |
| Eight evidence tiers, rules-based | Automated benchmark scraping |
| Seven dimensions with both caps | Skill taxonomy mapping (beyond the small synonym table in §2) |
| Gap ranking with blocking rules | Deduplication and entity resolution |
| Title and overview generation | Weight refit, presence engine |
| One page that shows the result | Proposal drafts, multiple niches |
| | Any visual polish at all |

The out-of-scope list is still a **commitment**, not a wish list. If a piece is finished, the next move is running more real profiles through it or hardening it — not starting an out-of-scope item.

Two specific traps to avoid: CV parsing is a rabbit hole (support a handful of common layouts, fail loudly on the rest with a clear message — don't chase a two-column PDF with a photo in it); and manual benchmark reading always takes longer than estimated (cap at 30 profiles — 20 with honest notes beats 30 rushed).

### Build order

The order below preserves the original "walking skeleton first" logic — get something running end to end on fake data immediately, so every later piece replaces a fake one instead of being built in a vacuum. Nothing here is a day; work through it at whatever pace is sustainable.

**Phase A — skeleton and schema.**

| Task | Done when |
|---|---|
| Lock the claim/profile/benchmark schemas, write as files | Three schema files committed |
| Walking skeleton: API, page, stub endpoints returning fake data | The whole path runs from a browser, nothing real in it yet |
| Read 30 top profiles in the niche, pull out patterns by hand | Notes on title shapes, overview length, recurring terms, rate bands |
| Seven dimension formulas, running against fake claims | Fake input produces a plausible score breakdown |
| File router, then CV parsing into claim records | A real CV produces real claim records |

**Phase B — one real person, all the way through.**

| Task | Done when |
|---|---|
| GitHub API pull, then Upwork profile text-paste parsing | Three sources all produce claim records in the agreed shape |
| Benchmark written as a file, required terms + synonym table, tier rules implemented | Any claim can be assigned a tier automatically |
| Caps applied, gap ranking with blocking/dependency rules, then generation | A score object + a ranked gap list + a title and overview |
| Real storage, real API, replace stubs as pieces land | Fake data is gone from the main path |

**This is the real checkpoint**, deadline or not: your own CV and GitHub should go in and produce a score, a ranked gap list, and a rewritten title. If it's not working here, don't move on to polish — find out why first.

**Phase C — real profiles, hardened.**

| Task | Done when |
|---|---|
| Fix whatever breaks on real inputs | Five different CVs parse without crashing |
| Check the benchmark against real profiles, adjust required terms | Scores look sane to someone who knows the niche |
| Span validation on every generated claim, then fixes | No generated number exists without a traceable source |
| Integration pass, display, then a walkthrough of the whole thing | The page shows everything a demo would need |

### Phase output contracts

Even solo, define what each phase must produce before starting the next — it's what keeps "build it properly" from turning into an unstructured rewrite loop.

| Phase | Produces | Consumed by |
|---|---|---|
| A | A running skeleton with stub endpoints | Every later phase — nothing is blocked waiting on a real piece |
| A/B | A list of claim records in the agreed shape (empty list is fine; wrong shape is not) | Scoring |
| A/B | A benchmark file: required terms, synonym table, per-dimension targets, rate bands | Scoring |
| B | A score object, a ranked gap list with blocking items separated out, generated title/overview with source spans attached | Platform/display |

### Checkpoints and fallbacks

Without a deadline these are less about triage and more about noticing when a piece is fighting you harder than it should:

| Checkpoint | If it's taking far longer than expected, cut this |
|---|---|
| Schema locked | Nothing — stay on it. Everything downstream is worse if this is wrong. |
| Skeleton running | Drop the Upwork paste source temporarily. Two sources are enough to keep moving. |
| Real profile through end to end | Set generation aside. A score and a ranked gap list still proves the concept — come back to generation once that's solid. |
| Integration feels shaky | Get one profile fully clean and demo-ready before spreading effort across five. |

### Definition of done

Phase 1 succeeds when all of the following are true:

- Five real freelancer profiles have been through the system end to end
- Each produced a readiness score with the cap applied correctly when evidence was thin
- Each produced a ranked gap list with blocking items shown separately from ranked ones
- Each produced a rewritten title and overview, every number traceable to a source span on request
- **At least one person outside the project looked at their own report and said something they didn't already know**

The last item is the real test. The first four are engineering; the fifth is whether the product is worth building. A working pipeline producing reports nobody finds useful isn't actually done, even if every component works.

> **One line for the solo build:** lock the schema before anything else, get a working skeleton end to end before perfecting any one piece, and let "no stones unturned" apply to finishing the in-scope list correctly — not to growing it.

---

## 6. Risks and open decisions

### What will probably go wrong

| Risk | Why it happens | Mitigation |
|---|---|---|
| Schema changes mid-build | A field turns out to be needed that wasn't planned for | Add a field, never rename or remove one — additions don't break code you already wrote against the old shape |
| CV parsing eats far more time than planned | Real CVs are far messier than test CVs | Fix the format list early; reject the rest with a clear message rather than chasing every layout |
| Benchmark takes longer than planned | Reading 30 profiles carefully is slow work | Cap at 30. Short on time? 20 with honest notes beats 30 rushed |
| Everything only comes together at the very end | Each piece got built and tested in isolation | The walking skeleton exists precisely to prevent this — wire each piece in and run it end to end as soon as it lands, don't stockpile finished pieces |
| Generated text says things the evidence doesn't support | The span check was left until last | Build the validator with the generator, not after — it's the whole point of the product |
| Open-ended time quietly becomes scope creep | No deadline pressure removes the natural brake on adding "just one more thing" | The scope fence is the brake now — before starting anything new, check it's actually on the in-scope list |

### Open product decisions (unresolved, need a call before Stage 2+)

| Decision | The tension |
|---|---|
| Show benchmark numbers, or only the gaps | Showing them is more persuasive but invites gaming |
| How hard to flag unproven claims | Too gentle and profiles stay inflated; too harsh and the first interaction feels like an accusation |
| Does identity verification gate generation, or only paid activation | Moves conversion significantly either way |
| How long original files are retained | Span grounding needs them, storage costs money, privacy law prefers deletion — a fixed window is likely the answer |
| Whether skill-gap reporting suggests specific learning resources | Useful, but turns a diagnostic product into a curriculum product |

**The line that governs every other decision:** if a claim cannot be traced to a source, it does not appear on the profile. Everything else in this plan exists to make that rule practical at scale.

---

## 7. Tool stack (reference)

| Job | Primary | Alternative |
|---|---|---|
| Onboarding form | Hosted form with webhook to the database | Form built into the application |
| Document parsing | Docling | LlamaParse, Unstructured |
| Scanned documents | Tesseract, managed OCR on failure | PaddleOCR for non-Latin scripts |
| Schema enforcement | Pydantic with a validating wrapper | Constrained decoding at higher volume |
| Field extraction | **Gemini 3.6 Flash (free tier), JSON schema mode, small fast model per field group, parallel** | One larger model if latency allows |
| Site and article crawl | Firecrawl | Jina Reader for single pages |
| LinkedIn | Native ZIP export parsed with pandas | None — no scrapers here |
| Marketplace benchmark | Scheduled scraper actors, monthly | Managed data vendor |
| Code evidence | GitHub REST/GraphQL, Hugging Face Hub | GitLab API |
| Video transcripts | Transcript API, managed ASR fallback | Self-hosted Whisper |
| Radar sources | Search API plus community sources | Manual review either way |
| Skill normalization | NER model plus taxonomy mapping | Pre-built skills extraction library |
| Deduplication | String similarity, then embedding clustering | Probabilistic record linkage at scale |
| Embeddings | **`sentence-transformers` locally (e.g. `all-MiniLM-L6-v2`)** | Managed embedding API |
| Generation | **Gemini 3.6 Flash (free tier)** | Groq (Llama 3.1/3.3) for redundancy, Stage 2+ |
| Database | PostgreSQL with vector support | Managed Postgres |
| Original files | Object storage, retained for span re-reading | Non-negotiable if grounding is real |

**Model decision (2026-09-01, revised same day after live testing):** Originally planned on Gemini 2.5 Flash. Once the real API key was live, `models.list` and a real `generateContent` call showed the field has moved fast since my training data — **2.5 Flash returns 404 for new API keys** ("no longer available to new users"), and Google's own error message points at `gemini-3.6-flash` as the replacement. Confirmed `gemini-3.6-flash` works end-to-end against our actual key. **Use `gemini-3.6-flash` for both extraction and generation.** Lesson: for a fast-moving API, a live call against the real key beats any cached knowledge or blog post — verify model availability this way at the start of any future stage too, not just once. Embeddings for keyword semantic matching run locally via `sentence-transformers` (e.g. `all-MiniLM-L6-v2`), not through the API — no reason to spend API budget on a similarity check.

---

*Source documents: "Plan Part One.pdf" (sprint plan) and "Plan Part Two.pdf" (system specification, Phase 1, July 2026), both in the project root.*
