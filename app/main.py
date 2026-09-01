"""Walking skeleton — Phase B's checkpoint is met: CV (Docling + Gemini),
Upwork-paste (Gemini), and GitHub (deterministic, no Gemini — see
app/ingestion/github_parser.py) all real, feeding a real scorer and real,
grounding-validated title/overview generation (app/generation/).

/analyze is a plain `def`, not `async def`, on purpose: it calls blocking sync
code (Docling, sync HTTP to Gemini/GitHub). An async endpoint runs directly on
FastAPI's single event loop, so blocking work inside it would stall every
other request; a sync `def` endpoint is automatically run in a thread pool by
Starlette instead. Caught this by watching a real request hang past a 30s
Playwright timeout, not by reasoning about it in advance.
"""

import tempfile
from pathlib import Path

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
from app.stub_data import STUB_BENCHMARK, STUB_MANUAL_SCORES

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
):
    cv_claims = []
    if cv_file is not None and cv_file.filename:
        suffix = Path(cv_file.filename).suffix or ".pdf"
        with tempfile.NamedTemporaryFile(suffix=suffix, delete=False) as tmp:
            tmp.write(cv_file.file.read())
            tmp_path = tmp.name
        try:
            cv_claims = parse_cv_to_claims(tmp_path, freelancer_id="fl_stub")
        except ScannedDocumentError as e:
            return templates.TemplateResponse(request, "error.html", {"message": str(e)})
        except (httpx.TimeoutException, httpx.HTTPStatusError):
            return templates.TemplateResponse(request, "error.html", {"message": GEMINI_UNAVAILABLE_MESSAGE})
        finally:
            Path(tmp_path).unlink(missing_ok=True)

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

    result = score_profile(
        freelancer_id="fl_stub",
        claims=claims,
        benchmark=STUB_BENCHMARK,
        manual_dimension_scores=STUB_MANUAL_SCORES,
    )

    # Generation is additive, not load-bearing: if it fails, the score and gap list
    # still stand on their own (matches the plan's own fallback: "drop generation,
    # a score and a ranked gap list still proves the concept").
    try:
        result.generated = generate_title_and_overview(claims, STUB_BENCHMARK.title_formula)
    except (httpx.TimeoutException, httpx.HTTPStatusError):
        pass

    return templates.TemplateResponse(
        request, "result.html", {"result": result, "claims": claims, "benchmark": STUB_BENCHMARK}
    )
