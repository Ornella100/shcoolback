from django.contrib.auth import authenticate, login, logout
from django.middleware.csrf import get_token
from django.utils.encoding import force_str
from django.utils.http import urlsafe_base64_decode
from rest_framework import status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response

from .emails import password_reset_token, send_password_reset_email
from .models import User
from .serializers import (
    PasswordResetConfirmSerializer,
    PasswordResetRequestSerializer,
    ProfileUpdateSerializer,
    RegisterSerializer,
)


def _serialize_user(user):
    data = {
        'id': user.id,
        'username': user.username,
        'first_name': user.first_name,
        'last_name': user.last_name,
        'is_superuser': user.is_superuser,
        'account_type': user.account_type,
        'school': {
            'id': user.school_id,
            'name': user.school.name,
        } if user.school_id else None,
    }
    if user.account_type == User.AccountType.PARENT and user.parent_profile_id:
        data['parent'] = {
            'id': user.parent_profile_id,
            'first_name': user.parent_profile.first_name,
            'last_name': user.parent_profile.last_name,
        }
    return data


@api_view(['GET'])
@permission_classes([AllowAny])
def csrf_view(request):
    get_token(request)
    return Response({'detail': 'CSRF cookie set'})


@api_view(['POST'])
@permission_classes([AllowAny])
def register_view(request):
    serializer = RegisterSerializer(data=request.data)
    serializer.is_valid(raise_exception=True)
    user = serializer.save()
    login(request, user)
    return Response(_serialize_user(user), status=status.HTTP_201_CREATED)


@api_view(['POST'])
@permission_classes([AllowAny])
def login_view(request):
    identifier = request.data.get('username') or request.data.get('email') or ''
    username = identifier.strip() if isinstance(identifier, str) else ''
    password = request.data.get('password')
    user = authenticate(request, username=username, password=password)
    if user is None and username:
        candidate = User.objects.filter(
            email__iexact=username,
            account_type=User.AccountType.PARENT,
            is_active=True,
        ).first()
        if candidate and candidate.check_password(password or ''):
            user = candidate
    if user and user.account_type == User.AccountType.PARENT:
        if not user.parent_profile_id or not user.parent_profile.is_active:
            user = None
    if user is None:
        return Response({'detail': 'Identifiants invalides.'}, status=status.HTTP_401_UNAUTHORIZED)
    login(request, user)
    return Response(_serialize_user(user))


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def logout_view(request):
    logout(request)
    return Response(status=status.HTTP_204_NO_CONTENT)


@api_view(['GET', 'PATCH'])
@permission_classes([IsAuthenticated])
def me_view(request):
    if request.method == 'GET':
        return Response(_serialize_user(request.user))
    serializer = ProfileUpdateSerializer(instance=request.user, data=request.data, partial=True)
    serializer.is_valid(raise_exception=True)
    user = serializer.save()
    return Response(_serialize_user(user))


@api_view(['POST'])
@permission_classes([AllowAny])
def password_reset_request_view(request):
    """Envoie un email de réinitialisation si le compte existe. Répond toujours 200 avec
    le même message, pour ne jamais révéler si un email est associé à un compte."""
    serializer = PasswordResetRequestSerializer(data=request.data)
    serializer.is_valid(raise_exception=True)
    email = serializer.validated_data['email']

    user = User.objects.filter(email=email).first()
    if user is not None:
        send_password_reset_email(user)

    return Response({
        'detail': "Si un compte existe avec cet email, un lien de réinitialisation a été envoyé.",
    })


@api_view(['POST'])
@permission_classes([AllowAny])
def password_reset_confirm_view(request):
    serializer = PasswordResetConfirmSerializer(data=request.data)
    serializer.is_valid(raise_exception=True)
    data = serializer.validated_data

    try:
        user_id = force_str(urlsafe_base64_decode(data['uid']))
        user = User.objects.get(pk=user_id)
    except (User.DoesNotExist, ValueError, TypeError, OverflowError):
        return Response({'detail': 'Lien de réinitialisation invalide.'}, status=status.HTTP_400_BAD_REQUEST)

    if not password_reset_token.check_token(user, data['token']):
        return Response({'detail': 'Lien de réinitialisation invalide ou expiré.'}, status=status.HTTP_400_BAD_REQUEST)

    user.set_password(data['new_password'])
    user.save()
    return Response({'detail': 'Mot de passe mis à jour.'})
