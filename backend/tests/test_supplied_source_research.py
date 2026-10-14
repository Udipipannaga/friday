"""Research from explicit sources remains a durable, bounded tool workflow."""
import json
from friday import db, execution, retrieval, providers
from friday.config import settings


class TestModel:
    def complete(self, messages, on_text):
        response = json.dumps({'findings': [{'claim': 'The source describes a durable research workflow.',
            'source': 1, 'evidence': 'durable research workflow'}], 'gaps': 'Only one source was supplied.'})
        on_text(response)
        return providers.Result(response, 25, 40)


def test_supplied_sources_bypass_search_and_save_evidence(client, monkeypatch):
    monkeypatch.setattr(settings, 'provider', 'ollama')
    monkeypatch.setattr(settings, 'search_key', '')
    urls = ['https://example.org/research']
    payload = {'text': 'How does durable research work?', 'source_urls': urls, 'request_key': db.uid()}
    submitted = client.post('/api/projects', json=payload)
    assert submitted.status_code == 202, submitted.text
    job_id = submitted.json()['id']
    assert submitted.json()['source_urls'] == urls
    assert client.post('/api/projects', json=payload).json()['id'] == job_id
    assert client.post('/api/projects', json={**payload, 'source_urls': ['https://example.org/other']}).status_code == 409

    def unexpected_search(_query):
        raise AssertionError('Supplied-source workflow must not call web search')

    execution.run_job(job_id, provider=TestModel(), search=unexpected_search,
        fetch=lambda url: retrieval.Page(url, 'Fixture source',
            'A durable research workflow persists source evidence and project state. ' * 4))
    result = client.get('/api/jobs/' + job_id).json()
    assert result['status'] == 'succeeded', result['error']
    assert result['source_urls'] == urls
    assert result['sources'][0]['url'] == urls[0]
    assert urls[0] in result['artifact']


def test_source_urls_are_bounded_and_web_search_still_requires_key(client, monkeypatch):
    monkeypatch.setattr(settings, 'provider', 'ollama')
    monkeypatch.setattr(settings, 'search_key', '')
    base = {'text': 'Check a source', 'request_key': db.uid()}
    assert client.post('/api/projects', json=base).status_code == 503
    assert client.get('/api/me').json()['jobs_today'] == 0
    bad = ['http://example.org', 'https://user:pass@example.org',
           'https://example.org:8080', 'https://example.org/path#fragment',
           'https://example.org/has space']
    for url in bad:
        assert client.post('/api/projects', json={**base, 'source_urls': [url]}).status_code == 422
    assert client.post('/api/projects', json={**base, 'source_urls': ['https://example.org'] * 6}).status_code == 422
    assert client.get('/api/me').json()['jobs_today'] == 0

