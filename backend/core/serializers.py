from django.contrib.auth import get_user_model
from django.contrib.auth.password_validation import validate_password
from django.core.exceptions import ValidationError as DjangoValidationError
from rest_framework import serializers

User = get_user_model()

# Serializador para o registro de novos usuários
class RegisterSerializer(serializers.Serializer):

    username = serializers.CharField(max_length=150, trim_whitespace=True)
    email = serializers.EmailField(required=False, allow_blank=True, default='')
    password = serializers.CharField(write_only=True, style={'input_type': 'password'})
    password_confirm = serializers.CharField(write_only=True, style={'input_type': 'password'})

    def validate_username(self, value):

        if User.objects.filter(username__iexact=value).exists():
            raise serializers.ValidationError('Este nome de utilizador já está em uso.')
        return value

    def validate_email(self, value):

        value = (value or '').strip()
        if value and User.objects.filter(email__iexact=value).exists():
            raise serializers.ValidationError('Este email já está em uso.')
        return value

    def validate(self, attrs):

        if attrs['password'] != attrs['password_confirm']:
            raise serializers.ValidationError(
                {'password_confirm': 'As palavras-passe não coincidem.'}
            )
        try:
            validate_password(attrs['password'])
        except DjangoValidationError as exc:
            raise serializers.ValidationError({'password': list(exc.messages)}) from exc
        return attrs

    def create(self, validated_data):

        validated_data.pop('password_confirm')
        password = validated_data.pop('password')
        email = (validated_data.pop('email', '') or '').strip()
        return User.objects.create_user(
            username=validated_data['username'],
            email=email,
            password=password,
        )
