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

import httpx
from fastapi import FastAPI, Form, Request, UploadFile
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates

from app.generation.title_overview import generate_title_and_overview
from app.ingestion.cv_parser import parse_cv_to_claims
from app.ingestion.file_router import ScannedDocumentError
from app.ingestion.github_parser import GitHubRateLimitError, GitHubUserNotFoundError, parse_github_to_claims
from app.ingestion.upwork_parser import parse_upwork_text_to_claims
from app.scoring.engine import score_profile
from app.storage import get_analysis_run, list_analysis_runs, save_analysis_run, save_uploaded_file
from app.stub_data import STUB_BENCHMARK

app = FastAPI(title="AI5K Profile Intelligence — Phase A skeleton")
templates = Jinja2Templates(directory="app/templates")

GEMINI_UNAVAILABLE_MESSAGE = (
    "The AI extraction step failed after retrying — Gemini is likely under transient load "
    "(we've seen real 503 \"high demand\" responses during this build). This isn't a bug; "
    "wait a bit and try again."
)


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
    cv_claims = []
    if cv_file is not None and cv_file.filename:
        # Persisted, not a temp file that gets deleted after parsing -- a claim's
        # source_span needs to point at a file that still exists later, not just
        # for the duration of this request (Section 2: span grounding needs the
        # original source re-readable at generation time, not just at extraction time).
        stored_path = save_uploaded_file(cv_file.file.read(), cv_file.filename)
        try:
            cv_claims = parse_cv_to_claims(str(stored_path), freelancer_id="fl_stub")
        except ScannedDocumentError as e:
            return templates.TemplateResponse(request, "error.html", {"message": str(e)})
        except (httpx.TimeoutException, httpx.HTTPStatusError):
            return templates.TemplateResponse(request, "error.html", {"message": GEMINI_UNAVAILABLE_MESSAGE})

    try:
        upwork_claims = parse_upwork_text_to_claims(upwork_text, "fl_stub") if upwork_text.strip() else []
    except (httpx.TimeoutException, httpx.HTTPStatusError):
        return templates.TemplateResponse(request, "error.html", {"message": GEMINI_UNAVAILABLE_MESSAGE})

    github_claims = []
    if github_username.strip():
        try:
            github_claims = parse_github_to_claims(github_username.strip(), "fl_stub")
        except GitHubUserNotFoundError as e:
            return templates.TemplateResponse(request, "error.html", {"message": str(e)})
        except GitHubRateLimitError as e:
            return templates.TemplateResponse(request, "error.html", {"message": str(e)})

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
    except (httpx.TimeoutException, httpx.HTTPStatusError):
        pass

    result = score_profile(
        freelancer_id="fl_stub",
        claims=claims,
        benchmark=STUB_BENCHMARK,
        generated=generated,
        stated_rate=parsed_rate,
    )

    run_id = save_analysis_run("fl_stub", claims, result)

    return templates.TemplateResponse(
        request, "result.html", {"result": result, "claims": claims, "benchmark": STUB_BENCHMARK, "run_id": run_id}
    )


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
