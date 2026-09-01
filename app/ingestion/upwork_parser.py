"""Upwork-profile-paste -> Claim records.

Same grounding-by-construction pattern as cv_parser.py: Gemini classifies
which paragraphs carry evidence and what skills they support; claim text and
source span always come from our own paragraph segmentation of the exact
pasted text, never from the model's own wording.

Tier assignment is deliberately more conservative than the CV parser's: an
Upwork profile's project narrative is the freelancer's own unverified sales
copy, not tied to a checkable employer name the way a CV entry is. Only an
actual quoted client testimonial counts as corroborated (T1) — matching
Section 3's framing of Upwork/Fiverr paste as a source of "reviews naming
outcomes". Everything else defaults to T8, even a detailed project
description with hard metrics, because self-reported metrics with no
reviewer, employer, or link behind them are exactly what T8 means.
"""

from datetime import date

from schemas.claim import Claim, EvidenceTier, SourceSpan, SourceType

from .text_segmentation import segment_paragraphs
from app.llm.client import generate_json

CLAIM_EXTRACTION_SCHEMA = {
    "type": "object",
    "properties": {
        "claims": {
            "type": "array",
            "items": {
                "type": "object",
                "properties": {
                    "block_index": {"type": "integer"},
                    "skill_ids": {"type": "array", "items": {"type": "string"}},
                },
                "required": ["block_index", "skill_ids"],
            },
        }
    },
    "required": ["claims"],
}

EXTRACTION_PROMPT_TEMPLATE = """You are extracting evidence claims from a freelancer's pasted \
Upwork profile text for a skills-verification system. There are {num_blocks} numbered paragraph \
blocks below, indexed 0 to {max_index}.

You MUST evaluate every single block from 0 to {max_index} independently and include one claim \
object in the "claims" array for EVERY block that describes a concrete skill, project, client \
outcome, or piece of work experience -- a list of short skill_id strings (lowercase, \
underscore-separated, e.g. "workflow_automation", "api_integration") it supports. Do not stop \
after the first match -- continue checking all remaining blocks. Skip only blocks that are pure \
rate/logistics statements with no skill content (e.g. a standalone "I charge $X/hour" line with \
nothing else in the block).

{numbered_blocks}
"""


def assign_tier(text: str) -> EvidenceTier:
    lowered = text.lower()
    is_quoted_testimonial = '"' in text and any(
        phrase in lowered for phrase in ("client wrote", "client said", "client noted", "one client")
    )
    if is_quoted_testimonial:
        return EvidenceTier.T1
    if "certif" in lowered and ("proctor" in lowered or "exam" in lowered):
        return EvidenceTier.T4
    if "certif" in lowered or "badge" in lowered:
        return EvidenceTier.T5
    return EvidenceTier.T8


def parse_upwork_text_to_claims(upwork_text: str, freelancer_id: str) -> list[Claim]:
    blocks = segment_paragraphs(upwork_text)
    if not blocks:
        return []

    numbered = "\n".join(f"[{b.index}] {b.text}" for b in blocks)
    prompt = EXTRACTION_PROMPT_TEMPLATE.format(numbered_blocks=numbered, num_blocks=len(blocks), max_index=len(blocks) - 1)
    result = generate_json(prompt, CLAIM_EXTRACTION_SCHEMA)

    claims: list[Claim] = []
    for i, candidate in enumerate(result.get("claims", [])):
        idx = candidate.get("block_index")
        if not isinstance(idx, int) or idx < 0 or idx >= len(blocks):
            continue

        block = blocks[idx]
        claims.append(
            Claim(
                claim_id=f"upwork_{freelancer_id}_{i}",
                freelancer_id=freelancer_id,
                text=block.text,
                skill_ids=candidate.get("skill_ids", []),
                source_type=SourceType.UPWORK_PASTE,
                source_span=SourceSpan(
                    document_id=f"upwork_paste:{freelancer_id}",
                    start_index=block.start,
                    end_index=block.end,
                    extracted_text=block.text,
                ),
                tier=assign_tier(block.text),
                observed_date=date.today(),
                publishable=True,
            )
        )
    return claims
