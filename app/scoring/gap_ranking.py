"""Section 2's gap ranking formula, plus the three rules from Section 3:
blocking items are excluded entirely (handled elsewhere, not here), dependencies
gate what's shown, and the top five stays balanced rather than pure ROI-sorted.
"""

from schemas.result import DimensionScore, Gap

from .efficacy import DEFAULT_EFFICACY, DEFAULT_EFFORT_HOURS, EFFICACY, EFFORT_HOURS

# "no title rewrite before a vertical is chosen; no pricing advice before evidence
# exists to justify a rate" (Section 3) — encoded as: a dimension in this dict can't
# surface as a gap until every listed prerequisite has reached DEPENDENCY_THRESHOLD
# of its own target.
DEPENDENCIES: dict[str, list[str]] = {
    "pricing_strategy": ["evidence_quality"],
    "conversion": ["positioning"],
}
DEPENDENCY_THRESHOLD = 0.5


def compute_gaps(dimensions: dict[str, DimensionScore]) -> list[Gap]:
    gaps: list[Gap] = []
    for name, d in dimensions.items():
        if d.current >= d.target:
            continue

        prereqs = DEPENDENCIES.get(name, [])
        gated = any(
            dimensions[p].current < dimensions[p].target * DEPENDENCY_THRESHOLD
            for p in prereqs
            if p in dimensions
        )
        if gated:
            continue

        efficacy = EFFICACY.get(name, DEFAULT_EFFICACY)
        effort_hours = EFFORT_HOURS.get(name, DEFAULT_EFFORT_HOURS)

        gain = d.weight * (d.target - d.current) * efficacy
        priority = gain / max(effort_hours, 0.5)

        gaps.append(
            Gap(
                dimension=name,
                current=d.current,
                target=d.target,
                gain=round(gain, 2),
                effort_hours=effort_hours,
                priority=round(priority, 3),
            )
        )

    return sorted(gaps, key=lambda g: g.priority, reverse=True)


def select_top_five(gaps: list[Gap]) -> list[Gap]:
    """Top 3 by priority + the single largest available gain regardless of effort +
    anything blocking (blocking items live in Result.blocking, not passed in here).
    Prevents the list from filling permanently with five-minute fixes (Section 3)."""
    if not gaps:
        return []

    ranked = sorted(gaps, key=lambda g: g.priority, reverse=True)
    selected = list(ranked[:3])

    largest_gain = max(gaps, key=lambda g: g.gain)
    if largest_gain not in selected:
        selected.append(largest_gain)

    return selected
