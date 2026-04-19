
from __future__ import annotations

from typing import Any

import httpx


class OllamaChatError(Exception):
    """Falha na geração (rede, HTTP ou resposta inválida)."""


def _parse_chat_response(data: dict[str, Any]) -> str:

    msg = data.get('message')
    if isinstance(msg, dict):
        content = msg.get('content')
        if content is not None:
            return str(content).strip()
    raise OllamaChatError('Resposta do Ollama sem `message.content`.')


def ollama_chat_completion(
    messages: list[dict[str, str]],
    *,
    base_url: str,
    model: str,
    timeout: float = 180.0,
) -> str:
    """
    Uma volta de chat não streaming. `messages`: lista de ``{"role": "system"|"user"|"assistant", "content": "..."}``.
    """
    if not messages:
        raise ValueError('messages não pode ser vazio.')

    url = f'{base_url.rstrip("/")}/api/chat'

    with httpx.Client(timeout=timeout) as client:
        try:
            resp = client.post(
                url,
                json={
                    'model': model,
                    'messages': messages,
                    'stream': False,
                },
            )
        except httpx.RequestError as exc:
            raise OllamaChatError(
                f'Não foi possível contactar o Ollama em {base_url}: {exc}'
            ) from exc

        if resp.status_code >= 400:
            detail = resp.text[:400] if resp.text else resp.reason_phrase
            try:
                err_body = resp.json()
                if isinstance(err_body, dict) and err_body.get('error'):
                    detail = str(err_body['error'])[:500]
            except Exception:
                pass
            raise OllamaChatError(f'Ollama HTTP {resp.status_code}: {detail}')

        try:
            data = resp.json()
        except ValueError as exc:
            raise OllamaChatError('Resposta JSON inválida do Ollama.') from exc

        if not isinstance(data, dict):
            raise OllamaChatError('Resposta inesperada do Ollama.')

        return _parse_chat_response(data)
