# Benchmark: AI/ML Engineering Freelance

*What "good" looks like for the niche this system currently scores against. Last updated 2026-09-02.*

**Status: real data.** This benchmark is built from a hand-read of 30 real, currently-active Top Rated / Top Rated Plus Upwork profiles (~10 each across AI Engineer, Machine Learning Engineer, and LLM Engineer searches), collected manually — never scraped; see [Methodology](#methodology). This replaces the earlier version, which was built from general market research rather than actual profiles. Required skills, rate band, portfolio expectations, and title structure are all now computed directly from real data. One field — the internal scoring-dimension targets — still can't be derived this way; see [Confidence level](#confidence-level).

---

## Methodology

30 profiles, manually collected by the user browsing Upwork directly and copying public profile fields (title, rate, overview, skills tags, portfolio, work-history stats) — the same way anyone researching competitors would. Nothing was scraped or automated: the plan this project follows explicitly rules out pulling Upwork data programmatically, even by an assistant, and this step was always designed to need a human. Raw profile data (which includes real individuals' names and identifying details) is **not in this repository** — it's kept in a local, gitignored file and never committed or published, matching the project's own stated principle for benchmark data: extract the aggregate patterns, discard the source profiles. Only the derived numbers and patterns below are public.

## Required skills / terms

Computed directly from real profile skill-tag frequency across the 30 profiles (exact counts shown). This is a genuine correction from the earlier version, which was built from job-posting demand data — what employers ask for isn't identical to what winning freelancers actually tag themselves with.

| Term | Real frequency (of 30) | Notable change from the earlier version |
|---|---|---|
| Python | 25 | confirmed |
| Machine Learning | 24 | **new** — wasn't in the required list at all before, despite being this common |
| Artificial Intelligence | 22 | **new** |
| AI agent development | 19 | elevated — more dominant as a literal self-tag than job-market research suggested |
| Deep learning | 17 | **new** |
| RAG | 15 | confirmed |
| Agent framework (LangChain, LangGraph, LlamaIndex, AutoGen, CrewAI) | 14 | confirmed |
| LLM API integration (OpenAI/Anthropic/Gemini API) | 13 | confirmed |
| NLP | 13 | confirmed |
| Prompt engineering | 12 | confirmed |
| LLM / large language model | 10 | confirmed |
| Chatbot development / AI chatbot | 9 + 10 | **new** |
| AI app development | 9 | **new** |
| Generative AI | 9 | confirmed |
| Computer vision | 9 | **new** — meaningful cluster among ML Engineer profiles specifically |
| Claude | 8 | **new** — notable as its own named skill, not just folded into "LLM API" |
| Vector database | 7 | confirmed |
| Deep learning framework (PyTorch/TensorFlow) | 8 + 7 | confirmed |
| Automation (n8n, Zapier, Make.com) | 6 + 6 | **new finding** — not in job-market research at all, but a real, repeated pattern among these profiles |
| FastAPI | 5 | **new** |
| Cloud platform (AWS/GCP/Azure) | ~5-6 combined | confirmed, lower priority than expected |
| LLM fine-tuning | present | confirmed, less-tagged than job-market research suggested |
| MLOps | 2 | **downgraded** — job-market research suggested this was a headline skill; among real top freelancer profiles it's rarely an explicit tag |
| Containerization (Docker/Kubernetes) | ~1 | **downgraded**, same reason |
| LLM evaluation | 0 | **removed from confidence** — didn't appear as an explicit tag anywhere in the sample; kept in the underlying skill list but no longer a strong signal |

## Rate band

**$15–$120/hr USD**, median **$35/hr**, mean **$42/hr** — real distribution across the 30 profiles, not a survey estimate.

**This is the single most useful finding from the real data**, and it's a meaningful correction: the earlier version, built from general freelance-market rate reports, put "experienced" AI/ML freelancer rates at $118–195/hr average. The real Upwork data — even filtered to Top Rated / Top Rated Plus, the platform's own quality tier — runs substantially lower and more price-competitive than broad market surveys suggested. A profile charging $35/hr on Upwork isn't necessarily underpricing itself; it may be sitting exactly at the real median for this platform. Several of the highest earners in the sample (self-reporting $500K+ to $700K+ lifetime Upwork earnings) were charging in the $65–120/hr range, not the $150–250/hr the earlier market research implied was typical for "senior" work.

Full distribution: 15, 15, 17, 20, 20, 20, 25, 25, 30 ×6, 35 ×3, 36, 40, 40, 45, 45, 50, 65, 70, 75, 75, 80, 85, 120.

## Title formula

```
{role/seniority} | {specialization or key technologies}
```

**Changed from the earlier version**, which included `{measurable outcome}` as a third title component. Real data doesn't support that: only 1 of the 30 titles contained any digit at all, and even that one was a project count ("200+ AI Projects"), not a client outcome metric. Measurable results — dollar figures, percentage improvements, hours saved — appear constantly in these profiles, but in the **overview**, not the title. The title's job is role + specialization; the overview's job is proof.

## Overview structure

Confirmed hook → proof → process → call to action, but with specific, real stylistic patterns worth naming:

- **Explicit self-stated credibility markers inside the text itself** — "100% Job Success," "Top Rated Plus," years of experience, and dollar-earned figures are frequently restated in the overview's own prose, not just left to Upwork's badge display.
- **Named proof sections** — several profiles use literal subheadings like "Client Success Stories" or "RESULTS WITH FACTS," followed by bulleted, quantified outcomes (e.g., "cut manual workflows by up to 85%," "$500K+ Earned," "Reduction of up to 70% in project expenses").
- **Heavy use of emoji/symbol bullets** (📌 🏅 ⚡ → ⭐) to break up scannable lists — a concrete stylistic pattern generic profile-writing advice doesn't mention.
- **Direct address of the buyer's problem in the opening line** is common but not universal — several strong profiles open with a first-person credential statement instead ("I'm an AI Engineer with 6+ years...") and still perform well, suggesting the "always open with the buyer's problem" rule from generic research is a strong tendency, not an absolute one.

## Portfolio expectations

Real median: **7-8 items** (range 0-69). `portfolio_min` stays at **3** as a floor, not a target — real data supports it being a floor: one $85/hr profile in the sample had **zero** visible portfolio items at all, backed instead by a strong work-history/review track record. Portfolio isn't strictly load-bearing if other evidence (reviews, job success score, hours worked) is strong.

One correction to the earlier version's assumption: portfolio card **previews** in this sample mostly did **not** show explicit quantitative metrics on the card face itself — most displayed UI mockups, architecture diagrams, or product screenshots, with only a handful showing a visible number or percentage badge. Generic portfolio-writing advice emphasizes "show results, not just samples" — real top profiles in this niche seem to save the numbers for the overview and case-study detail, not necessarily the portfolio grid's cover image.

---

## Confidence level

| Section | Confidence | Why |
|---|---|---|
| Required terms | **High** | Real frequency counts from 30 actual profiles, not a proxy |
| Rate band | **High** | Real distribution, not a survey estimate — this is the finding most worth trusting and the most surprising relative to the earlier version |
| Title formula | **High** | Directly observed pattern (title-vs-overview split confirmed by checking every title in the sample) |
| Overview structure | **High** | Directly observed stylistic patterns across the sample |
| Portfolio expectations | **High** | Real distribution and a concrete counter-example (zero-portfolio, still $85/hr) |
| **Dimension targets** (the 0-100 target score per scoring dimension) | **Still low** | This is the one field real profile text genuinely can't answer directly — it would require running this system's own scoring formulas against real profiles and observing what top performers land on, which is a different exercise (running the *product*, not reading profiles) than this benchmark-building step covers. Still a reasoned estimate. |

**Bottom line:** this benchmark is now built on real evidence for everything except the internal dimension-scoring targets. The rate-band finding in particular is worth a conversation on its own — it materially changes what "a defensible rate" looks like for this product's pricing guidance.

---

*Machine-readable version: [benchmarks/ai_ml_engineering_freelance.py](benchmarks/ai_ml_engineering_freelance.py) — the actual file the scoring system reads, including exact frequency counts in comments. This document is the human-readable explanation; if the two ever disagree, the Python file is authoritative.*

*Raw source data (30 real Upwork profiles) is intentionally not included in this repository — see Methodology above.*
