import json
import httpx
import pytest
from friday import providers


def test_unknown_adapter_never_substituted(monkeypatch):
    monkeypatch.setattr(providers.settings, 'provider', 'friday-checkpoint')
    with pytest.raises(providers.ProviderError, match='no installed adapter'):
        providers.get_provider()


def test_status_describes_adapter_not_model_quality(client):
    status = client.get('/api/status').json()
    assert status['adapter_capabilities']['streaming'] is True
    assert status['adapter_capabilities']['tools'] is False
    assert status['model_evaluation'] == 'not evaluated'


def test_real_adapter_request_and_stream_parsing(monkeypatch):
    original = httpx.Client
    observed = []
    def handler(request):
        body = json.loads(request.content)
        observed.append(body)
        assert str(request.url) == 'https://api.openai.com/v1/responses'
        assert body['store'] is False and body['stream'] is True
        events = [{'type':'response.output_text.delta','delta':'Hello '},{'type':'response.output_text.delta','delta':'FRIDAY'},{'type':'response.completed','response':{'usage':{'input_tokens':12,'output_tokens':4}}}]
        return httpx.Response(200,text='\n\n'.join('data: '+json.dumps(x) for x in events))
    monkeypatch.setattr(httpx,'Client',lambda **kwargs:original(transport=httpx.MockTransport(handler)))
    chunks = []
    result = providers.OpenAIProvider().complete([{'role':'user','content':'hi'}],chunks.append)
    assert result.text == 'Hello FRIDAY' and result.input_tokens == 12
    assert chunks == ['Hello ', 'Hello FRIDAY']


@pytest.mark.parametrize('status',[401,429,500])
def test_provider_errors_are_sanitized(monkeypatch,status):
    original = httpx.Client
    monkeypatch.setattr(httpx,'Client',lambda **kwargs:original(transport=httpx.MockTransport(lambda r:httpx.Response(status,text='sensitive-provider-response'))))
    with pytest.raises(providers.ProviderError) as exc:
        providers.OpenAIProvider().complete([],lambda t:None)
    assert str(status) in str(exc.value) and 'sensitive' not in str(exc.value)


def test_private_ollama_adapter_streams_and_reports_usage(monkeypatch, client):
    original = httpx.Client
    monkeypatch.setattr(providers.settings, 'provider', 'ollama')
    monkeypatch.setattr(providers.settings, 'ollama_url', 'http://ollama:11434')
    observed = []
    def handler(request):
        body = json.loads(request.content)
        observed.append(body)
        assert str(request.url) == 'http://ollama:11434/api/chat'
        assert body['model'] == 'fixture-model' and body['stream'] is True
        events = [
            {'message': {'content': 'Hello '}, 'done': False},
            {'message': {'content': 'FRIDAY'}, 'done': False},
            {'message': {'content': ''}, 'done': True, 'prompt_eval_count': 7, 'eval_count': 2},
        ]
        return httpx.Response(200, text='\n'.join(json.dumps(x) for x in events) + '\n')
    monkeypatch.setattr(httpx, 'Client', lambda **kwargs: original(transport=httpx.MockTransport(handler)))
    chunks = []
    result = providers.get_provider().complete([{'role': 'user', 'content': 'hi'}], chunks.append)
    assert result.text == 'Hello FRIDAY' and (result.input_tokens, result.output_tokens) == (7, 2)
    assert chunks == ['Hello ', 'Hello FRIDAY'] and len(observed) == 1
    status = client.get('/api/status').json()
    assert status['chat_configured'] is True and 'FRIDAY_API_KEY' not in status['missing']


def test_ollama_rejects_external_endpoint_and_sanitizes_errors(monkeypatch):
    monkeypatch.setattr(providers.settings, 'ollama_url', 'https://example.com')
    with pytest.raises(providers.ProviderError, match='private local'):
        providers.OllamaProvider().complete([], lambda text: None)
    monkeypatch.setattr(providers.settings, 'ollama_url', 'http://127.0.0.1:11434')
    original = httpx.Client
    monkeypatch.setattr(httpx, 'Client', lambda **kwargs: original(transport=httpx.MockTransport(
        lambda request: httpx.Response(404, text='private model details'))))
    with pytest.raises(providers.ProviderError) as exc:
        providers.OllamaProvider().complete([], lambda text: None)
    assert '404' in str(exc.value) and 'private model details' not in str(exc.value)

