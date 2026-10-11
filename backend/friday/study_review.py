"""Load private immutable model responses; keep human judgments separate."""
import json
from datetime import datetime, timezone
from pathlib import Path
from fastapi import HTTPException
from .config import settings


def load_run() -> tuple[dict, list[dict]]:
    try:
        manifest = json.loads(Path(settings.study_manifest_path).read_text(encoding='utf-8'))
        rows = [json.loads(line) for line in Path(settings.study_queue_path).read_text(encoding='utf-8').splitlines() if line.strip()]
    except (OSError, ValueError, TypeError) as exc:
        raise HTTPException(503, 'The private study responses are not installed on this server.') from exc
    if (manifest.get('source_kind') != 'actual_inference' or manifest.get('candidate_system') != 'friday_hosted'
            or not manifest.get('run_id') or not manifest.get('model_id') or not rows):
        raise HTTPException(503, 'The private study run has invalid provenance.')
    ids = [row.get('id') for row in rows]
    if (any(not isinstance(case_id, str) or not case_id for case_id in ids)
            or len(set(ids)) != len(ids)
            or any(not isinstance(row.get('candidate_answer'), str) or not row['candidate_answer'].strip()
                   or row.get('review') is not None for row in rows)):
        raise HTTPException(503, 'The private study run is incomplete or altered.')
    return manifest, rows


def load_ai_triage(manifest: dict, rows: list[dict]) -> dict[str, dict] | None:
    """Read a separate AI issue screen, never human judgments or a score."""
    path = Path(settings.study_ai_triage_path)
    if not path.exists():
        return None
    try:
        triage = [json.loads(line) for line in path.read_text(encoding='utf-8').splitlines() if line.strip()]
    except (OSError, ValueError, TypeError) as exc:
        raise HTTPException(503, 'The private AI triage file cannot be read.') from exc
    by_id = {item.get('id'): item for item in triage if isinstance(item, dict) and isinstance(item.get('id'), str)}
    source = {row['id']: row for row in rows}
    if len(triage) != len(rows) or len(by_id) != len(rows) or set(by_id) != set(source):
        raise HTTPException(503, 'The private AI triage does not match this study run.')
    allowed = {'mismatch', 'incomplete', 'reasoning_issue', 'convention_issue', 'not_flagged'}
    for case_id, item in by_id.items():
        if (item.get('run_id') != manifest['run_id'] or item.get('model_id') != manifest['model_id']
                or item.get('candidate_raw_response_body_sha256') != source[case_id].get('raw_response_body_sha256')
                or item.get('kind') not in allowed or type(item.get('flagged')) is not bool
                or item['flagged'] != (item['kind'] != 'not_flagged')
                or not isinstance(item.get('note'), str) or not item['note'].strip()
                or not isinstance(item.get('screened_by'), str) or not item['screened_by'].strip()
                or not isinstance(item.get('screened_date'), str) or not item['screened_date'].strip()
                or item.get('score') is not None or item.get('model_human_reviewed') is not False
                or item.get('reference_human_verified') is not False):
            raise HTTPException(503, 'The private AI triage has invalid provenance or scoring fields.')
    return {case_id: {key: item[key] for key in ('kind', 'flagged', 'note', 'screened_by', 'screened_date')}
            for case_id, item in by_id.items()}


def review_view(row, user_email: str) -> dict:
    date = datetime.fromtimestamp(row.reviewed_at, timezone.utc).date().isoformat()
    reference = {'status': row.reference_status, 'reviewer': user_email, 'reviewed_at': date,
                 'rationale': row.reference_note}
    answer = {'score': row.score, 'reviewer': user_email, 'reviewed_at': date,
              'rationale': row.rationale} if row.score is not None else None
    return {'reference_review': reference, 'review': answer}
