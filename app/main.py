"""Walking skeleton — Phase B's checkpoint is met: CV (Docling + Gemini),
Upwork-paste (Gemini), and GitHub (deterministic, no Gemini — see
app/ingestion/github_parser.py) all real, feeding a real scorer, real,
grounding-validated title/overview generation (app/generation/), and now
real persistent storage (app/storage/) instead of everything living only
for the duration of one request.

/analyze is a plain `def`, not `async def`, on purpose: it calls blocking sync
code (Docling, sync HTTP to Gemini/GitHub). An async endpoint runs directly on
FastAPI's single event loop, so blocking work inside it would stall every
other request; a sync `def` endpoint is automatically run in a thread pool by
Starlette instead. Caught this by watching a real request hang past a 30s
Playwright timeout, not by reasoning about it in advance.
"""

import hashlib
import json
import time
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

import httpx
from fastapi import FastAPI, Form, Request, UploadFile
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates

from app.generation.title_overview import generate_title_and_overview
from app.ingestion.cv_parser import parse_cv_to_claims
from app.ingestion.file_router import InvalidDocumentError, ScannedDocumentError
from app.ingestion.github_parser import (
    GitHubRateLimitError,
    GitHubUnavailableError,
    GitHubUserNotFoundError,
    parse_github_to_claims,
)
from app.ingestion.upwork_parser import parse_upwork_text_to_claims
from app.scoring.dimensions import GAP_GUIDANCE
from app.scoring.engine import score_profile
from app.storage import get_analysis_run, list_analysis_runs, save_analysis_run, save_uploaded_file
from app.stub_data import STUB_BENCHMARK

app = FastAPI(title="AI5K Profile Intelligence")
app.mount("/static", StaticFiles(directory="app/static"), name="static")
templates = Jinja2Templates(directory="app/templates")
templates.env.globals["gap_guidance"] = GAP_GUIDANCE

LLM_UNAVAILABLE_MESSAGE = (
    "The AI extraction step failed after retrying — the configured model backend is either "
    "under transient load or unreachable (if LLM_PROVIDER=ollama, check that Ollama is running "
    "locally). This isn't a bug; wait a bit and try again."
)

# Local-demo convenience only: a real end-to-end pass on CPU-only local inference
# can take 10+ minutes for a real multi-page CV, which is fine for one-off testing
# but not for repeatedly showing the same case to someone. Exact-hash match on the
# raw submitted inputs -- never serves a cached result for anything that doesn't
# byte-for-byte match a previously computed run, so this can't silently return a
# stale or wrong result for a genuinely new submission.
DEMO_CACHE_PATH = Path("data/demo_cache.json")

# A cache hit returning in ~0s skips right past the analyzing screen (index.html's
# JS shows it until the page navigates, which happens the instant a response
# arrives) -- for a live demo that looks broken, not fast. This holds the response
# just long enough for that screen's ~10s step animation to actually play out.
DEMO_CACHE_ARTIFICIAL_DELAY_SECONDS = 10


def _demo_cache_key(cv_bytes: bytes | None, github_username: str, upwork_text: str, stated_rate: str) -> str:
    h = hashlib.sha256()
    h.update(cv_bytes or b"")
    h.update(github_username.strip().encode())
    h.update(upwork_text.strip().encode())
    h.update(stated_rate.strip().encode())
    return h.hexdigest()


def _load_demo_cache() -> dict[str, str]:
    if DEMO_CACHE_PATH.exists():
        return json.loads(DEMO_CACHE_PATH.read_text(encoding="utf-8"))
    return {}


def _save_demo_cache_entry(key: str, run_id: str) -> None:
    cache = _load_demo_cache()
    cache[key] = run_id
    DEMO_CACHE_PATH.parent.mkdir(parents=True, exist_ok=True)
    DEMO_CACHE_PATH.write_text(json.dumps(cache, indent=2), encoding="utf-8")


@app.get("/", response_class=HTMLResponse)
def index(request: Request):
    return templates.TemplateResponse(request, "index.html", {})


