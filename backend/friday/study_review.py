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


def review_view(row, user_email: str) -> dict:
    date = datetime.fromtimestamp(row.reviewed_at, timezone.utc).date().isoformat()
    reference = {'status': row.reference_status, 'reviewer': user_email, 'reviewed_at': date,
                 'rationale': row.reference_note}
    answer = {'score': row.score, 'reviewer': user_email, 'reviewed_at': date,
              'rationale': row.rationale} if row.score is not None else None
    return {'reference_review': reference, 'review': answer}
