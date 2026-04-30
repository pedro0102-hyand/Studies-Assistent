from __future__ import annotations

from typing import Any

from rest_framework.response import Response
from rest_framework.views import exception_handler as drf_exception_handler


_DETAIL_MAP: dict[str, str] = {
    # DRF auth
    'Authentication credentials were not provided.': 'Credenciais de autenticação não foram fornecidas.',
    'Invalid token.': 'Token inválido.',
    'Token is invalid or expired': 'Token inválido ou expirado.',
    'You do not have permission to perform this action.': 'Você não tem permissão para realizar esta ação.',
    'Not found.': 'Não encontrado.',
    'Method \"{method}\" not allowed.': 'Método \"{method}\" não permitido.',
    # SimpleJWT login
    'No active account found with the given credentials': 'Nenhuma conta ativa encontrada com as credenciais informadas.',
    'No active account found with the given credentials.': 'Nenhuma conta ativa encontrada com as credenciais informadas.',
    # Generic
    'Bad Request': 'Pedido inválido.',
    'Internal Server Error': 'Erro interno do servidor.',
}


def _translate_detail(detail: Any) -> Any:
    """
    Traduz mensagens comuns do DRF/SimpleJWT que podem aparecer em inglês.
    Mantém estrutura (str/list/dict) quando possível.
    """
    if isinstance(detail, str):
        return _DETAIL_MAP.get(detail, detail)
    if isinstance(detail, list):
        return [_translate_detail(x) for x in detail]
    if isinstance(detail, dict):
        return {k: _translate_detail(v) for k, v in detail.items()}
    return detail


def exception_handler(exc: Exception, context: dict[str, Any]) -> Response | None:
    res = drf_exception_handler(exc, context)
    if res is None:
        return None

    data = res.data
    # DRF geralmente usa {'detail': '...'}
    if isinstance(data, dict) and 'detail' in data:
        data = {**data, 'detail': _translate_detail(data.get('detail'))}
        res.data = data
    elif isinstance(data, (list, dict)):
        res.data = _translate_detail(data)

    return res

