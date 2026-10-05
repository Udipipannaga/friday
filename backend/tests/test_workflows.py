import json
import time
from concurrent.futures import ThreadPoolExecutor
from fastapi.testclient import TestClient
from sqlalchemy import select
from sqlalchemy.orm import sessionmaker
from friday import db, execution, providers, retrieval
from friday.api import app
from friday.config import settings


class TestModel:
    __test__ = False
    calls = 0
    def complete(self, messages, on_text):
        self.calls += 1
        if 'ONLY JSON' in messages[0]['content']:
            text = json.dumps({'findings': [{'claim': 'The source describes a durable research workflow.', 'source': 1, 'evidence': 'durable research workflow'}], 'gaps': 'This fixture uses one source and is not a live provider test.'})
        else:
            text = 'TEST FIXTURE RESPONSE: ' + messages[-1]['content']
        on_text(text)
        return providers.Result(text, 25, 40)


def submit(client, kind='research', key=None):
    payload = {'text': 'How does durable research work?', 'request_key': key or db.uid()}
    if kind == 'chat':
        c = client.post('/api/conversations', json={}).json()
        result = client.post(f'/api/conversations/{c["id"]}/messages', json=payload)
    else:
        result = client.post('/api/projects', json=payload)
    assert result.status_code == 202, result.text
    return result.json()['id']


def run(job_id, model=None):
    execution.run_job(job_id, provider=model or TestModel(), search=lambda q: ['https://example.org/research'],
        fetch=lambda u: retrieval.Page(u, 'Fixture source', 'A durable research workflow persists source evidence and project state. ' * 4))


def test_conversation_survives_engine_restart(client, monkeypatch):
    job_id = submit(client, 'chat')
    run(job_id)
    with db.Session() as s:
        cid = s.get(db.Job, job_id).conversation_id
    url = str(db.engine.url)
    db.engine.dispose()
    engine2 = db.make_engine(url)
    monkeypatch.setattr(db, 'Session', sessionmaker(engine2))
    result = client.get('/api/conversations/' + cid).json()
    assert [m['role'] for m in result['messages']] == ['user', 'assistant']
    assert 'TEST FIXTURE' in result['messages'][1]['text']
    engine2.dispose()


def test_research_returns_quickly_and_runs_without_client(client):
    start = time.monotonic()
    job_id = submit(client)
    assert time.monotonic() - start < 1
    assert client.get('/api/jobs/' + job_id).json()['status'] == 'queued'
    client.close()
    run(job_id)
    with db.Session() as s:
        assert s.get(db.Job, job_id).status == 'succeeded'
        report = s.scalar(select(db.Artifact).where(db.Artifact.job_id == job_id)).content
        assert 'https://example.org/research' in report
        assert 'Retrieved sources' in report


def test_cross_account_isolation(client):
    job_id = submit(client, 'chat')
    with db.Session() as s:
        cid = s.get(db.Job, job_id).conversation_id
    with TestClient(app, headers={'Origin':'http://testserver','X-Friday-Request':'1'}) as other:
        assert other.post('/api/auth/register', json={'email':'bob@example.com','password':'another-test-password'}).status_code == 201
        for path in [f'/api/jobs/{job_id}',f'/api/jobs/{job_id}/report',f'/api/conversations/{cid}']:
            assert other.get(path).status_code == 404
        assert other.post(f'/api/jobs/{job_id}/cancel').status_code == 404
        assert other.post(f'/api/conversations/{cid}/messages', json={'text':'attack','request_key':db.uid()}).status_code == 404


def test_missing_credentials_are_explicit(client, monkeypatch):
    monkeypatch.setattr(settings, 'api_key', '')
    r = client.post('/api/projects', json={'text':'question','request_key':db.uid()})
    assert r.status_code == 503
    assert 'FRIDAY_API_KEY' in r.json()['detail']
    assert client.get('/api/me').json()['jobs_today'] == 0


def test_duplicate_submission_and_changed_parameters(client):
    key = db.uid()
    first = submit(client, key=key)
    assert submit(client, key=key) == first
    assert client.get('/api/me').json()['jobs_today'] == 1
    r = client.post('/api/projects', json={'text':'changed','request_key':key})
    assert r.status_code == 409


def test_cancel_prevents_steps(client):
    job_id = submit(client)
    client.post('/api/jobs/' + job_id + '/cancel')
    model = TestModel()
    run(job_id, model)
    assert model.calls == 0
    assert client.get('/api/jobs/' + job_id).json()['status'] == 'cancelled'


def test_cancel_during_fetch_does_not_commit_or_call_model(client):
    job_id = submit(client)
    model = TestModel()
    def fetch(url):
        client.post('/api/jobs/' + job_id + '/cancel')
        return retrieval.Page(url, 'Cancelled', 'durable research workflow ' * 10)
    execution.run_job(job_id, provider=model, search=lambda q:['https://example.org'], fetch=fetch)
    assert model.calls == 0
    detail = client.get('/api/jobs/' + job_id).json()
    assert detail['status'] == 'cancelled' and detail['sources'] == []


