from rest_framework import status
from rest_framework.decorators import api_view, permission_classes, throttle_classes
from rest_framework.permissions import AllowAny
from rest_framework.response import Response

from .serializers import RegisterSerializer, UserMeSerializer
from .throttles import AuthRegisterThrottle


@api_view(['GET'])
@permission_classes([AllowAny])
def health(request):
    return Response({'status': 'ok'})


@api_view(['POST'])
@permission_classes([AllowAny])
@throttle_classes([AuthRegisterThrottle])
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


@api_view(['GET'])
def me(request):
    serializer = UserMeSerializer(request.user)
    return Response(serializer.data)
