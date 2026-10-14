"""Replaceable model interface. No mock provider is available in the application."""
import json
import time
from dataclasses import dataclass
from typing import Protocol, Callable
from urllib.parse import urlparse
import httpx
from .config import settings


class ProviderError(Exception):
    pass


@dataclass
class Result:
    text: str
    input_tokens: int | None = None
    output_tokens: int | None = None


@dataclass(frozen=True)
class Capabilities:
    text: bool = True
    streaming: bool = True
    tools: bool = False
    images: bool = False
    audio: bool = False


def provider_capabilities(name: str) -> Capabilities:
    """Adapter capabilities, not untested claims about a selected model."""
    if name not in ('openai', 'ollama', 'openclaw'):
        raise ProviderError('The selected provider has no installed adapter.')
    return Capabilities(streaming=False) if name == 'openclaw' else Capabilities()


def configuration_missing() -> list[str]:
    missing = []
    if not settings.model:
        missing.append('FRIDAY_MODEL')
    if settings.provider == 'openai' and not settings.api_key:
        missing.append('FRIDAY_API_KEY')
    if settings.provider == 'openclaw':
        if not settings.openclaw_token:
            missing.append('FRIDAY_OPENCLAW_TOKEN')
        if not settings.model or '/' not in settings.model:
            missing.append('FRIDAY_MODEL (provider/model)')
    if settings.provider not in ('openai', 'ollama', 'openclaw'):
        missing.append('FRIDAY_PROVIDER adapter')
    return missing


class ModelProvider(Protocol):
    capabilities: Capabilities
    def complete(self, messages: list[dict], on_text: Callable[[str], None]) -> Result: ...


class OpenAIProvider:
    capabilities = Capabilities()
    def complete(self, messages, on_text):
        if not settings.api_key or not settings.model:
            raise ProviderError('Configure FRIDAY_API_KEY and FRIDAY_MODEL on the server.')
        started = time.monotonic()
        text = ''
        try:
            with httpx.Client(timeout=60, trust_env=False) as client:
                with client.stream('POST', 'https://api.openai.com/v1/responses',
                    headers={'Authorization': f'Bearer {settings.api_key}'},
                    json={'model': settings.model, 'input': messages, 'store': False,
                          'stream': True, 'max_output_tokens': settings.max_output_tokens}) as response:
                    if response.status_code != 200:
                        raise ProviderError(f'Model provider returned HTTP {response.status_code}; check configuration or quota.')
                    for line in response.iter_lines():
                        if time.monotonic() - started > 100:
                            raise ProviderError('Model request exceeded its time limit; outcome uncertain.')
                        if not line.startswith('data: '):
                            continue
                        if line[6:] == '[DONE]':
                            break
                        data = json.loads(line[6:])
                        if data.get('type') == 'response.output_text.delta':
                            text += data['delta']
                            if len(text) > 80000:
                                raise ProviderError('Model output exceeded the application limit.')
                            on_text(text)
                        elif data.get('type') == 'response.completed':
                            usage = data['response'].get('usage') or {}
                            if not text.strip():
                                raise ProviderError('The provider returned no text.')
                            return Result(text, usage.get('input_tokens'), usage.get('output_tokens'))
                        elif data.get('type') in ('error', 'response.failed', 'response.incomplete'):
                            raise ProviderError('Model response failed or was incomplete; partial output is not a completed answer.')
        except (httpx.HTTPError, ValueError) as exc:
            raise ProviderError('Model connection failed; usage may have occurred. No automatic paid retry.') from exc
        raise ProviderError('Model stream ended without confirmation; outcome uncertain.')


