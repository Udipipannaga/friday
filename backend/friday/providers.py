"""Replaceable model interface. No mock provider is available in the application."""
import json
import time
from dataclasses import dataclass
from typing import Protocol, Callable
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
    if name != 'openai':
        raise ProviderError('The selected provider has no installed adapter.')
    return Capabilities()


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


def get_provider() -> ModelProvider:
    provider_capabilities(settings.provider)
    return OpenAIProvider()
