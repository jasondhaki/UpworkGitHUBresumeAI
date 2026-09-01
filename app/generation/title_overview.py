"""Title + overview generation, grounded by construction the same way ingestion
is: Gemini drafts against the claim set, then a validator re-reads every number
in the draft against the actual claim text before it's allowed through.

If any number in a draft can't be traced to allowed source material, the whole
field is withheld rather than published un-grounded or surgically edited —
editing free text to remove one number risks grammatically broken output;
withholding is the safe default. This is Section 3's "a claim with no source
span is never published; it becomes a coaching prompt instead" applied at
field granularity, which is the right grain for this build's scope.

Tier restriction is enforced structurally, not just by prompt instruction:
the overview's numbers are validated ONLY against T1-T4 claim text (Section 3:
"Proof section drawn only from T1-T4 claims"), regardless of which claim_id
the model claims it used — so even a model that miscites a weak claim can't
sneak an ungrounded number through as long as validation itself is honest.
Title has no tier restriction (any claim's span is enough), matching Section 3.
"""

import re

from schemas.claim import Claim, EvidenceTier
from schemas.result import GeneratedContent, GeneratedField, SourceSpanRef

from app.llm.client import generate_json

PROOF_ELIGIBLE_TIERS = {EvidenceTier.T1, EvidenceTier.T2, EvidenceTier.T3, EvidenceTier.T4}

GENERATION_SCHEMA = {
    "type": "object",
    "properties": {
        "title": {
            "type": "object",
            "properties": {
                "text": {"type": "string"},
                "supporting_claim_ids": {"type": "array", "items": {"type": "string"}},
            },
            "required": ["text", "supporting_claim_ids"],
        },
        "overview": {
            "type": "object",
            "properties": {
                "text": {"type": "string"},
                "supporting_claim_ids": {"type": "array", "items": {"type": "string"}},
            },
            "required": ["text", "supporting_claim_ids"],
        },
    },
    "required": ["title", "overview"],
}

# Matches things like "10", "10,000", "60%", "3.5" -- deliberately broad; false
# positives (e.g. a bare year) just mean a slightly stricter grounding check,
# which is the safe direction to err in for this product.
NUMBER_PATTERN = re.compile(r"\d[\d,]*\.?\d*%?")


def _numbers_in(text: str) -> set[str]:
    return set(NUMBER_PATTERN.findall(text))


def _validate_and_build(
    text: str,
    cited_claim_ids: list[str],
    claims_by_id: dict[str, Claim],
    allowed_claims: list[Claim],
) -> GeneratedField | None:
    if not text.strip() or not allowed_claims:
        return None

    allowed_ids = {c.claim_id for c in allowed_claims}
    source_text_pool = " ".join(c.text for c in allowed_claims)

    untraceable = _numbers_in(text) - _numbers_in(source_text_pool)
    if untraceable:
        return None  # a number in the draft isn't backed by any allowed claim -- withhold

    cited_claims = [claims_by_id[cid] for cid in cited_claim_ids if cid in claims_by_id and cid in allowed_ids]
    if not cited_claims:
        return None  # model cited nothing valid -- nothing to point the reader at

    spans = [
        SourceSpanRef(
            claim_id=c.claim_id,
            document_id=c.source_span.document_id if c.source_span else "",
            start_index=c.source_span.start_index if c.source_span else 0,
            end_index=c.source_span.end_index if c.source_span else 0,
        )
        for c in cited_claims
    ]
    return GeneratedField(text=text, source_spans=spans)


def generate_title_and_overview(claims: list[Claim], title_formula: str) -> GeneratedContent:
    if not claims:
        return GeneratedContent()

    claims_by_id = {c.claim_id: c for c in claims}
    proof_eligible = [c for c in claims if c.tier in PROOF_ELIGIBLE_TIERS]

    all_claims_block = "\n".join(f"[{c.claim_id}] (tier {c.tier.value}) {c.text}" for c in claims)
    proof_block = (
        "\n".join(f"[{c.claim_id}] (tier {c.tier.value}) {c.text}" for c in proof_eligible)
        or "(none available -- do not include any proof claims or numbers in the overview)"
    )

    prompt = f"""You are writing a freelancer's Upwork title and profile overview for an AI \
skills-verification product. Use ONLY facts and numbers literally present in the claims below \
-- never invent, estimate, or round a number that isn't already stated in a claim.

Title formula to follow: {title_formula}

Overview structure: a hook naming the buyer's problem, then proof, then a short description of \
process, then a call to action. The proof section may draw numbers/facts ONLY from these \
strongest, most verifiable claims (tiers T1-T4):
{proof_block}

All available claims (for general skill/context mentions elsewhere in the overview, NOT for \
proof-section numbers):
{all_claims_block}

For both title and overview, return supporting_claim_ids listing exactly which claim_id(s) back \
every specific number or fact you included. If you cannot write a proof section with real \
numbers from the T1-T4 claims above, write the overview without one rather than inventing a stat.
"""
    result = generate_json(prompt, GENERATION_SCHEMA)

    title_field = _validate_and_build(
        result["title"]["text"], result["title"]["supporting_claim_ids"], claims_by_id, allowed_claims=claims
    )
    overview_field = _validate_and_build(
        result["overview"]["text"],
        result["overview"]["supporting_claim_ids"],
        claims_by_id,
        allowed_claims=proof_eligible,
    )
    return GeneratedContent(title=title_field, overview=overview_field)
