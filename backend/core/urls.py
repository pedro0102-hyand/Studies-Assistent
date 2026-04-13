from django.urls import path
from rest_framework_simplejwt.views import TokenObtainPairView, TokenRefreshView

from . import views

urlpatterns = [
    # Endpoints para a saúde do backend e autenticação
    path('health/', views.health, name='health'),
    path('auth/register/', views.register, name='register'), # Endpoint para o registro de novos usuários
    path('auth/token/', TokenObtainPairView.as_view(), name='token_obtain_pair'), # Endpoint para a obtenção de tokens de acesso
    path('auth/token/refresh/', TokenRefreshView.as_view(), name='token_refresh'), # Endpoint para o refresh de tokens de acesso
]
