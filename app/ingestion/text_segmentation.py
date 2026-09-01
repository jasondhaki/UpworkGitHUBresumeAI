"""Paragraph segmentation for plain-text sources (Upwork/Fiverr paste, etc.) —
no file, no Docling, just exact offsets into the string the user actually
submitted. Shares TextBlock with file_router.py since the shape is identical;
only how blocks get produced differs per source type.
"""

import re

from .file_router import TextBlock


def segment_paragraphs(text: str) -> list[TextBlock]:
    raw_paragraphs = re.split(r"\n\s*\n", text)
    blocks: list[TextBlock] = []
    cursor = 0
    idx = 0
    for para in raw_paragraphs:
        stripped = para.strip()
        if not stripped:
            continue
        start = text.index(stripped, cursor)
        end = start + len(stripped)
        blocks.append(TextBlock(index=idx, start=start, end=end, text=stripped))
        idx += 1
        cursor = end
    return blocks
