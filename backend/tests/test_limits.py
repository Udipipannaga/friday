from friday import db, execution, providers, retrieval
from friday.config import settings
from tests.test_workflows import submit, TestModel


def test_active_limit_and_conversation_exclusion(client, monkeypatch):
    first = submit(client,'chat')
    with db.Session() as s:
        cid = s.get(db.Job,first).conversation_id
    assert client.post(f'/api/conversations/{cid}/messages',json={'text':'overlap','request_key':db.uid()}).status_code == 409
    monkeypatch.setattr(settings,'max_active_jobs',1)
    assert client.post('/api/projects',json={'text':'overlap','request_key':db.uid()}).status_code == 429
    assert client.get('/api/me').json()['jobs_today'] == 1


def test_oversized_json_rejected(client):
    assert client.post('/api/projects',content='x'*20001).status_code == 413


def test_model_failure_is_terminal_and_usage_uncertain(client):
    class FailedModel:
        def complete(self,messages,on_text):
            on_text('Partial response')
            raise providers.ProviderError('Connection lost; outcome uncertain.')
    jid = submit(client,'chat')
    execution.run_job(jid,provider=FailedModel())
    d = client.get(f'/api/jobs/{jid}').json()
    assert d['status'] == 'failed' and d['usage']['status'] == 'uncertain'
    assert d['partial'] == 'Partial response'


def test_forged_evidence_excerpt_rejected(client):
    class InventedModel(TestModel):
        def complete(self,messages,on_text):
            return providers.Result('{"findings":[{"claim":"Claim","source":1,"evidence":"This quote never existed"}],"gaps":"Unknown"}')
    jid = submit(client)
    execution.run_job(jid,provider=InventedModel(),search=lambda q:['https://example.org'],fetch=lambda u:retrieval.Page(u,'Evidence','durable research workflow '*8))
    d = client.get(f'/api/jobs/{jid}').json()
    assert d['status'] == 'failed' and d['artifact'] is None


def test_success_clears_previous_search_failure(client):
    jid = submit(client)
    def fail(q): raise retrieval.RetrievalError('Temporary search outage')
    execution.run_job(jid,provider=TestModel(),search=fail)
    with db.Session.begin() as s:
        s.get(db.Job,jid).available = 0
    execution.run_job(jid,provider=TestModel(),search=lambda q:['https://example.org'],fetch=lambda u:retrieval.Page(u,'Evidence','A durable research workflow stores state.'))
    d = client.get(f'/api/jobs/{jid}').json()
    assert d['status'] == 'succeeded' and d['error'] == ''
