import json
from friday.config import settings


def install_run(tmp_path, monkeypatch):
    manifest = tmp_path / 'run-manifest.json'
    queue = tmp_path / 'human-review-queue.jsonl'
    manifest.write_text(json.dumps({'run_id': 'test-friday-run', 'model_id': 'local-fixture',
        'source_kind': 'actual_inference', 'candidate_system': 'friday_hosted',
        'execution_path': 'direct_ollama_api'}), encoding='utf-8')
    queue.write_text(''.join(json.dumps({'id': case_id, 'category': {'name': 'Mechanics'},
        'question': 'What is speed?', 'worked_solution': 'distance / time', 'final_answer': '3 m/s',
        'check_tool': 'calculator', 'candidate_answer': answer, 'review': None,
        'raw_response_body_sha256': case_id}) + '\n' for case_id, answer in (
            ('M01', '3 m/s'), ('M02', '4 m/s'))), encoding='utf-8')
    monkeypatch.setattr(settings, 'study_manifest_path', str(manifest))
    monkeypatch.setattr(settings, 'study_queue_path', str(queue))


def test_owner_review_is_durable_and_raw_answer_unchanged(client, tmp_path, monkeypatch):
    install_run(tmp_path, monkeypatch)
    assert client.get('/api/evaluation/study-pack').status_code == 403
    monkeypatch.setattr(settings, 'owner_email', 'alice@example.com')
    first = client.get('/api/evaluation/study-pack')
    assert first.status_code == 200 and len(first.json()['cases']) == 2
    assert first.json()['cases'][0]['review'] is None
    result = client.post('/api/evaluation/study-pack/M01/review', json={
        'reference_status': 'verified', 'reference_note': 'Checked division and SI units with a calculator',
        'score': 2, 'rationale': 'Correct relation, value, and units'})
    assert result.status_code == 200, result.text
    assert result.json()['review']['reviewer'] == 'alice@example.com'
    after = client.get('/api/evaluation/study-pack').json()
    assert after['cases'][0]['candidate_answer'] == '3 m/s'
    assert after['cases'][0]['review']['score'] == 2
    assert after['cases'][1]['review'] is None
    exported = client.get('/api/evaluation/study-pack/export')
    assert exported.status_code == 200
    rows = [json.loads(line) for line in exported.text.splitlines()]
    assert len(rows) == 2 and rows[0]['reference_review']['status'] == 'verified'
    assert rows[0]['raw_response_body_sha256'] == 'M01'


def test_reference_issue_blocks_score_and_missing_run_fails_closed(client, tmp_path, monkeypatch):
    monkeypatch.setattr(settings, 'owner_email', 'alice@example.com')
    assert client.get('/api/evaluation/study-pack').status_code == 503
    install_run(tmp_path, monkeypatch)
    route = '/api/evaluation/study-pack/M01/review'
    assert client.post(route, json={'reference_status': 'invalid', 'reference_note': 'Bad units',
        'score': 2, 'rationale': 'Looks right'}).status_code == 422
    assert client.post(route, json={'reference_status': 'verified', 'reference_note': 'Checked units',
        'score': None, 'rationale': ''}).status_code == 422
    invalid = client.post(route, json={'reference_status': 'invalid', 'reference_note': 'Bad units'})
    assert invalid.status_code == 200 and invalid.json()['review'] is None
    assert client.post('/api/evaluation/study-pack/UNKNOWN/review', json={
        'reference_status': 'invalid', 'reference_note': 'No case'}).status_code == 404
