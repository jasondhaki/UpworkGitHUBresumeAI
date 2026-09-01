"""Deterministic file classification + native-PDF extraction (Section 3).

Classification happens before any expensive parsing, and a PDF that turns out
to be a scan is rejected loudly rather than silently OCR'd — OCR is out of
scope for Phase 1 (PROJECT_PLAN.md scope fence).

Docling's API was verified live against a real generated PDF before writing
this (see scripts/fixtures_sample_cv.pdf + the inspection session) rather than
assumed from training data — the field moves too fast for that to be safe,
same lesson as the Gemini model mix-up earlier this build.
"""

from dataclasses import dataclass
from enum import Enum
from pathlib import Path

from docling.document_converter import DocumentConverter

MIN_CHARS_PER_ITEM_AVG = 15  # a native doc's text items average far more than this; a scan is ~0


class FileType(str, Enum):
    PDF = "pdf"
    DOCX = "docx"
    UNSUPPORTED = "unsupported"


class ScannedDocumentError(Exception):
    """Raised when a PDF has no meaningfully extractable text — a scan wearing
    a PDF extension. Fail loudly here; do not let silent garbage into claims."""


@dataclass
class TextBlock:
    index: int
    start: int
    end: int
    text: str


SUPPORTED_EXTENSIONS = {".pdf": FileType.PDF, ".docx": FileType.DOCX}

_converter = DocumentConverter()  # loads once, reused across calls — construction is expensive


def classify_file(path: str | Path) -> FileType:
    return SUPPORTED_EXTENSIONS.get(Path(path).suffix.lower(), FileType.UNSUPPORTED)


def extract_text_blocks(path: str | Path) -> list[TextBlock]:
    """Converts a native PDF/DOCX into ordered text blocks with our own, exactly-known
    character offsets into a single concatenated document string — not Docling's internal
    per-item charspans, which are local to each item, not global. We control the join,
    so we control the offsets exactly; this is what source_span grounding stands on.
    """
    file_type = classify_file(path)
    if file_type == FileType.UNSUPPORTED:
        raise ValueError(f"{path}: unsupported file type — Phase 1 only handles PDF and DOCX")

    result = _converter.convert(str(path))
    items = [t for t in result.document.texts if t.text.strip()]

    if not items or (sum(len(t.text) for t in items) / len(items)) < MIN_CHARS_PER_ITEM_AVG:
        raise ScannedDocumentError(
            f"{path}: extracted text looks too sparse to be a native document — this looks like "
            "a scanned PDF. OCR is out of scope for Phase 1; please provide a native (text-based) file."
        )

    blocks: list[TextBlock] = []
    cursor = 0
    for i, item in enumerate(items):
        text = item.text
        start = cursor
        end = start + len(text)
        blocks.append(TextBlock(index=i, start=start, end=end, text=text))
        cursor = end + 1  # +1 accounts for the "\n" join in the reconstructed full text

    return blocks