@app.post("/analyze", response_class=HTMLResponse)
def analyze(
    request: Request,
    cv_file: UploadFile | None = None,
    github_username: str = Form(default=""),
    upwork_text: str = Form(default=""),
    stated_rate: str = Form(default=""),
):
    cv_bytes = cv_file.file.read() if (cv_file is not None and cv_file.filename) else None
    cache_key = _demo_cache_key(cv_bytes, github_username, upwork_text, stated_rate)
    cached_run_id = _load_demo_cache().get(cache_key)
    if cached_run_id:
        cached = get_analysis_run(cached_run_id)
        if cached is not None:
            cached_result, cached_claims = cached
            time.sleep(DEMO_CACHE_ARTIFICIAL_DELAY_SECONDS)
            return templates.TemplateResponse(
                request,
                "result.html",
                {"result": cached_result, "claims": cached_claims, "benchmark": STUB_BENCHMARK, "run_id": cached_run_id},
            )

    # GitHub is a plain network call, independent of CV/Upwork -- kick it off in a
    # background thread now so it overlaps with the CV/Upwork extraction below
    # instead of waiting its turn after them. Those two stay sequential: both hit
    # the same local model, which serializes requests anyway, so parallelizing
    # them wouldn't actually overlap real work, just add complexity.
    github_executor = ThreadPoolExecutor(max_workers=1) if github_username.strip() else None
    github_future = (
        github_executor.submit(parse_github_to_claims, github_username.strip(), "fl_stub") if github_executor else None
    )

    try:
        cv_claims = []
        if cv_bytes is not None:
            # Persisted, not a temp file that gets deleted after parsing -- a claim's
            # source_span needs to point at a file that still exists later, not just
            # for the duration of this request (Section 2: span grounding needs the
            # original source re-readable at generation time, not just at extraction time).
            stored_path = save_uploaded_file(cv_bytes, cv_file.filename)
            try:
                cv_claims = parse_cv_to_claims(str(stored_path), freelancer_id="fl_stub")
            except (ScannedDocumentError, InvalidDocumentError) as e:
                return templates.TemplateResponse(request, "error.html", {"message": str(e)})
            except httpx.HTTPError:  # covers timeouts, connection failures, and bad status codes alike
                return templates.TemplateResponse(request, "error.html", {"message": LLM_UNAVAILABLE_MESSAGE})

        try:
            upwork_claims = parse_upwork_text_to_claims(upwork_text, "fl_stub") if upwork_text.strip() else []
        except httpx.HTTPError:  # covers timeouts, connection failures, and bad status codes alike
            return templates.TemplateResponse(request, "error.html", {"message": LLM_UNAVAILABLE_MESSAGE})

        github_claims = []
        if github_future is not None:
            try:
                github_claims = github_future.result()
            except (GitHubUserNotFoundError, GitHubRateLimitError, GitHubUnavailableError) as e:
                return templates.TemplateResponse(request, "error.html", {"message": str(e)})
    finally:
        if github_executor is not None:
            github_executor.shutdown(wait=False)

    claims = cv_claims + upwork_claims + github_claims

    parsed_rate: float | None = None
    if stated_rate.strip():
        try:
            parsed_rate = float(stated_rate.strip())
        except ValueError:
            return templates.TemplateResponse(
                request, "error.html", {"message": f"'{stated_rate}' isn't a valid hourly rate — enter a number."}
            )

    # Generation runs BEFORE scoring now: positioning/conversion read the generated
    # title/overview (see dimensions.py). Additive, not load-bearing -- if it fails,
    # scoring still proceeds with generated=None (those two dimensions score 0,
    # matching the plan's own fallback: "drop generation, a score and a ranked gap
    # list still proves the concept").
    generated = None
    try:
        generated = generate_title_and_overview(claims, STUB_BENCHMARK.title_formula)
    except httpx.HTTPError:  # covers timeouts, connection failures, and bad status codes alike
        pass

    result = score_profile(
        freelancer_id="fl_stub",
        claims=claims,
        benchmark=STUB_BENCHMARK,
        generated=generated,
        stated_rate=parsed_rate,
    )

    run_id = save_analysis_run("fl_stub", claims, result)
    _save_demo_cache_entry(cache_key, run_id)

    return templates.TemplateResponse(
        request, "result.html", {"result": result, "claims": claims, "benchmark": STUB_BENCHMARK, "run_id": run_id}
    )


@app.get("/benchmark", response_class=HTMLResponse)
def benchmark(request: Request):
    return templates.TemplateResponse(request, "benchmark.html", {"benchmark": STUB_BENCHMARK})


@app.get("/examples", response_class=HTMLResponse)
def examples(request: Request):
    return templates.TemplateResponse(request, "examples.html", {"benchmark": STUB_BENCHMARK})


@app.get("/runs", response_class=HTMLResponse)
def list_runs(request: Request):
    runs = list_analysis_runs("fl_stub")
    return templates.TemplateResponse(request, "runs.html", {"runs": runs})


@app.get("/runs/{run_id}", response_class=HTMLResponse)
def view_run(request: Request, run_id: str):
    fetched = get_analysis_run(run_id)
    if fetched is None:
        return templates.TemplateResponse(request, "error.html", {"message": f"No saved run with id {run_id}."})
    result, claims = fetched
    return templates.TemplateResponse(
        request, "result.html", {"result": result, "claims": claims, "benchmark": STUB_BENCHMARK, "run_id": run_id}
    )
