"""Rate limits por IP nas rotas de autenticação (força bruta / abuso)."""

from rest_framework.throttling import SimpleRateThrottle


class _AuthIPThrottle(SimpleRateThrottle):
    """Sempre por IP, mesmo com sessão JWT (evita contornar limites)."""

    def get_cache_key(self, request, view):
        return self.cache_format % {
            'scope': self.scope,
            'ident': self.get_ident(request),
        }


class AuthLoginThrottle(_AuthIPThrottle):
    scope = 'auth_login'


class AuthRegisterThrottle(_AuthIPThrottle):
    scope = 'auth_register'


class AuthRefreshThrottle(_AuthIPThrottle):
    scope = 'auth_refresh'
