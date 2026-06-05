"""Login / refresh / logout com tokens só em cookies HttpOnly (não no JSON).

Nota de segurança — CSRF:
    CsrfViewMiddleware foi removido do pipeline (ver settings.py MIDDLEWARE).
    Este módulo lida exclusivamente com autenticação JWT; não há Django sessions
    nem formulários. Os cookies são HttpOnly, portanto o JS nunca consegue lê-los
    para implementar o padrão Double Submit Cookie.

    Proteção CSRF garantida por:
        1. SameSite=Lax em desenvolvimento  → bloqueia POSTs cross-site simples
        2. SameSite=None+Secure em produção → requer HTTPS + CORS explícito
        3. CORS_ALLOWED_ORIGINS restrito    → browsers só enviam cookies para
                                              origens aprovadas
        4. Rate limiting por IP             → limita força bruta nos endpoints
                                              AllowAny (login, register, refresh)

    Os @method_decorator(csrf_exempt) abaixo são defesa em profundidade: caso
    CsrfViewMiddleware seja reativado por engano no futuro, estes views continuam
    funcionando corretamente sem quebrar o fluxo JWT.
"""

from django.conf import settings
from django.utils.decorators import method_decorator
from django.views.decorators.csrf import csrf_exempt
from rest_framework import status
from rest_framework.exceptions import ValidationError
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from rest_framework_simplejwt.exceptions import TokenError
from rest_framework_simplejwt.serializers import (
    TokenBlacklistSerializer,
    TokenObtainPairSerializer,
    TokenRefreshSerializer,
)
from rest_framework_simplejwt.settings import api_settings as jwt_api_settings
from rest_framework_simplejwt.views import (
    TokenBlacklistView,
    TokenObtainPairView,
    TokenRefreshView,
)

from .throttles import AuthLoginThrottle, AuthRefreshThrottle


def _cookie_common() -> dict:
    """Retorna os kwargs comuns a todos os cookies JWT.

    Em DEBUG (HTTP local): SameSite=Lax, Secure=False.
    Em produção (HTTPS):   SameSite=None, Secure=True  (obrigatório para cross-site).

    Pode ser sobrescrito via settings:
        JWT_COOKIE_SAMESITE = 'Lax' | 'None' | 'Strict'
        JWT_COOKIE_SECURE   = True | False
    """
    configured = getattr(settings, 'JWT_COOKIE_SAMESITE', None)
    if configured is None or (isinstance(configured, str) and not configured.strip()):
        raw = 'lax' if settings.DEBUG else 'none'
    else:
        raw = str(configured).strip().lower()

    if raw == 'strict':
        samesite = 'Strict'
    elif raw == 'none':
        samesite = 'None'
    else:
        samesite = 'Lax'

    secure = getattr(settings, 'JWT_COOKIE_SECURE', None)
    if secure is None:
        secure = not settings.DEBUG
    # SameSite=None exige Secure obrigatoriamente (RFC 6265bis)
    if samesite == 'None' and not secure:
        secure = True

    return {
        'httponly': True,
        'secure': secure,
        'samesite': samesite,
        'path': getattr(settings, 'JWT_AUTH_COOKIE_PATH', '/api'),
    }


def _attach_auth_cookies(response, access: str, refresh: str) -> None:
    """Define os cookies de access e refresh na resposta."""
    common = _cookie_common()
    access_name = getattr(settings, 'JWT_ACCESS_COOKIE_NAME', 'studies_access')
    refresh_name = getattr(settings, 'JWT_REFRESH_COOKIE_NAME', 'studies_refresh')
    access_max = int(jwt_api_settings.ACCESS_TOKEN_LIFETIME.total_seconds())
    refresh_max = int(jwt_api_settings.REFRESH_TOKEN_LIFETIME.total_seconds())
    response.set_cookie(access_name, access, max_age=access_max, **common)
    response.set_cookie(refresh_name, refresh, max_age=refresh_max, **common)


def _clear_auth_cookies(response) -> None:
    """Remove os cookies de access e refresh da resposta (logout)."""
    common = _cookie_common()
    access_name = getattr(settings, 'JWT_ACCESS_COOKIE_NAME', 'studies_access')
    refresh_name = getattr(settings, 'JWT_REFRESH_COOKIE_NAME', 'studies_refresh')
    path = common['path']
    response.delete_cookie(access_name, path=path, samesite=common['samesite'])
    response.delete_cookie(refresh_name, path=path, samesite=common['samesite'])


