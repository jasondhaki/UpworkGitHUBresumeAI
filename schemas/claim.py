from datetime import date
from enum import Enum
from typing import Optional

from pydantic import BaseModel, Field, computed_field


class SourceType(str, Enum):
    """Where a claim was extracted from. Section 3 lists nine; Phase 1 only feeds the first three."""

    CV = "cv"
    GITHUB = "github"
    UPWORK_PASTE = "upwork_paste"
    ONBOARDING_FORM = "onboarding_form"  # out of scope for Phase 1
    PORTFOLIO = "portfolio"  # out of scope for Phase 1
    LINKEDIN = "linkedin"  # out of scope for Phase 1
    HUGGING_FACE = "hugging_face"  # out of scope for Phase 1
    DEMO_VIDEO = "demo_video"  # out of scope for Phase 1
    ARTICLE = "article"  # out of scope for Phase 1


class EvidenceTier(str, Enum):
    """Section 2's eight tiers, strongest first."""

    T1 = "T1"  # client-verified outcome
    T2 = "T2"  # project demonstrated
    T3 = "T3"  # platform-assessed
    T4 = "T4"  # certification, proctored
    T5 = "T5"  # certification, badge-only
    T6 = "T6"  # employer-confirmed
    T7 = "T7"  # peer-endorsed
    T8 = "T8"  # self-declared, no corroboration


TIER_WEIGHTS: dict[EvidenceTier, float] = {
    EvidenceTier.T1: 1.00,
    EvidenceTier.T2: 0.85,
    EvidenceTier.T3: 0.80,
    EvidenceTier.T4: 0.75,
    EvidenceTier.T5: 0.55,
    EvidenceTier.T6: 0.50,
    EvidenceTier.T7: 0.30,
    EvidenceTier.T8: 0.15,
}


class SourceSpan(BaseModel):
    """Pointer back to the exact original text a claim came from.

    extracted_text is re-sliced from (start_index, end_index) at parse time,
    never taken from what the model claims it quoted — that's what makes
    grounding real instead of aspirational (PROJECT_PLAN.md line 108).
    """

    document_id: str
    start_index: int
    end_index: int
    extracted_text: str


class Claim(BaseModel):
    claim_id: str
    freelancer_id: str
    text: str
    skill_ids: list[str] = Field(default_factory=list)
    source_type: SourceType
    # None only for claims with no underlying document (e.g. a structured onboarding-form answer) —
    # out of scope for Phase 1, where every claim comes from a real document and must have a span.
    source_span: Optional[SourceSpan] = None
    tier: EvidenceTier
    observed_date: date
    publishable: bool

    @computed_field  # type: ignore[misc]
    @property
    def weight(self) -> float:
        """Derived from tier, never set directly — tier -> weight is a fixed lookup table (Section 2),
        not a per-claim judgment call, so there's nothing here for a bug or a bad prompt to get wrong."""
        return TIER_WEIGHTS[self.tier]