def test_expired_worker_resumes_completed_retrieval(client):
    job_id = submit(client)
    with db.Session.begin() as s:
        j = s.get(db.Job, job_id)
        j.stage, j.status, j.lease, j.lease_until = 'fetch', 'running', 'dead-worker', 1
        j.checkpoint = {'urls':['https://example.org/research']}
        s.add(db.Source(job_id=job_id, position=1, url='https://example.org/research', title='Saved evidence', text='A durable research workflow is recoverable.'))
    def forbidden(*args):
        raise AssertionError('Completed retrieval was repeated')
    execution.run_job(job_id, provider=TestModel(), search=forbidden, fetch=forbidden)
    assert client.get('/api/jobs/' + job_id).json()['status'] == 'succeeded'


def test_concurrent_claim_only_one_wins(client):
    job_id = submit(client)
    with ThreadPoolExecutor(max_workers=2) as pool:
        results = list(pool.map(execution.claim, [job_id,job_id]))
    assert sum(r is not None for r in results) == 1


def test_stale_worker_cannot_write(client):
    job_id = submit(client)
    old = execution.claim(job_id)
    with db.Session.begin() as s:
        s.get(db.Job, job_id).lease_until = 0
    assert execution.claim(job_id) != old
    try:
        execution.checkpoint(job_id, old, lambda s,j:setattr(j,'partial','stale'))
        assert False
    except execution.LostLease:
        pass


def test_search_retries_bounded(client):
    job_id = submit(client)
    def fail(q):
        raise retrieval.RetrievalError('Search unavailable')
    for _ in range(5):
        execution.run_job(job_id, provider=TestModel(), search=fail)
        with db.Session.begin() as s:
            s.get(db.Job, job_id).available = 0
    detail = client.get('/api/jobs/' + job_id).json()
    assert detail['status'] == 'failed' and detail['attempts'] == 3


def test_uncertain_model_call_not_replayed(client):
    job_id = submit(client, 'chat')
    with db.Session.begin() as s:
        j = s.get(db.Job, job_id)
        j.stage = 'model'
        s.add(db.Usage(job_id=job_id, provider='test', model='test'))
    model = TestModel()
    run(job_id, model)
    detail = client.get('/api/jobs/' + job_id).json()
    assert detail['status'] == 'failed' and 'uncertain' in detail['error']
    assert model.calls == 0 and detail['usage']['status'] == 'uncertain'


def test_completed_model_output_recovers_without_another_call(client):
    job_id = submit(client, 'chat')
    with db.Session.begin() as s:
        j = s.get(db.Job, job_id)
        j.stage = 'finalize'
        j.checkpoint = {'model_output':'Already saved response'}
    model = TestModel()
    run(job_id, model)
    assert model.calls == 0
    assert client.get('/api/jobs/' + job_id).json()['status'] == 'succeeded'


def test_fabricated_citation_rejected(client):
    class BadModel(TestModel):
        def complete(self, messages, on_text):
            return providers.Result(json.dumps({'findings':[{'claim':'Invented','source':99,'evidence':'made up text'}],'gaps':'none'}))
    job_id = submit(client)
    run(job_id, BadModel())
    detail = client.get('/api/jobs/' + job_id).json()
    assert detail['status'] == 'failed' and detail['artifact'] is None


def test_inaccessible_sources_never_synthesized(client):
    def fail(url):
        raise retrieval.RetrievalError('Source unavailable')
    job_id = submit(client)
    model = TestModel()
    execution.run_job(job_id, provider=model, search=lambda q:['https://example.org'], fetch=fail)
    detail = client.get('/api/jobs/' + job_id).json()
    assert detail['status'] == 'failed' and model.calls == 0
    assert detail['sources'][0]['error']


def test_quotas_and_one_active_response(client, monkeypatch):
    monkeypatch.setattr(settings, 'daily_jobs', 1)
    job_id = submit(client)
    client.post(f'/api/jobs/{job_id}/cancel')
    assert client.post('/api/projects', json={'text':'next','request_key':db.uid()}).status_code == 429


def test_csrf_logout_and_password_storage(client):
    assert client.post('/api/conversations', json={}, headers={'Origin':'https://evil.example'}).status_code == 403
    with db.Session() as s:
        u = s.scalar(select(db.User))
        assert u.password.startswith('$argon2') and 'test-password-long' not in u.password
    assert client.post('/api/auth/logout').status_code == 200
    assert client.get('/api/me').status_code == 401


def test_sessions_survive_restart_and_expire(client):
    assert client.get('/api/me').status_code == 200
    with db.Session.begin() as s:
        s.scalar(select(db.SessionToken)).expires = 0
    assert client.get('/api/me').status_code == 401
