"""Cross-source skill consistency check -- a skill being TRUE in one source
doesn't mean it's PRESENTED everywhere it should be. Two separate checks,
both driven by the same simple substring/synonym text matching
compute_keyword_coverage already uses (not embeddings, not fuzzy NLP):

1. Benchmark-required terms: for each term this niche's benchmark expects, is
   it demonstrated on GitHub, mentioned in the CV, and/or mentioned in the
   Upwork profile text? A term missing everywhere is a real gap against the
   niche standard; one demonstrated on GitHub but never mentioned in the
   Upwork text is a presentation gap, not a skill gap -- different problems,
   different fixes.
2. Self-claimed skills outside the benchmark: skill_ids the CV/Upwork
   extraction itself identified that aren't in the required-term list at all
   (e.g. "Next.js" against an AI/ML-niche benchmark) still deserve the same
   proven-vs-advertised check, just without a "required for this niche" label.

This is a coaching aid, not a guarantee: a skill phrased very differently
across three independently-extracted sources can still be missed, and GitHub
evidence is currently only as deep as package.json dependencies for JS/TS
repos (see github_parser.py) -- a Python project's real dependencies aren't
inspected the same way.
"""

from dataclasses import dataclass

from schemas.benchmark import Benchmark
from schemas.claim import Claim, SourceType

STATUS_MISSING = "missing"
STATUS_UNPROVEN = "claimed_unproven"
STATUS_UNADVERTISED = "demonstrated_not_advertised"
STATUS_COVERED = "well_covered"

# Prefixes the CV/Upwork extraction model commonly prepends to a skill_id (e.g.
# "web_development_next_js") that would otherwise stop it from matching the
# same skill's bare mention elsewhere ("next", "nextjs").
_CATEGORY_PREFIXES = [
    "web_development_", "mobile_application_development_", "programming_languages_",
    "ai_model_", "database_", "hardware_", "frameworks_libraries_", "tools_platforms_",
    "serverless_", "query_language_", "headless_cms_", "cad_software_", "code_editor_",
    "version_control_", "embedded_systems_", "android_", "robotics_",
]


@dataclass
class SkillStatus:
    name: str
    required: bool  # came from the niche benchmark's required terms, not self-claimed
    on_cv: bool
    on_github: bool
    on_upwork: bool
    status: str
    guidance: str


# Cosmetic only: normalization is lowercase/underscore-stripped for matching,
# but a few extremely common tokens look wrong title-cased verbatim ("Next Js").
_DISPLAY_NAMES = {
    "next": "Next.js", "next js": "Next.js", "nextjs": "Next.js",
    "typescript": "TypeScript", "javascript": "JavaScript", "nodejs": "Node.js",
    "node": "Node.js", "graphql": "GraphQL", "postgresql": "PostgreSQL",
    "mongodb": "MongoDB", "tailwindcss": "Tailwind CSS", "fastapi": "FastAPI",
    "vuejs": "Vue.js", "nextauth": "NextAuth",
}


def _display_name(normalized: str) -> str:
    return _DISPLAY_NAMES.get(normalized, normalized.title())


# Bare category labels with nothing specific after them (e.g. a skill_id of
# just "frameworks_libraries", not "frameworks_libraries_next_js") aren't a real
# skill -- normalizing one would otherwise leave the category name itself
# ("frameworks libraries") looking exactly like a legitimate row.
_BARE_CATEGORY_LABELS = {p.rstrip("_").replace("_", " ") for p in _CATEGORY_PREFIXES}


def _normalize(skill_id: str) -> str:
    s = skill_id.lower()
    for prefix in _CATEGORY_PREFIXES:
        if s.startswith(prefix):
            s = s[len(prefix):]
            break
    normalized = s.replace("_", " ").replace("-", " ").strip()
    return "" if normalized in _BARE_CATEGORY_LABELS else normalized


def _claims_by_source(claims: list[Claim]) -> dict[SourceType, list[Claim]]:
    by_source: dict[SourceType, list[Claim]] = {SourceType.CV: [], SourceType.GITHUB: [], SourceType.UPWORK_PASTE: []}
    for c in claims:
        if c.source_type in by_source:
            by_source[c.source_type].append(c)
    return by_source


def _source_text(source_claims: list[Claim]) -> str:
    parts = []
    for c in source_claims:
        parts.append(c.text.lower())
        parts.extend(_normalize(sid) for sid in c.skill_ids)
    return " ".join(parts)


def _term_present(term: str, synonyms: list[str], text: str) -> bool:
    candidates = [term.lower(), *[s.lower() for s in synonyms]]
    return any(candidate in text for candidate in candidates)


