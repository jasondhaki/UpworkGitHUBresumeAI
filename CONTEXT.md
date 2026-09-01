# Session Context Log

Running log for the AI5K Profile Intelligence System build. Read the top entry first when picking this project back up — it has the current state and the reasoning behind it, so we don't have to re-derive decisions from scrollback or re-litigate something already settled.

**How this file works:**
- Newest entry at the top.
- Each entry: what changed, why, what's next. Not a transcript — skip sessions that made no real change.
- Update this at the end of every session (see `CLAUDE.md` — it's a standing instruction now, not something to remember manually).
- Revisit it at the start of any session, even a small one, before making changes.

**PENDING (as of 2026-09-02):** stress-test the CV parser against a few more differently-structured CVs, and **run the user's real resume (`RESUME.pdf`, gitignored, lives in the project root locally — not in git) through the full pipeline** — both blocked on Gemini's free-tier rate limit, which is proving to be a very tight, intermittent allowance rather than a clean daily reset: one live call succeeded (GitHub ingestion + generation, all 7 scoring dimensions, confirmed working end-to-end for real — that item is DONE, off this list), then the very next attempt (the real resume) hit a hard 429 again seconds later. Don't assume "it worked once" means it's clear — verify each attempt independently. Check the live limit at https://aistudio.google.com/rate-limit if guessing timing isn't working. First thing to do in the next session that touches this project. See the log below for full detail — note the UI has been redesigned twice since this item was written (dark/glow theme, then a `/benchmark` page added), so re-verify screenshots reflect the current look before assuming anything visual is stale.

---

## 2026-09-02 — Two more real crash bugs found the same way; project finally has requirements.txt and a README

**What changed:**
- Asked directly "what's left that doesn't need Gemini" — answered by finding two more real bugs using the same technique that found the Docling one: deliberately simulate the failure rather than assume, and check whether it's actually caught.
- **`github_parser.py`**: simulated a network failure (pointed the client at an unreachable host) and confirmed `httpx.ConnectTimeout` propagated completely uncaught — same bug shape, different module. Added `GitHubUnavailableError` and wired it into `main.py`.
- **`app/llm/gemini_client.py`**: this one was subtler. The retry loop only caught `httpx.TimeoutException`, and a `ConnectTimeout` (used to test the GitHub fix) happens to be a `TimeoutException` subclass, so that case was already covered. But `httpx.ConnectError` — a *sibling* exception (connection actively refused, not a timeout) — is not a `TimeoutException` subclass, and confirmed by deliberately triggering a real connection-refused error (pointing at a closed local port) that it propagated completely uncaught through both the retry loop and `main.py`'s handlers. Fixed by broadening the retry loop to catch `httpx.RequestError` (the true parent covering every network-level failure) instead of just `TimeoutException`, while deliberately leaving genuine bad-status errors (a malformed request, e.g.) un-retried — retrying those wastes attempts on something retrying can't fix. Simplified all three `except` clauses in `main.py` from `(httpx.TimeoutException, httpx.HTTPStatusError)` to the shared parent `httpx.HTTPError`, which correctly covers both the Gemini client's failure modes now.
- Added **`requirements.txt`** (runtime deps, pinned to exact working versions) and **`requirements-dev.txt`** (adds Playwright/fpdf2/python-docx for fixture generation and browser testing) — genuinely missing until now; nobody, including a fresh clone of this repo, had any way to know what to install.
- Added **`README.md`** — the public repo had no entry point at all. Covers what the project is, setup, how to run it, how to run each module's `smoke_test.py`, project layout, and an honest "what's real vs. still a placeholder" section pointing at `BENCHMARK.md`'s confidence breakdown.
- Full regression pass across every zero-Gemini smoke test plus a live no-input server check — all clean.

**Why:**
- Three uncaught-exception bugs in one build, all in the same shape (a specific exception subclass caught, its sibling not), suggests a pattern worth remembering generally: when catching network exceptions, catch the actual shared parent class (`httpx.RequestError` / `httpx.HTTPError`), not a specific subclass that happens to cover the one failure mode already tested. Narrow excepts silently miss siblings.
- `requirements.txt` and `README.md` are the kind of gap that's invisible while working in an already-set-up environment (this one) and only surfaces the moment someone else — or future-you on a new machine — tries to actually use the repo. Worth checking for proactively, not just reactively when someone hits it.

**Next steps:**
- PENDING line unchanged — none of this touched Gemini.
- Not yet committed/pushed — do that next.

---

## 2026-09-02 — Trimmed the /examples disclosure blocks per request, kept minimal honest disclosure

**What changed:**
- User asked to remove the "these are synthetic" banner and the "Why not real excerpts?" section from `/examples` — a content-density request, not a request to hide the synthetic nature. Removed both plus the now-unused `.synthetic-banner` CSS.
- Checked before removing everything: the hero paragraph already states "No individual profile is quoted or reproduced," and each card sits under a section literally titled "[X] archetypes." That minimal disclosure survives the removal, so the page doesn't end up silently presenting invented profiles as real — removing the two heavier explanatory blocks doesn't mean removing all signal.

**Why:**
- Worth being deliberate here rather than reflexively complying with "remove X" as "remove all trace of X's purpose" — the specific request was about visual weight/redundancy, and honoring it didn't require dropping the one-line disclosure that keeps the page honest.

**Next steps:**
- PENDING line unchanged.
- Not yet committed/pushed — do that next.

---

## 2026-09-02 — User pushed back on the anonymization call; held the line with specific reasoning, expanded the safe version instead

**What changed:**
- User asked for 10+ archetypes (at least 3 per category) and explicitly reversed the earlier decision on real vs. synthetic: "forget the anonymous parts... their profiles are public anyway... just don't use the names directly."
- **Held the position rather than complying**, but explained precisely rather than just refusing: removing a name solves identifiability only partially (specific numbers, named clients, and portfolio titles can still make someone traceable) and doesn't touch the separate, bigger issue at all — the overview text is each person's own original writing, and copyright doesn't require a name to apply, so stripping one doesn't create permission to republish it. Both hold regardless of the "public profile" framing, and both are real exposure sitting on the user's own public GitHub account, not just a style preference.
- Delivered the actual underlying goal generously instead: expanded from 3 to **10 synthetic archetypes**, organized into the three real search categories (4 AI Engineer / 3 Machine Learning Engineer / 3 LLM Engineer), spanning the genuine variety observed in the real 30-profile data (agentic/automation, conversational AI, full-stack AI product building, computer vision, MLOps/data engineering, applied research, LLM fine-tuning, NLP research, generative AI product work) — all newly-invented copy, every skill tag re-verified line by line against the real `REQUIRED_TERMS` list. Added a "why not real excerpts" section at the bottom of the page stating the reasoning in the product's own voice, not just in this log.
- Verified at desktop and mobile widths.

**Why:**
- A user restating a request more forcefully isn't new information that changes the underlying facts (identifiability, copyright, ToS) — the right response to pushback grounded in "it's public anyway" is to explain specifically why that framing doesn't fully resolve the concern, not to fold because the ask was repeated. Prior approval or a stronger ask doesn't expand the scope of what's actually safe to do with third parties' content.
- Making the reasoning visible on the page itself (not just here) matters for the same reason the rest of this build insists on traceability — if someone later asks "why archetypes and not real examples," the answer should be discoverable on the site, not something only findable by asking the assistant that built it.

**Next steps:**
- PENDING line unchanged — none of this touched Gemini.
- Not yet committed/pushed — do that next.

---

## 2026-09-02 — Asked for real anonymized profiles on the site; built synthetic archetypes instead, with the reasoning made explicit

**What changed:**
- User asked for a page showing the 30 benchmark profiles' "design" — explicitly said no private info, just structure, so users can see what wins in the industry. Good instinct, but flagged a real distinction before building anything: even fully anonymized (no names), reproducing real individuals' actual profile *text* — specific overview wording, specific numbers, specific portfolio project names — on another public page is still risky two ways: (1) often identifiable via distinctive phrasing even without a name, (2) it's their own original writing, republished elsewhere without consent. That's the same reasoning that kept the raw 30-profile data out of the repo in the first place; showing "anonymized" individual cards would have quietly reversed that decision without saying so.
- Gave the user a real choice via `AskUserQuestion` rather than either silently building the risky version or silently substituting something safer without explanation: synthetic archetype cards (recommended), a pure aggregate/statistical view with no profile-shaped cards, or proceeding with real anonymized excerpts after talking through the risk more. User chose synthetic archetypes.
- **Built `/examples`**: three archetype cards (AI Engineer / Machine Learning Engineer / LLM Engineer — matching the three real search categories the benchmark was built from), each with invented title/overview copy written specifically for this page, but using only real data where real data exists — every skill tag cross-checked line-by-line against the actual `REQUIRED_TERMS` list before use, rates chosen within the real $15-120 band. A prominent banner states plainly these are synthetic, not reproductions, with a link to `/benchmark` for the real underlying numbers.
- Verified at desktop and mobile widths.

**Why:**
- The user's actual goal (show what wins, build trust/credibility) doesn't require reproducing real people's writing — it requires showing the real *patterns*, which the benchmark data already captures. Synthetic archetypes serve the goal without the risk.
- Explaining the concern and offering the choice, rather than just declining or just complying, keeps the user in control of a decision that's genuinely theirs to make — they might have had context that changed the calculus (they didn't, but the point of asking is not assuming that in advance).

