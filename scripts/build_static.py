"""Renders the marketing pages (index, benchmark, examples) to static HTML for
GitHub Pages. No FastAPI, no Gemini, no SQLite -- Pages only serves flat files,
so /analyze and /runs (which need a live backend) are dropped: index.html
shows a "static preview, run locally" card instead of the live upload form,
and the "Past cases" nav link is hidden. Everything else (benchmark, examples,
the 8-tier chain, all real benchmark data) renders identically to the live app
since they all read the same STUB_BENCHMARK and the same templates.

Re-run this after any template/CSS change meant to reach the deployed site --
it's a build step, not something the live app calls.
"""

import shutil
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from jinja2 import Environment, FileSystemLoader  # noqa: E402

from app.stub_data import STUB_BENCHMARK  # noqa: E402

BASE_PATH = "/UpworkGitHUBresumeAI"  # GitHub Pages project-site subpath
OUT_DIR = ROOT / "docs"

env = Environment(loader=FileSystemLoader(str(ROOT / "app" / "templates")))

PAGES = {
    "index.html": {},
    "benchmark.html": {"benchmark": STUB_BENCHMARK},
    "examples.html": {"benchmark": STUB_BENCHMARK},
}


def build() -> None:
    if OUT_DIR.exists():
        shutil.rmtree(OUT_DIR)
    OUT_DIR.mkdir(parents=True)

    for template_name, context in PAGES.items():
        template = env.get_template(template_name)
        html = template.render(base_path=BASE_PATH, static_mode=True, **context)
        (OUT_DIR / template_name).write_text(html, encoding="utf-8")
        print(f"wrote docs/{template_name}")

    static_out = OUT_DIR / "static"
    static_out.mkdir()
    shutil.copy(ROOT / "app" / "static" / "style.css", static_out / "style.css")
    print("copied docs/static/style.css")

    (OUT_DIR / ".nojekyll").write_text("", encoding="utf-8")


if __name__ == "__main__":
    build()
