"""Walking skeleton (Phase A): the whole path runs from a browser.

CV and Upwork-paste both go through real parsers now (Docling + Gemini for
CV, Gemini alone for the Upwork paste). GitHub is still a stub — Phase B.

/analyze is a plain `def`, not `async def`, on purpose: it calls blocking sync
code (Docling, sync HTTP to Gemini). An async endpoint runs directly on
FastAPI's single event loop, so blocking work inside it would stall every
other request; a sync `def` endpoint is automatically run in a thread pool by
Starlette instead. Caught this by watching a real request hang past a 30s
Playwright timeout, not by reasoning about it in advance.
"""

import tempfile
from pathlib import Path

from fastapi import FastAPI, Form, Request, UploadFile
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates

from app.ingestion.cv_parser import parse_cv_to_claims
from app.ingestion.file_router import ScannedDocumentError
from app.ingestion.upwork_parser import parse_upwork_text_to_claims
from app.scoring.engine import score_profile
from app.stub_data import STUB_BENCHMARK, STUB_MANUAL_SCORES, stub_github_claim

app = FastAPI(title="AI5K Profile Intelligence — Phase A skeleton")
templates = Jinja2Templates(directory="app/templates")


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
        finally:
            Path(tmp_path).unlink(missing_ok=True)

    upwork_claims = parse_upwork_text_to_claims(upwork_text, "fl_stub") if upwork_text.strip() else []
    github_claims = stub_github_claim(github_username)
    claims = cv_claims + upwork_claims + github_claims

    result = score_profile(
        freelancer_id="fl_stub",
        claims=claims,
        benchmark=STUB_BENCHMARK,
        manual_dimension_scores=STUB_MANUAL_SCORES,
    )
    return templates.TemplateResponse(request, "result.html", {"result": result, "claims": claims})
