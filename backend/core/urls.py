from django.urls import path
from rest_framework_simplejwt.views import (
    TokenBlacklistView,
    TokenObtainPairView,
    TokenRefreshView,
)

from . import views

urlpatterns = [
    path('health/', views.health, name='health'),
    path('auth/register/', views.register, name='register'),
    path('auth/me/', views.me, name='me'),
    # Login: mesmo comportamento que auth/token/ (body: username, password)
    path('auth/login/', TokenObtainPairView.as_view(), name='login'),
    path('auth/token/', TokenObtainPairView.as_view(), name='token_obtain_pair'),
    path('auth/token/refresh/', TokenRefreshView.as_view(), name='token_refresh'),
    # Logout: body JSON {"refresh": "<refresh_token>"}
    path('auth/logout/', TokenBlacklistView.as_view(), name='logout'),
]
