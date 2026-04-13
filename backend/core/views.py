from rest_framework import status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import AllowAny
from rest_framework.response import Response

from .serializers import RegisterSerializer


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
