from rest_framework import status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response

from .serializers import RegisterSerializer, UserMeSerializer


@api_view(['GET']) # Endpoint para verificar a saúde do backend

@permission_classes([AllowAny]) # Permite acesso a todos os usuários

def health(request):
    return Response({'status': 'ok'})


@api_view(['POST'])
@permission_classes([AllowAny])
def register(request):
    serializer = RegisterSerializer(data=request.data)
    serializer.is_valid(raise_exception=True)
    user = serializer.save()
    return Response(
        {
            'id': user.id,
            'username': user.username,
            'email': user.email,
        },
        status=status.HTTP_201_CREATED,
    )


@api_view(['GET']) # Endpoint para obter o perfil do usuário autenticado
@permission_classes([IsAuthenticated]) # Requer autenticação
def me(request):
    serializer = UserMeSerializer(request.user) # Serializa o usuário autenticado
    return Response(serializer.data) # Retorna o perfil do usuário autenticado  