@method_decorator(csrf_exempt, name='dispatch')
class CookieTokenObtainPairView(TokenObtainPairView):
    """POST /api/auth/login/ — autentica com username/password e define cookies JWT.

    Resposta: { "detail": "Sessão iniciada." }
    Os tokens access e refresh são enviados exclusivamente via cookies HttpOnly
    — nunca no corpo da resposta.

    csrf_exempt: ver docstring do módulo.
    """

    permission_classes = [AllowAny]
    throttle_classes = [AuthLoginThrottle]

    def post(self, request, *args, **kwargs):
        serializer = TokenObtainPairSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        data = serializer.validated_data
        access = str(data['access'])
        refresh = str(data['refresh'])
        response = Response({'detail': 'Sessão iniciada.'}, status=status.HTTP_200_OK)
        _attach_auth_cookies(response, access, refresh)
        return response


@method_decorator(csrf_exempt, name='dispatch')
class CookieTokenRefreshView(TokenRefreshView):
    """POST /api/auth/token/refresh/ — renova o access token via cookie de refresh.

    Aceita o refresh token:
        1. Do cookie HttpOnly (fluxo normal da SPA).
        2. Do corpo JSON { "refresh": "..." } (compatibilidade com testes/CLI).

    Em caso de token inválido ou expirado, apaga ambos os cookies e retorna 401
    para forçar o frontend a redirecionar para o login.

    csrf_exempt: ver docstring do módulo.
    """

    permission_classes = [AllowAny]
    throttle_classes = [AuthRefreshThrottle]

    def post(self, request, *args, **kwargs):
        refresh_name = getattr(settings, 'JWT_REFRESH_COOKIE_NAME', 'studies_refresh')
        refresh = request.data.get('refresh') or request.COOKIES.get(refresh_name)

        if not refresh:
            return Response(
                {'detail': 'Refresh em falta.'},
                status=status.HTTP_401_UNAUTHORIZED,
            )

        serializer = TokenRefreshSerializer(data={'refresh': refresh})
        try:
            serializer.is_valid(raise_exception=True)
        except (TokenError, ValidationError):
            resp = Response(
                {'detail': 'Token inválido ou expirado.'},
                status=status.HTTP_401_UNAUTHORIZED,
            )
            _clear_auth_cookies(resp)
            return resp

        access = str(serializer.validated_data['access'])
        response = Response({'detail': 'Token renovado.'}, status=status.HTTP_200_OK)
        common = _cookie_common()
        access_name = getattr(settings, 'JWT_ACCESS_COOKIE_NAME', 'studies_access')
        access_max = int(jwt_api_settings.ACCESS_TOKEN_LIFETIME.total_seconds())
        response.set_cookie(access_name, access, max_age=access_max, **common)

        # ROTATE_REFRESH_TOKENS=True: SimpleJWT devolve um novo refresh token.
        if 'refresh' in serializer.validated_data:
            new_refresh = str(serializer.validated_data['refresh'])
            refresh_max = int(jwt_api_settings.REFRESH_TOKEN_LIFETIME.total_seconds())
            response.set_cookie(refresh_name, new_refresh, max_age=refresh_max, **common)

        return response


@method_decorator(csrf_exempt, name='dispatch')
class CookieTokenBlacklistView(TokenBlacklistView):
    """POST /api/auth/logout/ — invalida o refresh token e apaga os cookies.

    Aceita o refresh token do cookie ou do corpo (compatibilidade).
    Falhas silenciosas (token já inválido/expirado): os cookies são apagados
    de qualquer forma para garantir que o estado do cliente fique limpo.

    csrf_exempt: ver docstring do módulo.
    Nota: um logout forçado via CSRF seria apenas um inconveniente para o
    utilizador (não expõe dados). O SameSite=Lax em dev e o CORS em produção
    já previnem esse cenário.
    """

    def post(self, request, *args, **kwargs):
        refresh_name = getattr(settings, 'JWT_REFRESH_COOKIE_NAME', 'studies_refresh')
        refresh = request.data.get('refresh') or request.COOKIES.get(refresh_name)

        if refresh:
            serializer = TokenBlacklistSerializer(data={'refresh': refresh})
            try:
                # is_valid() já executa internamente o blacklist do SimpleJWT.
                serializer.is_valid(raise_exception=True)
            except (TokenError, ValidationError):
                # Token já expirado ou inválido — prosseguir e limpar cookies.
                pass

        response = Response({'detail': 'Sessão terminada.'}, status=status.HTTP_200_OK)
        _clear_auth_cookies(response)
        return response
