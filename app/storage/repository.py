"""Save/list/get for analysis runs. One table, deliberately un-normalized
(full Result and claim list stored as JSON blobs) -- this is a demo with one
user and no queries across runs by anything other than freelancer_id, so
normalizing into a claims table with foreign keys would be structure with
no current payoff. Revisit if real cross-run querying becomes a need.
"""

import json
import uuid
from datetime import datetime, timezone

from schemas.claim import Claim
from schemas.result import Result

from .db import get_connection


def save_analysis_run(freelancer_id: str, claims: list[Claim], result: Result) -> str:
    run_id = uuid.uuid4().hex
    conn = get_connection()
    with conn:
        conn.execute(
            "INSERT INTO analysis_runs (run_id, freelancer_id, created_at, result_json, claims_json) "
            "VALUES (?, ?, ?, ?, ?)",
            (
                run_id,
                freelancer_id,
                datetime.now(timezone.utc).isoformat(),
                result.model_dump_json(),
                json.dumps([c.model_dump(mode="json") for c in claims]),
            ),
        )
    conn.close()
    return run_id


def list_analysis_runs(freelancer_id: str) -> list[dict]:
    conn = get_connection()
    rows = conn.execute(
        "SELECT run_id, created_at, result_json FROM analysis_runs WHERE freelancer_id = ? "
        "ORDER BY created_at DESC",
        (freelancer_id,),
    ).fetchall()
    conn.close()

    summaries = []
    for run_id, created_at, result_json in rows:
        result = Result.model_validate_json(result_json)
        summaries.append(
            {"run_id": run_id, "created_at": created_at, "readiness": result.readiness, "capped": result.capped}
        )
    return summaries


def get_analysis_run(run_id: str) -> tuple[Result, list[Claim]] | None:
    conn = get_connection()
    row = conn.execute(
        "SELECT result_json, claims_json FROM analysis_runs WHERE run_id = ?", (run_id,)
    ).fetchone()
    conn.close()

    if row is None:
        return None
    result_json, claims_json = row
    result = Result.model_validate_json(result_json)
    claims = [Claim.model_validate(c) for c in json.loads(claims_json)]
    return result, claims
