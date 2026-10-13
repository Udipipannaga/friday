"""Explicit memory lifecycle and model-context isolation."""
from fastapi.testclient import TestClient
from friday import db, execution, providers
from friday.api import app


class CaptureModel:
    def __init__(self):
        self.calls = []

    def complete(self, messages, on_text):
        self.calls.append(messages)
        on_text('Fixture reply.')
        return providers.Result('Fixture reply.', 10, 3)


def chat(client, model):
    c = client.post('/api/conversations', json={}).json()
    r = client.post(f'/api/conversations/{c["id"]}/messages',
        json={'text': 'What do you know about my work?', 'request_key': db.uid()})
    assert r.status_code == 202, r.text
    execution.run_job(r.json()['id'], provider=model)
    return c['id']


def test_memory_is_explicit_editable_exportable_and_removed_from_later_context(client):
    model = CaptureModel()
    assert client.get('/api/memories').json() == []
    first = chat(client, model)
    assert all('QuiCut' not in m['content'] for m in model.calls[0])
    saved = client.post('/api/memories', json={'label': 'My company', 'content': 'QuiCut matches creators with editors.'})
    assert saved.status_code == 201
    memory_id = saved.json()['id']
    assert saved.json()['origin'] == 'user_explicit'
    assert len(client.get('/api/memories').json()) == 1
    assert client.get('/api/memories/export').json()[0]['id'] == memory_id
    chat(client, model)
    assert 'QuiCut matches creators with editors.' in str(model.calls[-1])
    updated = client.post(f'/api/memories/{memory_id}/update', json={'label': 'My company', 'content': 'QuiCut is a private marketplace project.'})
    assert updated.status_code == 200
    chat(client, model)
    assert 'private marketplace project' in str(model.calls[-1])
    assert 'matches creators with editors' not in str(model.calls[-1])
    assert client.post(f'/api/memories/{memory_id}/delete').status_code == 200
    assert client.get('/api/memories').json() == []
    chat(client, model)
    assert 'QuiCut' not in str(model.calls[-1])
    assert client.get(f'/api/conversations/{first}').status_code == 200  # history remains separate


def test_memory_is_private_and_rejects_credential_or_card_text(client):
    saved = client.post('/api/memories', json={'label': 'Preference', 'content': 'Use concise project updates.'})
    memory_id = saved.json()['id']
    for secret in ['My password is abc123', 'Card 4111 1111 1111 1111', 'API key is abc123']:
        assert client.post('/api/memories', json={'label': 'Unsafe', 'content': secret}).status_code == 422
    with TestClient(app, headers={'Origin': 'http://testserver', 'X-Friday-Request': '1'}) as other:
        assert other.post('/api/auth/register', json={'email': 'bob@example.com', 'password': 'another-test-password'}).status_code == 201
        assert other.get('/api/memories').json() == []
        assert other.get('/api/memories/export').json() == []
        assert other.post(f'/api/memories/{memory_id}/update', json={'label': 'Attack', 'content': 'Changed'}).status_code == 404
        assert other.post(f'/api/memories/{memory_id}/delete').status_code == 404
    assert client.get('/api/memories').json()[0]['content'] == 'Use concise project updates.'