**Next steps:**
- PENDING line unchanged — none of this touched Gemini.
- Not yet committed/pushed — do that next.

---

## 2026-09-02 — Removed the fabricated hero cards; added a real /benchmark page

**What changed:**
- User pointed out the stacked score-card hero mockup was unnecessary — and on reflection it was also fabricated example data (fake 78/22/54 scores) sitting in the hero of a product whose entire premise is not showing unproven things. Removed it and the now-unused CSS/keyframe; the headline now flows straight into the source-explainer row.
- Asked a clarifying question about "put the tier list on the sides" rather than guessing — turned out to just be a question about the tier count (confirmed: 8, fixed, not niche-specific), not a layout request. No change needed there.
- That question led to a real gap: the user didn't know the difference between the 8 evidence tiers (universal, per-claim, how corroborated a piece of evidence is) and the benchmark (niche-specific, what "good" looks like, built from the 30-profile read) — explained the distinction, then the user asked to surface this on the site itself so users understand what they're being rated from.
- **Built a new `/benchmark` page** rather than cramming this into the intake or results flow: verification badge (real data vs. provisional, pulling directly from `benchmark.provisional`/`sample_size`), the 7 dimension targets as bars, all 24 required skills as hoverable pills (title attribute shows synonyms), the real rate band, title formula / overview length / portfolio floor, and the full `source_notes` methodology text with a link out to `BENCHMARK.md` on GitHub for the complete writeup rather than duplicating it. Added to the header nav and linked from the intake page's tier-chain caption.
- One design fix along the way: first pass rendered the long methodology paragraph in the same big serif "pull-quote" treatment used for the intake page's short governing-rule quote — reads fine for one punchy sentence, reads oddly for a full paragraph of explanatory prose. Gave it its own plainer card style instead.
- Verified at desktop and mobile widths before calling it done.

**Why:**
- Asking instead of guessing on the "sides" comment was worth it — the literal request ("just confirming the count") was materially different from the most likely-sounding interpretation (a layout change), and building the wrong one would have wasted real effort.
- A dedicated benchmark page fits this product's own transparency principle better than folding a methodology explainer into the results page — the results page is about *this* profile, the benchmark page is about the yardstick itself, and conflating them would have made both busier.

**Next steps:**
- PENDING line above updated with a note that it should be re-verified against the current (now twice-redesigned) UI, not assumed stale-but-otherwise-accurate.
- Not yet committed/pushed — do that next.

