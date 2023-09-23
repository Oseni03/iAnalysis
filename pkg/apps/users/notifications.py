import logging

from common import emails
from . import email_serializers

logger = logging.getLogger(__name__)


class UserEmail(emails.Email):
    def __init__(self, user, data=None):
        super().__init__(to=user.email, data=data)


class OTPAuthMail(UserEmail):
    """
    To call:
        notifications.OTPAuthMail(
            user=user, 
            data={
                'user_id': user.id.hashid, 
                'token': 'jgdrjh568832'
            }
        ).send()
    """
    name = 'OTP_AUTH_MAIL'
    serializer_class = email_serializers.OTPAuthSerializer


class AccountActivationEmail(UserEmail):
    name = 'ACCOUNT_ACTIVATION'
    serializer_class = email_serializers.AccountActivationEmailSerializer


class PasswordResetEmail(UserEmail):
    name = 'PASSWORD_RESET'
    serializer_class = email_serializers.PasswordResetEmailSerializer
    