"""CV -> Claim records (Phase A: 'a real CV produces real claim records').

Two-stage, matching Section 3's design: Gemini classifies which text blocks
carry evidence and what skills they support (a judgment call); everything
else — the claim's actual text and its source span — comes straight from our
own authoritative block list, never from anything the model wrote. That's
grounding by construction, not just validation after the fact.

Tier assignment is a separate, deterministic, rules-based pass (assign_tier)
— Section 2 makes tiers a rules concern, not a model concern. The rules below
are a first-pass approximation (see the docstring on assign_tier) and are the
most likely thing here to need revisiting once real CVs are run through it.
"""

from datetime import date

from schemas.claim import Claim, EvidenceTier, SourceSpan, SourceType

from .file_router import TextBlock, extract_text_blocks
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

EXTRACTION_PROMPT_TEMPLATE = """You are extracting evidence claims from a freelancer's CV for a \
skills-verification system. There are {num_blocks} numbered text blocks below, extracted from the \
document, indexed 0 to {max_index}.

You MUST evaluate every single block from 0 to {max_index} independently and include one claim \
object in the "claims" array for EVERY block that describes a concrete skill, project, \
certification, or piece of work experience -- a list of short skill_id strings (lowercase, \
underscore-separated, e.g. "vector_databases", "llm_fine_tuning") it supports. Do not stop after \
the first match -- continue checking all remaining blocks. Skip only blocks that are just section \
headers (e.g. "Skills:", "Experience:") or contain no evidence of a skill. A block can support more \
than one skill_id.

{numbered_blocks}
"""


def assign_tier(text: str) -> EvidenceTier:
    """Rules-based, per Section 2 — approximate first pass, not final.

    A CV alone has no external corroboration for anything it claims, so
    strictly nothing here should outrank T6. What this function distinguishes
    is *how* self-reported the phrasing is: a proctored certification claim
    (T4) vs. a badge/course mention (T5) vs. a described role/project (T6,
    treated as employer-confirmed by convention pending real verification —
    Phase 1 doesn't check employment) vs. a bare skill-list mention with no
    supporting context at all (T8, self-declared, matching Section 2's
    definition exactly). Revisit once a batch of real CVs has gone through
    this and the tier distribution can be sanity-checked against them.
    """
    lowered = text.lower()
    if "certif" in lowered and ("proctor" in lowered or "exam" in lowered):
        return EvidenceTier.T4
    if "certif" in lowered or "badge" in lowered:
        return EvidenceTier.T5
    action_words = ("built", "deployed", "led", "shipped", "developed", "designed", "launched", "architected")
    if any(w in lowered for w in action_words) and len(text.split()) > 6:
        return EvidenceTier.T6
    return EvidenceTier.T8


def parse_cv_to_claims(pdf_path: str, freelancer_id: str) -> list[Claim]:
    blocks: list[TextBlock] = extract_text_blocks(pdf_path)  # raises ScannedDocumentError if it's a scan
    if not blocks:
        return []

    numbered = "\n".join(f"[{b.index}] {b.text}" for b in blocks)
    prompt = EXTRACTION_PROMPT_TEMPLATE.format(numbered_blocks=numbered, num_blocks=len(blocks), max_index=len(blocks) - 1)
    result = generate_json(prompt, CLAIM_EXTRACTION_SCHEMA)

    claims: list[Claim] = []
    for i, candidate in enumerate(result.get("claims", [])):
        idx = candidate.get("block_index")
        if not isinstance(idx, int) or idx < 0 or idx >= len(blocks):
            continue  # model returned an out-of-range index — drop it, never guess a span

        block = blocks[idx]
        claims.append(
            Claim(
                claim_id=f"cv_{freelancer_id}_{i}",
                freelancer_id=freelancer_id,
                text=block.text,  # always the real source block — never the model's own phrasing
                skill_ids=candidate.get("skill_ids", []),
                source_type=SourceType.CV,
                source_span=SourceSpan(
                    document_id=str(pdf_path),
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
