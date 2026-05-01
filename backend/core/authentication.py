"""JWT a partir do header Authorization (compat. testes/CLI) ou de cookies HttpOnly (SPA)."""

from django.conf import settings
from rest_framework_simplejwt.authentication import JWTAuthentication


class JWTCookieAuthentication(JWTAuthentication):
    """Tenta primeiro Bearer; se não houver, usa o cookie de access definido em settings."""

    def authenticate(self, request):
        
        header = self.get_header(request)
        if header is not None:
            raw = self.get_raw_token(header)
            if raw is not None:
                validated = self.get_validated_token(raw)
                return self.get_user(validated), validated

        name = getattr(settings, 'JWT_ACCESS_COOKIE_NAME', 'studies_access')
        raw = request.COOKIES.get(name)
        if not raw:
            return None
        validated = self.get_validated_token(raw)
        return self.get_user(validated), validated
