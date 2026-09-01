"""Persistent storage for original uploaded files (Section 2: "original source
files are retained... because grounding means re-reading the source at
generation time"). Local disk, not cloud object storage -- free-tier demo
scope, swap for real object storage later if this needs to survive beyond
one machine.

This fixes a real gap: until now, uploaded CVs were written to a
NamedTemporaryFile and deleted right after parsing, so a claim's source_span
pointed at a file that no longer existed the moment the request finished --
span grounding was real only during the request, not after. Now it persists.
"""

import uuid
from pathlib import Path

STORAGE_DIR = Path("data/files")
STORAGE_DIR.mkdir(parents=True, exist_ok=True)


def save_uploaded_file(content: bytes, original_filename: str) -> Path:
    suffix = Path(original_filename).suffix or ".bin"
    dest = STORAGE_DIR / f"{uuid.uuid4().hex}{suffix}"
    dest.write_bytes(content)
    return dest
