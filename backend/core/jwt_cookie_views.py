"""Login / refresh / logout com tokens só em cookies HttpOnly (não no JSON)."""

from django.conf import settings
from rest_framework import status
from rest_framework.exceptions import ValidationError
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


def _cookie_common():
    """Secure obrigatório com SameSite=None; em DEBUG local (HTTP) usa Lax + Secure=False."""
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
    if samesite == 'None' and not secure:
        secure = True
    return {
        'httponly': True,
        'secure': secure,
        'samesite': samesite,
        'path': getattr(settings, 'JWT_AUTH_COOKIE_PATH', '/api'),
    }


def _attach_auth_cookies(response, access: str, refresh: str) -> None:

    common = _cookie_common()
    access_name = getattr(settings, 'JWT_ACCESS_COOKIE_NAME', 'studies_access')
    refresh_name = getattr(settings, 'JWT_REFRESH_COOKIE_NAME', 'studies_refresh')
    access_max = int(jwt_api_settings.ACCESS_TOKEN_LIFETIME.total_seconds())
    refresh_max = int(jwt_api_settings.REFRESH_TOKEN_LIFETIME.total_seconds())
    response.set_cookie(access_name, access, max_age=access_max, **common)
    response.set_cookie(refresh_name, refresh, max_age=refresh_max, **common)


def _clear_auth_cookies(response) -> None:

    common = _cookie_common()
    access_name = getattr(settings, 'JWT_ACCESS_COOKIE_NAME', 'studies_access')
    refresh_name = getattr(settings, 'JWT_REFRESH_COOKIE_NAME', 'studies_refresh')
    path = common['path']
    response.delete_cookie(access_name, path=path, samesite=common['samesite'])
    response.delete_cookie(refresh_name, path=path, samesite=common['samesite'])


class CookieTokenObtainPairView(TokenObtainPairView):
    """POST username/password — define cookies; corpo sem tokens."""

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


class CookieTokenRefreshView(TokenRefreshView):
    """POST — refresh a partir do cookie ou do body (compat.); novo access em cookie."""

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
        if 'refresh' in serializer.validated_data:
            new_refresh = str(serializer.validated_data['refresh'])
            refresh_max = int(jwt_api_settings.REFRESH_TOKEN_LIFETIME.total_seconds())
            response.set_cookie(refresh_name, new_refresh, max_age=refresh_max, **common)
        return response


class CookieTokenBlacklistView(TokenBlacklistView):
    """POST — invalida refresh (cookie ou body) e apaga cookies."""

    def post(self, request, *args, **kwargs):
        refresh_name = getattr(settings, 'JWT_REFRESH_COOKIE_NAME', 'studies_refresh')
        refresh = request.data.get('refresh') or request.COOKIES.get(refresh_name)
        if refresh:
            serializer = TokenBlacklistSerializer(data={'refresh': refresh})
            try:
                serializer.is_valid(raise_exception=True)
                serializer.save()
            except (TokenError, ValidationError):
                pass
        response = Response({'detail': 'Sessão terminada.'}, status=status.HTTP_200_OK)
        _clear_auth_cookies(response)
        return response
