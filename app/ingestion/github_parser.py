"""GitHub username -> Claim records. Zero Gemini calls, by design.

Unlike CV/Upwork text, GitHub's API already returns structured facts (stars,
language, push dates) — there's no unstructured prose to interpret, so there's
nothing for an LLM to extract. Claims are built deterministically straight
from the API response. This also means grounding here is stronger than the
text-based parsers': the source_span points at a real, clickable repo URL,
not a byte range picked out of a document — the claim is directly verifiable,
not just traceable.

Forks are excluded: a fork isn't demonstrated work by this person unless
meaningfully modified, which the API alone can't tell us — excluding is the
conservative call, matching the "no claim without real backing" principle.

Tier is T2 ("project demonstrated: deployed repository...") for every
included repo, uniformly — tier reflects verification method, not
popularity. Stars/recency are facts carried in the claim text and available
to portfolio_quality scoring later, not a tier upgrade.
"""

import os
from datetime import date, datetime

import httpx

from schemas.claim import Claim, EvidenceTier, SourceSpan, SourceType

GITHUB_API_BASE = "https://api.github.com"
MAX_REPOS = 10  # cap claim count for prolific users; ranked by stars first


class GitHubUserNotFoundError(Exception):
    pass


class GitHubRateLimitError(Exception):
    pass


def _headers() -> dict:
    headers = {"Accept": "application/vnd.github+json", "User-Agent": "ai5k-profile-intelligence"}
    token = os.environ.get("GITHUB_TOKEN")
    if token:
        headers["Authorization"] = f"Bearer {token}"
    return headers


def _fetch_repos(username: str) -> list[dict]:
    resp = httpx.get(
        f"{GITHUB_API_BASE}/users/{username}/repos",
        params={"sort": "pushed", "per_page": 100},
        headers=_headers(),
        timeout=30.0,
    )
    if resp.status_code == 404:
        raise GitHubUserNotFoundError(f"GitHub user '{username}' not found")
    if resp.status_code == 403 and "rate limit" in resp.text.lower():
        raise GitHubRateLimitError(
            "GitHub API rate limit hit (60/hour unauthenticated). Set GITHUB_TOKEN to raise it to 5000/hour."
        )
    resp.raise_for_status()
    return resp.json()


def parse_github_to_claims(username: str, freelancer_id: str) -> list[Claim]:
    repos = _fetch_repos(username)
    non_forks = [r for r in repos if not r.get("fork")]
    top_repos = sorted(non_forks, key=lambda r: r.get("stargazers_count", 0), reverse=True)[:MAX_REPOS]

    claims: list[Claim] = []
    for repo in top_repos:
        name = repo["name"]
        language = repo.get("language")
        stars = repo.get("stargazers_count", 0)
        description = repo.get("description")
        pushed_at = repo.get("pushed_at")
        topics = repo.get("topics", []) or []
        html_url = repo["html_url"]

        pushed_date = datetime.fromisoformat(pushed_at.replace("Z", "+00:00")).date() if pushed_at else date.today()

        desc_part = f"{description} - " if description else ""
        lang_part = f"primary language {language}, " if language else ""
        text = (
            f"Repository '{name}': {desc_part}{lang_part}{stars} star"
            f"{'s' if stars != 1 else ''}, last updated {pushed_date.isoformat()}."
        )

        skill_ids = []
        if language:
            skill_ids.append(language.lower().replace(" ", "_"))
        skill_ids.extend(t.lower().replace("-", "_") for t in topics)

        claims.append(
            Claim(
                claim_id=f"github_{freelancer_id}_{name}",
                freelancer_id=freelancer_id,
                text=text,
                skill_ids=skill_ids,
                source_type=SourceType.GITHUB,
                source_span=SourceSpan(
                    document_id=html_url,
                    start_index=0,
                    end_index=len(text),
                    extracted_text=text,
                ),
                tier=EvidenceTier.T2,
                observed_date=pushed_date,
                publishable=True,
            )
        )

    return claims