class OllamaProvider:
    """Stream one response from a private Ollama service, with no cloud fallback."""
    capabilities = Capabilities()

    def complete(self, messages, on_text):
        if not settings.model:
            raise ProviderError('Configure FRIDAY_MODEL on the server.')
        parsed = urlparse(settings.ollama_url)
        if (parsed.scheme != 'http' or parsed.hostname not in ('ollama', 'localhost', '127.0.0.1')
                or parsed.username or parsed.password or parsed.path not in ('', '/')
                or parsed.query or parsed.fragment):
            raise ProviderError('FRIDAY_OLLAMA_URL must point to the private local Ollama service.')
        url = settings.ollama_url.rstrip('/') + '/api/chat'
        started = time.monotonic()
        output = ''
        try:
            with httpx.Client(timeout=httpx.Timeout(300, connect=10), trust_env=False) as client:
                with client.stream('POST', url, json={
                    'model': settings.model,
                    'messages': messages,
                    'stream': True,
                    'options': {'num_predict': settings.max_output_tokens},
                }) as response:
                    if response.status_code != 200:
                        raise ProviderError(f'Local model returned HTTP {response.status_code}; check model service and selected model.')
                    for line in response.iter_lines():
                        if time.monotonic() - started > 600:
                            raise ProviderError('Local model response exceeded its time limit.')
                        if not line:
                            continue
                        data = json.loads(line)
                        if data.get('error'):
                            raise ProviderError('Local model returned an error; inspect private service logs.')
                        chunk = (data.get('message') or {}).get('content', '')
                        if not isinstance(chunk, str):
                            raise ProviderError('Local model returned invalid text.')
                        output += chunk
                        if len(output) > 80000:
                            raise ProviderError('Local model output exceeded the application limit.')
                        if chunk:
                            on_text(output)
                        if data.get('done') is True:
                            if not output.strip():
                                raise ProviderError('The local model returned no text.')
                            return Result(output, data.get('prompt_eval_count'), data.get('eval_count'))
        except (httpx.HTTPError, ValueError, TypeError) as exc:
            raise ProviderError('Local model connection failed or returned invalid data; no answer was saved.') from exc
        raise ProviderError('Local model stream ended without a final response.')


class OpenClawProvider:
    """Use a private, policy-restricted OpenClaw Gateway as an agent runtime.

    FRIDAY still owns authentication, chat history and the selected underlying model.
    Gateway tool permissions must be restricted separately before this mode is enabled.
    """
    capabilities = Capabilities(streaming=False)

    def complete(self, messages, on_text):
        parsed = urlparse(settings.openclaw_url)
        if (parsed.scheme != 'http' or parsed.hostname not in ('openclaw', 'localhost', '127.0.0.1')
                or parsed.username or parsed.password or parsed.path not in ('', '/')
                or parsed.query or parsed.fragment):
            raise ProviderError('OpenClaw Gateway must be a private local service.')
        if not settings.openclaw_token or not settings.model or '/' not in settings.model:
            raise ProviderError('Configure a Gateway token and a provider/model in FRIDAY Settings.')
        if not messages or any(m.get('role') not in ('system', 'user', 'assistant')
                               or not isinstance(m.get('content'), str) for m in messages):
            raise ProviderError('Invalid conversation sent to the agent runtime.')
        try:
            with httpx.Client(timeout=httpx.Timeout(180, connect=5), trust_env=False) as client:
                response = client.post(settings.openclaw_url.rstrip('/') + '/v1/chat/completions',
                    headers={'Authorization': f'Bearer {settings.openclaw_token}',
                             'x-openclaw-model': settings.model},
                    json={'model': 'openclaw/default', 'messages': messages,
                          'stream': False, 'max_completion_tokens': settings.max_output_tokens})
            if response.status_code != 200:
                raise ProviderError(f'Private agent runtime returned HTTP {response.status_code}.')
            data = response.json()
            choice = data['choices'][0]
            message = choice['message']
            if choice.get('finish_reason') != 'stop' or message.get('tool_calls'):
                raise ProviderError('Agent runtime did not return a completed text answer.')
            output = message.get('content')
            if not isinstance(output, str) or not output.strip() or len(output) > 80000:
                raise ProviderError('Agent runtime returned invalid or empty text.')
            usage = data.get('usage') or {}
            on_text(output)
            return Result(output, usage.get('prompt_tokens'), usage.get('completion_tokens'))
        except (httpx.HTTPError, ValueError, KeyError, IndexError, TypeError) as exc:
            raise ProviderError('Private agent runtime failed or returned invalid data.') from exc


def get_provider() -> ModelProvider:
    provider_capabilities(settings.provider)
    if settings.provider == 'openai':
        return OpenAIProvider()
    if settings.provider == 'openclaw':
        return OpenClawProvider()
    return OllamaProvider()