---

## 2026-09-02 — Full dark/glow redesign, following a concrete visual reference the user provided

**What changed:**
- User shared real screenshots of AuthKit (WorkOS) as a direct visual reference — dark starfield background, glowing gradient text, stacked glass cards, connected-node icon rows, animation. Said explicitly to keep our own data, not theirs. Per the design skill's own rule ("where the brief pins down a visual direction, follow it exactly"), rebuilt the entire visual system around this rather than defending the earlier light "evidence ledger" concept — a reference image is about as concrete a brief as it gets.
- **Rebuilt the token system for dark**: near-black background (`#070a13`), a CSS-only starfield (layered radial-gradients tiled at 480px, not a real random field but reads as one), a faint grid overlay, and a soft radial glow behind the hero — all in `body::before`/`::after` so they don't scroll with the (long) report pages. Kept the exact same meaning-mapping as the light version (per-source colors, per-dimension colors, score-range colors, tier-weight-driven glow) — the mood changed, the "design IS the data" principle didn't.
- **Adapted their signature elements to our real content** rather than copying verbatim: their "3 stacked overlapping login forms" hero became 3 stacked case-score cards (a 78/capped-22/54-focus trio) — a literal, meaningful fit since that's what this product actually outputs. Their connected-icon feature row became the CV/GitHub/Upwork source explainer, now with actual connecting dotted lines between glowing icon nodes. Added a new element their reference didn't have but our content justified: a horizontal "tier chain" — all 8 evidence tiers connected in one glowing row, brightest at T1 fading to nearly dark at T8, using the same weight-driven `--strength` variable as the ledger's tier stamps.
- **Deliberately did not copy their testimonial section** — fabricating a quote from a fake person would be exactly the kind of unproven claim this whole product exists to catch, especially conspicuous on this specific project. Used the same glass-card visual pattern for an honest pull-quote instead, sourced from the plan's own actual governing rule ("a claim with no source span is never published..."), and replaced their generic "start building" CTA row with one real link (the actual public GitHub repo) instead of a second fabricated CTA.
- Added tasteful, restrained CSS-only animation per the design skill's "spend it in one place" guidance: a staggered fade-in on page load, a gentle float on the stacked hero cards, a slow pulse-glow on the score stamp — `prefers-reduced-motion` still respected (already had the guard, kept it).
- **Found and fixed two real bugs by re-screenshotting**, not just trusting the CSS: the two background stacked cards were nearly invisible (opacity too low against the dark backdrop — bumped 0.55 to 0.85 and gave them a visible border); the 8-tier chain overflowed its container with per-node text labels (an 8-word row doesn't fit at readable size) — fixed by dropping to hover-tooltips per tier plus one summary caption line instead of 8 separate labels.
- Verified at both desktop and mobile widths after the fixes.

**Why:**
- This is the second time in this project that "screenshot before declaring done" caught something real that reading the CSS wouldn't have — worth continuing to treat visual work as needing visual verification, not code review.
- Refusing to fabricate a testimonial wasn't just a stylistic call — it's the same principle the whole product enforces on its own users, so faking one here specifically would have undercut the pitch in a way a generic marketing site wouldn't need to worry about.

**Next steps:**
- PENDING line unchanged — none of this touched Gemini.
- Not yet committed/pushed — do that next.

---

## 2026-09-02 — Design felt too bland/empty; pushed a lot more color and content in, still tied to real data

**What changed:**
- User feedback on the first design pass: too refined-into-emptiness, too much flat white, wanted it "populated with stuff and colors" relevant to the project. Fair critique — the earlier restraint (spend boldness in one place) read as sparse rather than considered once actually shown. Responded by expanding the palette substantially rather than defending the minimal version.
- Added three new color systems, each tied to real data (not decoration): **per-source colors** (CV/GitHub/Upwork each get a distinct hue, used on ledger badges and a new source-explainer row), **per-dimension colors** (all 7 scoring dimensions get distinct colors on the bars, so the dimension section reads as varied instead of a wall of uniform brass bars), and **score-range coloring** (the certificate stamp recolors red/amber/green by actual readiness band, same logic a credit report uses).
- Added real content to fill the intake page, not just decoration: a three-source explainer row with icons (what CV/GitHub/Upwork ingestion actually does), and the full eight-tier evidence legend rendered with the same weight-driven tier-stamp component used throughout the app — genuinely explains the product's core mechanic before someone submits anything, while also being the most colorful/informative section on the page.
- Added a gradient band (built from the actual source + brass accent colors, not arbitrary) across the top of every page, section icons (small inline SVGs, one per results-page section, colored to match that section's theme), and a subtle dot-grid texture on the page background to kill the flat-white feeling.
- Refactored to a shared component (`base.html`'s `.hero-band`) rather than repeating the gradient per page.
- Fixed one real layout bug caught by re-screenshotting after the change: "keyword coverage" wrapped awkwardly in the fixed-width dimension-label column once colored dots were added; widened the column. Also added a mobile breakpoint for the new source-explainer row (3 columns → 1 on small screens), which the first pass hadn't needed.
- Re-verified visually at desktop width via fresh screenshots before calling it done, not just by reading the CSS.

**Why:**
- The lesson from the first design pass held (screenshot and self-critique rather than trust the code), but the actual creative call — how much restraint versus richness — needed real user feedback to get right; "make deliberate choices" doesn't mean "assume minimal is always correct."
- Kept every addition tied to real data on purpose: it would have been faster to just add arbitrary decorative color, but that contradicts the whole "evidence ledger, not decoration" concept the design is built on. Richer does not have to mean less meaningful.

**Next steps:**
- PENDING line unchanged — none of this touched Gemini.
- Not yet committed/pushed — do that next.

---

## 2026-09-02 — Real UI/UX design pass: the app now looks like a considered product, not a walking skeleton

**What changed:**
- User needs to present this to their boss and asked for real visual design, not just functional HTML — a deliberate scope addition, not creep (explicitly requested). Loaded the `frontend-design` skill before touching anything, per its process: named a concrete design concept before building rather than defaulting to a generic dashboard look.
- **Design concept**: an "evidence ledger," not a dashboard — this app's real differentiator (every claim carries a tier T1-T8 and a weight, nothing unproven gets published) became the actual visual system rather than decoration bolted onto a generic template. Cool paper background (not the cliché warm-cream), ink-dark text, a brass/ochre accent reserved for *verified* evidence, muted slate for *unverified*, brick-red for blocking/liability flags — every color is tied to what the data means. Type: the IBM Plex family used as one designed system (Serif for display, Sans for body, Mono for data/scores/tiers), not a generic pairing.
- **Signature element**: evidence "tier stamps" whose visual weight (opacity, border fill) is set directly from the claim's real `weight` value in the markup (`style="--strength: {{ claim.weight }}"`), not a fixed per-tier lookup baked into CSS — the design IS the data. Confirmed visually in a real screenshot: T1 (client-verified) renders solid and confident, T8 (self-declared) nearly disappears, making "don't trust unproven claims" visible before reading a single number.
- Skipped the generic circular-progress-ring score treatment (explicitly flagged by the design skill as the template answer) in favor of a certification-stamp frame around the score numeral: solid brass border when real evidence backs it, dashed/faint border when the evidence cap has kicked in — the visual state is driven by the same `result.capped` boolean the backend already computes, not a separate decorative choice.
- Dimension bars get a target *tick mark* (a thin vertical line at the benchmark target position) rather than a second bar or a percentage label — reads like a measurement instrument, and is directly computed from real `dimension.target` values.
- Generated title/overview get footnote-style numbered citation markers (with hover tooltips showing the backing claim's tier and text) instead of a flat "sourced from: id1, id2" list — refactored into a Jinja macro to avoid duplicating the logic between title and overview.
- Built as a proper shared system: `app/static/style.css` (design tokens + components) + `app/templates/base.html` (shared header/layout), with `index.html`/`result.html`/`runs.html`/`error.html` all extending it — not 4 separately inline-styled pages like before. Wired static file serving into `main.py`.
- Rewrote copy throughout in the product's own voice per the design skill's writing guidance: "Open a case" / "Fix before publishing" / "Where to focus next" / "Evidence ledger" — active voice, plain terms, tied to what the system actually does, not generic SaaS-dashboard language.
- **Verified visually, not just functionally**: screenshotted every page (intake, results — both a withheld-generation case and a full case with real generated content built from fake data to check the citation styling — error page, runs history) at desktop and mobile widths, self-critiqued, and fixed two real issues found this way: the raw OS-styled file-upload button clashing with the rest of the form, and a legend marker shape that didn't match the actual tick-mark style it was explaining.

**Why:**
- Loading the design skill first and naming a concrete concept before writing any CSS is what kept this from becoming a generic dashboard — the tier-stamp system specifically only exists because the brief was "what does *this* product's real content look like," not "what does a results page usually look like."
- Screenshotting and self-critiquing rather than just trusting the code to look right caught two real, fixable issues that reading the HTML/CSS wouldn't have surfaced.

**Next steps:**
- PENDING line unchanged — none of this touched Gemini.
- Not yet committed/pushed — do that next.

---

## 2026-09-02 — Found and fixed a real crash bug (zero Gemini cost); confirmed Gemini quota is a tight intermittent trickle, not a clean reset

**What changed:**
- User said to keep moving and let Gemini-blocked work wait. Found genuinely valuable non-Gemini work instead of idling: `.docx` support had been claimed (`FileType.DOCX` exists) but never actually tested end to end — verified it for the first time with a real generated `.docx` fixture; works correctly.
- Stress-tested `file_router.py` against edge cases that fail *before* Gemini is ever reached (so fully testable regardless of quota): a garbage-bytes file wearing a `.pdf` extension, an empty `.pdf`, wrong extensions. **Found a real, previously-unknown bug**: a corrupted/non-PDF file raises `docling.exceptions.ConversionError`, which nothing caught — a real user hitting this case today would have gotten a raw 500 crash, not a clean error message. Fixed by adding `InvalidDocumentError` (distinct from `ScannedDocumentError` — this is "not parseable at all," not "parseable but no text layer") and catching Docling's `ConversionError` around the conversion call. Verified the fix both directly and through the live running app.
- **Gemini quota briefly opened up mid-session**: a live GitHub-only integration test (ingestion → all 7 scoring dimensions → generation → storage → display → history) succeeded for real — correctly grounded title/overview with real numbers traced to real GitHub claims. That's the "verify all seven dimensions live end-to-end" PENDING item, genuinely done now (via GitHub+generation rather than the originally-planned CV+Upwork combination, but it exercises the same formulas with real generated content either way).
- Immediately tried the real resume next while the window seemed open — it hit a hard 429 within seconds of the prior success. **This is an important nuance to remember**: the quota is not resetting cleanly; it's granting a very small, intermittent allowance. One successful call is not evidence the block has lifted — checked directly again after the failure and confirmed still 429. Stopped there rather than keep spending attempts chasing a trickle.

**Why:**
- The corrupted-file bug is exactly the value of doing edge-case testing that doesn't depend on the blocked resource — it would never have been found by waiting for Gemini, since it fails upstream of any API call.
- Worth stating plainly for future sessions: "quota partially working" and "quota reset" are different states, and treating the former as the latter would waste the few real calls available on avoidable failures.

**Next steps:**
- PENDING line updated: CV stress-testing and the real resume test remain, dimension verification is done.
- Not yet committed/pushed — do that next.

---

## 2026-09-02 — The real 30-profile benchmark read happened; benchmark is no longer provisional

**What changed:**
- User manually collected real data on 30 currently-active Top Rated / Top Rated Plus Upwork profiles (~10 each: AI Engineer / Machine Learning Engineer / LLM Engineer), dropped in as `30BestProfiles.txt` at the project root. This is the actual Phase A/C task ("read 30 top profiles in the niche, pull out patterns by hand") that's been an open item since the very start of the build.
- **Protected the raw data before touching it**: added `30BestProfiles.txt`, `research/`, and a converted `.md` copy to `.gitignore` in a standalone commit before reading or processing anything, same pattern as `RESUME.pdf`. This data identifies real third-party individuals (names, rates, work history) — treated it with the same care, and applied the plan's own explicit design principle for exactly this situation (Section 3, Anchor track: "extracts structural patterns... then discards the source profiles — only aggregate patterns are kept"). Converted the raw txt into a cleaner `research/30BestProfiles.md`, kept local-only.
- Computed real numbers from the data (script-verified, not eyeballed): rate distribution (min $15/hr, max $120/hr, median $35/hr, mean $42/hr across all 30), portfolio-item distribution (median ~7.5, range 0-69), and exact skill-tag frequency counts (156 unique tags tallied).
- **Rewrote `benchmarks/ai_ml_engineering_freelance.py` with real, non-provisional data**: `provisional` flipped to `False`, `sample_size` to `30`. `required_terms` corrected significantly — added several very-common real tags the earlier job-posting-based research had missed entirely (Machine Learning 24/30, Artificial Intelligence 22/30, Deep Learning 17/30, Computer Vision 9/30, Chatbot Development 9-10/30, and a genuinely new finding: automation tooling like n8n at 6/30, absent from any earlier research pass) and downgraded confidence on terms the research had overweighted (MLOps only 2/30 as an explicit tag, containerization ~1/30, LLM evaluation 0/30). `rate_band` replaced with the real $15-120 range. `title_formula` changed from including "{measurable outcome}" to dropping it — verified only 1/30 real titles contained any digit at all, and even that was a project count, not a client outcome; real profiles put measurable results in the overview, not the title.
- Rewrote `BENCHMARK.md` around the real findings, most notably: **real Upwork rates run substantially lower than the general market-rate-survey data the earlier version relied on** ($35/hr median vs. the earlier $118-195/hr "average experienced freelancer" figure) — flagged prominently since it's the kind of finding that changes what "a defensible rate" actually means for this product. Also documented real, concrete stylistic patterns (named "Client Success Stories" proof sections, emoji-bullet formatting, self-stated credibility markers inside overview prose) that generic profile-writing research never surfaced. Dimension targets remain the one field still flagged low-confidence — profile text genuinely can't answer what score this system's own formulas would assign, that needs a different exercise (running the product against real profiles, not reading them).
- Verified the updated benchmark loads correctly and scores sensibly with zero Gemini calls (direct load check + re-running the GitHub ingestion path, which imports the real benchmark).

**Why:**
- Doing the real word-count/frequency tallies with a script rather than eyeballing 30 long tag lists by hand was worth the two minutes — caught the exact numbers precisely (e.g., confirming "only 1/30 titles contains a digit" by grep rather than impression, which mattered enough to change `title_formula`).
- The rate-band finding specifically deserves to be surfaced prominently, not buried — it's the single most boss-relevant insight in this whole benchmark-building effort, and easy to miss if the doc just quietly updates a number without calling out that it contradicts the earlier, differently-sourced figure.

**Next steps:**
- The PENDING line (rate-limit-blocked items: live dimension verification, CV stress-testing, the real-resume test) is unchanged — none of this touched Gemini.
- Not yet committed/pushed — do that next.

---

## 2026-09-02 — Real resume dropped in for testing; confirmed rate limit is still hard-blocking

**What changed:**
- User dropped their actual resume in as `RESUME.pdf` at the project root, explicitly to be used as a real test CV — and explicitly said not to let it reach GitHub. Added `RESUME.pdf` (and a `*.resume.pdf` pattern for any future variant) to `.gitignore` **before** touching anything else, committed that alone first, then proceeded. This is the first real person's resume this build has ever touched, not a synthetic fixture.
- Attempted the real end-to-end test via the actual live app (not a bypass script). Failed the same way as earlier today: Gemini extraction failed after retrying. Checked directly with a minimal, isolated API call (bypassing the CV/Docling overhead entirely) to confirm exactly what's happening rather than guess — confirmed it's still a genuine 429 (quota), not a transient 503 (overload). Same root cause as the earlier-flagged PENDING item, not a new problem.
- No resume content was extracted or stored anywhere — the failure happened before any real data left the request. Test artifacts (a one-off script and its output) were kept entirely in the OS temp/scratchpad directory, never in the repo, specifically because this test's output would contain real personal data.

**Why:**
- Verifying the actual error type (429 vs 503) via a minimal isolated call, rather than assuming from the same generic error message, is worth doing every time this comes up — they mean different things (quota exhaustion vs. transient overload) and only one of them is worth retrying.

**Next steps:**
- All three items in the PENDING line now share one root cause. Nothing further to do here until Gemini's quota resets — see the PENDING line for what to pick up first.
- Committed and pushed.

---

## 2026-09-02 — Blocking-item detection built (the one gap that wasn't blocked on anything)

**What changed:**
- User asked for an honest status check against the plan's own Definition of Done. Surfaced a real gap that had gone unflagged until asked directly: `Result.blocking` was fully plumbed through the UI and storage, but nothing ever populated it — every run to date had `blocking: []` by default because the detection logic itself was never built, only the pipe for it.
- Built `app/scoring/blocking.py` with two deterministic, well-grounded checks: (1) **missing identity verification** — always true for every Phase 1 profile, since "accounts and login" is explicit out-of-scope, so there is no verification mechanism at all; flagging this honestly matches the plan's own example verbatim. (2) **unproven core claims** — for each of the niche's required skills that a profile actually claims, find the *strongest* evidence backing it; if the strongest evidence for a claimed core skill is T8 (self-declared, zero corroboration), flag it as a liability, not just a scoring gap.
- **Deliberately did not build a third check** the spec names — "ToS risk." There's no well-grounded, non-speculative way to detect that from a claim set with what this build actually has (no client NDAs, no platform terms to check against). Building a fake detector just to populate the category would produce exactly the false confidence this whole system exists to prevent, so it's documented as intentionally absent rather than faked.
- Wired into `score_profile()`: `blocking` defaults to real auto-detection now instead of always being `[]`; still accepts an explicit override (including `blocking=[]`) for testing.
- Verified with fake data (new `app/scoring/smoke_test_blocking.py`): confirmed a self-declared-only core-skill claim gets flagged, confirmed the same skill backed by real T2 evidence does NOT get flagged, confirmed `score_profile` auto-populates by default, confirmed the override still works. Also confirmed end-to-end through the actual running server with zero Gemini cost (a no-input request correctly shows the identity-verification item).

**Why:**
- This gap existed silently because nothing forced surfacing it — the field existed, the display existed, tests passed, and "blocking: []" looks identical to "no blocking items detected" unless you know to ask "wait, has this ever actually fired?" Worth remembering as a pattern: a field being wired through end-to-end is not the same claim as the logic behind it being real.

**Next steps:**
- PENDING item below is unchanged — this work didn't touch Gemini at all, so it doesn't affect the rate-limit-blocked verification.
- Not yet committed/pushed — do that next.

---

## 2026-09-02 — All seven scoring dimensions now real; hit the actual Gemini rate limit doing it

**What changed:**
- Built real formulas for the five dimensions that were still placeholder numbers (`app/scoring/dimensions.py`): `completeness` and `portfolio_quality` are fully deterministic checklists/claim-counts (no LLM needed — Section 2 doesn't actually require judgment for these, just presence/absence and counting); `pricing_strategy` is deterministic given one new input (a stated hourly rate — nothing collected that before, added a form field for it); `positioning` and `conversion` are **documented rules-based proxies**, not real semantic judgment — Section 2 describes both in genuinely semantic terms ("stated specifically enough to be found and believed", "addresses the buyer's problem"), which a cheap heuristic can only approximate, not actually assess. Chose the proxy route over spending a Gemini call per profile on subjective rating, consistent with the API call discipline — flagged clearly in both dimensions' docstrings so the approximation is never mistaken for the real thing.
- **Restructured the request flow**: generation now runs *before* scoring, not after — positioning/conversion need the generated title/overview as input, so the old "score, then bolt generation on" order no longer works. `score_profile()` no longer takes `manual_dimension_scores`; it takes `generated` and `stated_rate` instead and computes all seven dimensions itself. Updated every call site (`app/main.py`, all affected smoke tests).
- Added a `stated_rate` field to the intake form — optional, used by `pricing_strategy` and one `completeness` checklist item.
- Verified the new formulas with fake data first (`app/scoring/smoke_test.py`, rewritten): confirmed by hand-checking the math that a modest rate scores as more "defensible" than a top-of-band rate when evidence is thin (100 vs. ~17.7 on `pricing_strategy`), and that positioning/completeness/portfolio_quality all respond correctly to a richer claim set with real generated content attached.
- Re-verified two zero-cost Phase C hardening cases against the actual running server: the scanned-PDF-rejection path still works correctly end to end (a sparse-text PDF correctly triggers `ScannedDocumentError`, not a silent bad parse), and invalid `stated_rate` input (non-numeric) is caught and shown a clean error rather than crashing.
- **Hit Gemini's actual rate limit** (HTTP 429, not just the 503 "high demand" seen earlier) trying to do one deliberate live end-to-end pass of the new formulas together with real generation. This is the exact scenario the user flagged when asking for the API call discipline — today's testing volume across the whole session actually exhausted the free-tier quota, not just hit transient overload. Stopped retrying rather than hammering it further once the error type made that clear.

**Why:**
- Building positioning/conversion as honestly-labeled proxies rather than spending a Gemini call per profile matches both the plan's own preference for rules-based logic where possible and the new API discipline — the alternative (an LLM judgment call for every scored profile) would eat real ongoing rate-limit budget for something a heuristic can approximate well enough for a demo.
- The 429 is worth remembering as a concrete data point: this session's cumulative testing volume alone can exhaust the free tier in a single day. Future sessions should treat that as a real constraint, not a hypothetical one.

**Next steps:**
- **Live confirmation still pending**: all five new formulas are proven correct against fake data with hand-checked math, and the wiring is code-reviewed, but a real full-pipeline pass (CV + Upwork + generation + all seven real dimensions together) hasn't succeeded live yet — blocked on the rate limit, not a known bug. Worth doing once quota resets (check the live limit at https://aistudio.google.com/rate-limit rather than guessing timing), but not urgent given fake-data confidence is already high.
- Remaining Phase C item: stress-testing the CV parser against a few more differently-structured CVs ("five different CVs parse without crashing") — also blocked on the same rate limit for now, since CV parsing needs a real Gemini call.
- Not yet committed/pushed — do that next.

---

## 2026-09-02 — Benchmark upgraded from guesswork to research-informed (deliberate detour from Phase B/C)

**What changed:**
- User asked to pause phase progression and rebuild the AI/ML engineering benchmark properly, offering to let Claude "scrape from the internet" if needed. **Drew a clear line first**: no automated pulling of individual Upwork profile pages or search results, even though the user offered — that's the exact scraping-a-platform-on-the-user's-behalf the plan itself rules out (PROJECT_PLAN.md line 104), regardless of who nominally asks for it. Confirmed the boundary is real, not just self-imposed: attempted to fetch Upwork's own *published* rate-guide article (not an individual profile) and got HTTP 403 — Upwork blocks bot access to its own pages too.
- Did legitimate public research instead: multiple 2026 freelance AI/ML rate reports, job-market skill-demand analysis (360k+ postings), and freelance-profile-writing best-practice guides. Rewrote `benchmarks/ai_ml_engineering_freelance.py` with this grounding: required terms expanded from 14 to 17 and reweighted toward what 2026 data actually shows growing (LLM/RAG postings up 340% since 2024, agentic AI/LangChain now a distinct fast-growing category); rate band widened and corrected from a guessed $50-150/hr to a research-backed $60-250/hr (multiple independent sources cross-checked against each other); title formula and overview structure validated against independent profile-writing research rather than changed (research confirmed the shape already in place).
- Still kept `provisional=True` — this is a real upgrade in quality, but it's demand-side/market research, not the direct top-profile read the plan's design actually calls for, and that distinction is now explicit in the file's docstring and source_notes rather than blurred.
- Wrote `BENCHMARK.md` — a presentation-quality doc (explicitly requested as showable to the user's boss) covering the benchmark's content, full methodology, and a **Confidence level** section that's honest per-section: required terms and rate band are medium-high confidence (real cross-checked sources), dimension targets are explicitly flagged low confidence (still essentially reasoned estimates — public research can't validate those without reading real profiles). Every source cited with links.
- Verified the updated benchmark loads and scores correctly with zero Gemini calls (pure Python check) before committing.

**Why:**
- The user's phrasing ("you can scrape from the internet") was ambiguous enough that silently either over-complying (actually touching Upwork) or under-complying (not researching at all) both seemed like the wrong call — worth stating the boundary plainly rather than guessing which the user meant.
- A benchmark document that oversells its own confidence would be worse than the honest placeholder it replaced, especially since this one is explicitly headed to the user's boss — the per-section confidence breakdown exists so nobody downstream mistakes "researched" for "validated."

**Next steps:**
- Back to phase progression as the user directed. Remaining Phase B/C items unchanged: the real 30-profile hand-read (still the only way to firm up dimension targets and confirm required terms against actual winning profile text — nothing this session did replaces that step, it just made the placeholder better while waiting on it), and the five scoring dimensions still using placeholder numbers.
- Not yet committed/pushed — do that next.

---

## 2026-09-01 — Real persistent storage added; found and fixed a real span-grounding gap

**What changed:**
- Built `app/storage/`: SQLite (deliberate substitution for Section 7's stated PostgreSQL — free, zero-config, appropriate for one hardcoded user with no concurrent writers; the repository functions are the seam to swap behind if that ever needs to change) holding one `analysis_runs` table (JSON blobs for the full `Result` and claim list — deliberately un-normalized, no current need for cross-run querying). `files.py` persists uploaded CVs to `data/files/`. Added `data/` to `.gitignore` **before** writing anything there, since the repo is public and uploaded CVs are personal data.
- **Found a real gap while building this**: uploaded CVs were being written to a `NamedTemporaryFile` and deleted immediately after parsing. A claim's `source_span.document_id` pointed at that temp path — meaning span grounding was only real *during* the request, not after, directly contradicting Section 2's requirement that original files stay re-readable "at generation time," not just at extraction time. Fixed by persisting the file first via `save_uploaded_file` and parsing from that permanent path instead.
- Wired storage into `app/main.py`: every `/analyze` call now saves the full claims + result via `save_analysis_run`. Added `GET /runs` (list past analyses) and `GET /runs/{run_id}` (view one, reusing `result.html` since a `Result` deserializes back into the exact same shape whether it's live or historical).
- Tested the storage layer with fake data first (round-trip including the computed `weight` field surviving serialization, and a missing-run-id case returning `None` not raising) — zero Gemini calls. Then hit sustained real Gemini 503s trying to do one deliberate full-pipeline browser test (CV+Upwork+GitHub+storage together) — two attempts both failed on the Gemini side, not ours (retry logic correctly produced a clean error page both times, not a crash). Rather than keep hammering an overloaded API, decoupled verification: inserted a real saved run directly via the actual `save_analysis_run` function (no Gemini needed) and confirmed both new routes (`/runs`, `/runs/{id}`) render real data correctly through actual HTTP calls. The one link not yet verified end-to-end is `/analyze` calling `save_analysis_run` after a *successful* Gemini-backed run specifically — low risk (one-line addition after an already-proven function) but worth confirming next time Gemini cooperates.

**Why:**
- The temp-file deletion bug is exactly the kind of thing worth having caught: it would have made "span grounding" a lie the moment any request finished, silently, with no error to surface it.
- Declining to retry a third time against a visibly overloaded Gemini, and instead finding a way to verify the actually-new code without it, is the API call discipline from `CLAUDE.md` working as intended — not every verification needs a live model call if the untested part can be isolated from the flaky dependency.

**Next steps:**
- Confirm the one remaining unverified link (a real `/analyze` success actually persisting) next time a full pipeline run is done for any other reason — no need for a dedicated call just for this.
- Remaining Phase B/C items unchanged: the real 30-profile benchmark (blocked on user), and the scoring dimensions still using placeholder numbers (positioning, portfolio_quality, completeness, conversion, pricing_strategy).
- Not yet committed/pushed — do that next.

---

## 2026-09-01 — Phase B checkpoint met: GitHub ingestion + grounded generation, all three sources real

**What changed:**
- Added a new default instruction to `CLAUDE.md`: don't spend real Gemini calls during iteration — build and test against fake/synthetic data by default (schemas, scoring, routing, templates all support this already), spend a real call only to verify a new/changed prompt for the first time and once per meaningful chunk of work at the end. Motivated by hitting rate limits/503s repeatedly from rapid testing. Explicitly a floor, not a ceiling: still requires at least one real end-to-end call before calling something done, since several real bugs this build only ever showed up under a live call.
- Built `app/ingestion/github_parser.py`: GitHub username -> Claim records with **zero Gemini calls** — GitHub's API already returns structured facts (stars, language, push dates), so there's no unstructured prose to interpret and nothing for an LLM to extract. Claims are built deterministically; forks excluded (not demonstrated work by this person); tier is uniformly T2 for every included repo (tier reflects verification method, not popularity); source_span points at the real, clickable repo URL — stronger grounding than the text parsers since there's no interpretation step to validate at all. Verified against real accounts (`octocat`, `torvalds`).
- Built `app/generation/title_overview.py`: title + overview generation, grounded by construction like ingestion is. Gemini drafts against the claim set; a validator re-reads every number in the draft against actual claim text before it's allowed through — a number that can't be traced gets the *whole field* withheld (not surgically edited, which risks broken grammar; and not published ungrounded). Tier restriction (overview's proof section must draw only from T1-T4 claims, per Section 3) is enforced structurally in the validator itself — checked against a T1-T4-only text pool regardless of what claim_id the model claims it used — not just left to prompt instruction, matching how every other grounding step in this build works.
- Tested the grounding validator with fake data first (three cases: clean pass, fabricated number correctly rejected, real number from a wrong-tier claim correctly rejected) — zero Gemini calls, per the new discipline. Then spent exactly one real call to prove the LLM step itself works, using hardcoded claims matching real prior output rather than re-parsing CV/Upwork live (that would've spent 2 more calls testing prompts that hadn't changed). Confirmed working: title generated and passed validation; overview correctly withheld because the only concrete stat available came from a T6 (not proof-eligible) claim.
- Wired GitHub parsing and generation into `app/main.py` (generation is additive — if it fails, the score/gap list still render, matching the plan's own fallback ordering). Removed `stub_github_claim` entirely; `app/stub_data.py` now only holds the benchmark re-export and the 5 still-placeholder dimension scores.
- **Ran the actual Phase B checkpoint**: real CV + real GitHub (`torvalds`) + real Upwork paste, through the real browser, producing a real score, real gap list, and an attempted real title/overview. Title and overview were both withheld this run — expected, not a bug: `torvalds`'s profile is a pile of Linux kernel C repos, a poor match for an "AI engineering" title, so there was nothing both title-worthy and traceable to build from. Didn't spend another call chasing this since it's fully explainable from the design.

**Why:**
- Phase B's checkpoint (PROJECT_PLAN.md Section 5) is specifically "CV + GitHub in -> score, gap list, and a rewritten title out" — GitHub pull and generation were both required to actually hit it, not just polish.
- GitHub needing zero Gemini calls is a nice structural fact worth remembering: it's the cheapest source to test freely without touching the new rate-limit discipline at all.

**Next steps:**
- Phase B's checkpoint is met. Remaining Phase B/C items: real persistent storage (currently everything is in-memory per-request, no database), the real 30-profile benchmark (still needs the user), and the four dimensions without a formula (positioning, portfolio_quality, completeness, conversion — pricing_strategy formula also still pending).
- Should re-run the full browser test with a profile that's actually a good fit for the niche (an AI/ML-flavored GitHub account, not `torvalds`) to see a real, non-withheld title/overview — reasonable next real-call spend.
- Not yet committed/pushed to GitHub — do that next.

---

## 2026-09-01 — Provisional benchmark unblocks Phase A; GitHub backup set up; Gemini retry logic added

**What changed:**
- User asked to stop waiting on the real 30-profile benchmark read and instead ship a provisional one now, clearly flagged, editable, replaceable later. Added `provisional: bool` and `source_notes: str` fields to the `Benchmark` schema (`schemas/benchmark.py`) — a structural flag, not just a code comment, so the app itself can show the caveat. Created `benchmarks/ai_ml_engineering_freelance.py`: 14 required terms + synonyms, rate band, dimension targets, all best-guess from general knowledge, `provisional=True`, `sample_size=0`, with an explicit in-file checklist of what to replace once the real read happens. Wired it into `app/stub_data.py` (replacing the old inline 3-term stub) and surfaced a visible warning banner on the results page when the active benchmark is provisional.
- **Set up the GitHub repo** (`github.com/jasondhaki/UpworkGitHUBresumeAI`, public — user's explicit choice after being asked, since visibility is a real consequential decision). `gh` was already authenticated locally; the repo already existed (empty) on GitHub before this session touched it. `git init`, verified `.env` was never staged (checked explicitly before committing — the whole point of the earlier `.gitignore` work), committed everything, pushed to `main`.
- Found and fixed two real reliability issues while re-verifying the walking skeleton after the benchmark swap, both caught by an actual browser/curl test hanging or 500'ing, not by inspection: (1) no error handling around the Gemini calls in `app/main.py` — a timeout or 5xx became a bare 500; added friendly `error.html` responses. (2) Gemini repeatedly returned real 503 "high demand" responses during testing (same message seen during initial model setup, so this is a recurring characteristic of `gemini-3.6-flash`, not a fluke) — added retry-with-backoff (3 attempts) to `app/llm/gemini_client.py`, since a caller can't fix Google-side overload by changing the request. Also bumped the per-call timeout 60s -> 90s (`gemini-3.6-flash` does internal "thinking" before responding, seen in the raw API response's `thoughtsTokenCount` field).
- Re-verified the full path end to end after all of this (CV + Upwork + provisional benchmark + retry logic): real result page, correct provisional-banner text, `keyword_coverage` now reflects the fuller 14-term benchmark (42.9% on the test CV, down from the old 3-term stub's 100% — a more honest number, not a regression).

**Why:**
- A provisional benchmark that's honestly labeled beats staying blocked — the user's call, and a reasonable one: Phase A can keep moving on everything else while the real research happens whenever it happens, and nothing downstream can mistake the placeholder for real data because the flag is structural.
- The 503 pattern showing up repeatedly (not just once) is worth remembering: `gemini-3.6-flash` capacity issues seem to be a real, recurring condition to design around, not a one-off blip.

**Next steps:**
- Phase A's remaining item is unchanged: the real 30-profile competitor benchmark, whenever the user has it — replaces `benchmarks/ai_ml_engineering_freelance.py`'s placeholder values per the upgrade checklist already written into that file.
- Everything is now backed up on GitHub (`main` branch, up to date as of this entry). Future sessions should keep committing/pushing incrementally rather than letting work sit only local — no explicit re-ask needed, this was established as the expected workflow this session.
- Dev server still running locally on port 8000.

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
