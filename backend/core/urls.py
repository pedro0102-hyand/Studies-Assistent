from django.urls import path

from . import views
from .jwt_cookie_views import (
    CookieTokenBlacklistView,
    CookieTokenObtainPairView,
    CookieTokenRefreshView,
)

urlpatterns = [
    path('health/', views.health, name='health'),
    path('auth/register/', views.register, name='register'),
    path('auth/me/', views.me, name='me'),
    # Login: body username/password — tokens só em cookies HttpOnly
    path('auth/login/', CookieTokenObtainPairView.as_view(), name='login'),
    path('auth/token/', CookieTokenObtainPairView.as_view(), name='token_obtain_pair'),
    path('auth/token/refresh/', CookieTokenRefreshView.as_view(), name='token_refresh'),
    path('auth/logout/', CookieTokenBlacklistView.as_view(), name='logout'),
]