def _classify(name: str, required: bool, on_cv: bool, on_github: bool, on_upwork: bool) -> SkillStatus:
    """GitHub presence is checked first, not "CV or Upwork" combined: the target
    artifact this whole audit is built around is the Upwork Skills section (per
    the feature request), so a skill can be perfectly real (on_github=True,
    on_cv=True) and still need action if it's specifically missing from Upwork --
    that's a different problem (an advertising gap) than a skill that's written
    down nowhere real backs up (an evidence gap, on_github=False)."""
    if on_github:
        if on_upwork:
            status = STATUS_COVERED
            guidance = "Proven by a real GitHub project and already listed on Upwork — no action needed."
        else:
            status = STATUS_UNADVERTISED
            guidance = "A GitHub repo proves this skill, but it's not in your Upwork profile — add it to your Upwork Skills section so it's actually findable."
    elif on_cv or on_upwork:
        status = STATUS_UNPROVEN
        guidance = "Claimed in your CV or Upwork text, but no GitHub project backs it up — build and publish something that uses it."
    else:
        status = STATUS_MISSING
        guidance = "Not mentioned anywhere, and nothing on GitHub demonstrates it. This niche's top profiles consistently show it — worth learning it or building a project around it."
    return SkillStatus(name=name, required=required, on_cv=on_cv, on_github=on_github, on_upwork=on_upwork, status=status, guidance=guidance)


def audit_required_terms(claims: list[Claim], benchmark: Benchmark) -> list[SkillStatus]:
    by_source = _claims_by_source(claims)
    cv_text = _source_text(by_source[SourceType.CV])
    github_text = _source_text(by_source[SourceType.GITHUB])
    upwork_text = _source_text(by_source[SourceType.UPWORK_PASTE])

    results = []
    for rt in benchmark.required_terms:
        on_cv = _term_present(rt.term, rt.synonyms, cv_text)
        on_github = _term_present(rt.term, rt.synonyms, github_text)
        on_upwork = _term_present(rt.term, rt.synonyms, upwork_text)
        results.append(_classify(rt.term, True, on_cv, on_github, on_upwork))
    return results


def audit_claimed_skills(claims: list[Claim], benchmark: Benchmark) -> list[SkillStatus]:
    """Unlike audit_required_terms (a fixed 24-ish rows, always shown in full --
    that's the "how do I fit this niche" picture), this list is open-ended: a
    resume with many small projects can easily produce 40+ distinct skill_ids.
    STATUS_COVERED entries (claimed AND proven, nothing to do) are dropped
    before returning -- they'd otherwise dominate the list with rows that need
    no action, burying the ones that do."""
    by_source = _claims_by_source(claims)
    github_tokens = {
        norm
        for c in by_source[SourceType.GITHUB]
        for sid in c.skill_ids
        if (norm := _normalize(sid)) and len(norm) >= 2
    }
    required_normalized = {rt.term.lower() for rt in benchmark.required_terms}
    required_normalized |= {s.lower() for rt in benchmark.required_terms for s in rt.synonyms}

    seen: dict[str, dict[str, bool]] = {}
    for source_type in (SourceType.CV, SourceType.UPWORK_PASTE):
        for c in by_source[source_type]:
            for sid in c.skill_ids:
                norm = _normalize(sid)
                if len(norm) < 2 or norm in required_normalized:
                    continue  # already covered by the required-term audit above
                entry = seen.setdefault(norm, {"on_cv": False, "on_upwork": False})
                if source_type == SourceType.CV:
                    entry["on_cv"] = True
                else:
                    entry["on_upwork"] = True

    results = []
    for norm_name, flags in seen.items():
        on_github = any(token == norm_name or token in norm_name or norm_name in token for token in github_tokens)
        status = _classify(_display_name(norm_name), False, flags["on_cv"], on_github, flags["on_upwork"])
        if status.status != STATUS_COVERED:
            results.append(status)
    return results


def audit_skills(claims: list[Claim], benchmark: Benchmark) -> list[SkillStatus]:
    """Required terms first (the niche standard), then the user's own claimed
    skills outside that list -- both sorted problems-first so the things
    needing action surface before the ones already in good shape."""
    order = {STATUS_MISSING: 0, STATUS_UNPROVEN: 1, STATUS_UNADVERTISED: 2, STATUS_COVERED: 3}
    required = sorted(audit_required_terms(claims, benchmark), key=lambda s: order[s.status])
    claimed = sorted(audit_claimed_skills(claims, benchmark), key=lambda s: order[s.status])
    return required + claimed
