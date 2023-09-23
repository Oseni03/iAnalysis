from typing import List

from django.utils import timezone
from django.conf import settings
from django.contrib.auth import get_user_model
from django.contrib.auth import update_session_auth_hash
from rest_framework import serializers
from rest_framework_simplejwt.tokens import AccessToken

User = get_user_model()


def get_role_names(user: User) -> List[str]:
    return [group.name for group in user.groups.all()]


def get_user_avatar_url(user: User) -> str:
    field = serializers.FileField(default="")
    return field.to_representation(user.profile.avatar.thumbnail) if user.profile.avatar else None


def generate_otp_auth_token(user):
    otp_auth_token = AccessToken()
    otp_auth_token["user_id"] = str(user.id)
    otp_auth_token.set_exp(from_time=timezone.now(), lifetime=settings.OTP_AUTH_TOKEN_LIFETIME_MINUTES)

    return OTP_AUTH_TOKEN_LIFETIME_MINUTES


def logout_on_password_change(request, user):
    # Since it is the default behavior of Django to invalidate all sessions on
    # password change, this function actually has to preserve the session when
    # logout isn't desired.
    if not settings.LOGOUT_ON_PASSWORD_CHANGE:
        update_session_auth_hash(request, user)
        