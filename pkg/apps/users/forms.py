from django import forms 
from django.conf import settings
from django.core import validators
from django.shortcuts import get_object_or_404
from django.contrib import auth as dj_auth
from django.contrib.auth import password_validation, get_user_model
from django.contrib.auth.models import update_last_login
from django.utils.translation import gettext as _
from django.core.exceptions import ValidationError
from django.contrib.auth.forms import PasswordChangeForm, SetPasswordForm


from common.decorators import context_user_required

import enums
from .services import otp as otp_services
from .utils import generate_otp_auth_token
from .models import User, UserProfile, UserAvatar
from config.celery import send_mail
from . import models, tokens

UPLOADED_AVATAR_SIZE_LIMIT = 1 * 1024 * 1024


class UserLoginForm(forms.Form):
    email = forms.EmailField(
        required=True,
        widget=forms.EmailInput(attrs={"autocorrect": "off", "autocapitalize": "off"}),
        help_text=_("Write your email here...")
    )
    password = forms.CharField(required=True, widget=forms.PasswordInput(), help_text=_("Write your password here..."))


class UserProfileForm(forms.ModelForm):
    # email = forms.EmailField()
    avatar = forms.FileField(required=False)

    class Meta:
        model = UserProfile
        fields = ("first_name", "last_name", "avatar")

    @staticmethod
    def validate_avatar(avatar):
        if avatar and avatar.size > UPLOADED_AVATAR_SIZE_LIMIT:
            raise ValidationError({"avatar": _("Too large file")}, 'too_large')
        return avatar

    def to_representation(self, user):
        self.fields["avatar"] = forms.FileField(source="avatar.thumbnail", default="")
        return super().to_representation(user)

    def update(self, user):
        avatar = self.cleaned_data.pop("avatar", None)
        first_name = self.cleaned_data.pop("first_name", None)
        last_name = self.cleaned_data.pop("last_name", None)
        # email = self.cleaned_data.pop("email")
        if avatar:
            if not user.avatar:
                user.avatar = UserAvatar()
            user.avatar.original = avatar
            user.avatar.save()
        # if email:
        #     if not user.user:
        #         user.user = User()
        #     user.user.email = email
        #     user.user.save()
        user.first_name = first_name
        user.last_name = last_name
        user.save()
        return user


class UserSignupForm(forms.ModelForm):
    email = forms.EmailField(
        validators=[validators.EmailValidator()],
        help_text=_("Write your email here...")
    )
    password1 = forms.CharField(label="Password", widget=forms.PasswordInput(render_value=True), help_text=_("Minimum 8 characters..."))
    password2 = forms.CharField(label="Confirm Password", widget=forms.PasswordInput(render_value=True), help_text=_("Rewrite password here..."))

    class Meta:
        model = dj_auth.get_user_model()
        fields = ("email", "password1", "password2",)

    def clean_email(self):
        email = self.cleaned_data["email"]
        user = dj_auth.get_user_model().objects.filter(email=email)
        if user.exists():
            raise ValidationError(_("User with email already exist"))
        return email

    def clean_password1(self):
        password = self.cleaned_data["password1"]
        password_validation.validate_password(password)
        return password
    
    def clean_password2(self):
        # Check that the two password entries match
        password1 = self.cleaned_data.get("password1")
        password2 = self.cleaned_data.get("password2")
        if password1 and password2 and password1 != password2:
            raise ValidationError("Passwords don't match")
        return password2

    def save(self, commit=True):
        user = dj_auth.get_user_model().objects.create_user(
            self.cleaned_data["email"],
            self.cleaned_data["password2"],
        )

        # if jwt_api_settings.UPDATE_LAST_LOGIN:
        #     update_last_login(None, user)
        
        if commit:
            user.save()
        
        send_mail.delay(enums.ACCOUNT_CONFIRMATION, user)
        return user


class UserAccountConfirmationForm(forms.Form):
    user = forms.CharField()
    token = forms.CharField()

    def clean(self):
        cleaned_data = super().clean()
        token = cleaned_data["token"]
        user_hash = cleaned_data["user"]
        user = get_object_or_404(User, id=user_hash)

        if not tokens.account_activation_token.check_token(user, token):
            raise ValidationError(_("Malformed user account confirmation token"))
        return {"user": user, "token": token}

    def save(self, commit=True):
        user = self.cleaned_data.pop("user")
        user.is_active = True
        if commit:
            user.save()
        return user


class UserAccountChangePasswordForm(PasswordChangeForm):
    new_password1 = forms.CharField(label="New Password", widget=forms.PasswordInput(render_value=False), help_text=_("Minimum of 8 characters..."))


class PasswordResetForm(forms.Form):
    email = forms.EmailField(
        validators=[validators.EmailValidator()],
        help_text=_("User e-mail...")
    )

    def clean(self):
        cleaned_data = super().clean()
        user = None
        try:
            user = dj_auth.get_user_model().objects.get(email=cleaned_data["email"])
        except dj_auth.get_user_model().DoesNotExist:
            pass

        return {**cleaned_data, 'user': user}

    def save(self, commit=True):
        user = self.cleaned_data.pop('user')
        if user:
            send_mail.delay(enums.PASSWORD_RESET, user)
        return user


class PasswordResetConfirmationForm(SetPasswordForm):
    new_password1 = forms.CharField(label="New Password", widget=forms.PasswordInput(render_value=False), help_text=_("Minimum of 8 characters..."))
    

@context_user_required
class VerifyOTPForm(forms.Form):
    otp_token = forms.CharField(help_text=_("Enter token here..."))

    def clean(self):
        otp_services.verify_otp(self.context_user, self.cleaned_data.get("otp_token", ""))
        return True


class ValidateOTPForm(forms.Form):
    user_id = forms.CharField(widget=forms.HiddenInput())
    otp_token = forms.CharField(help_text=_("Enter token here..."))
    
    def clean(self):
        cleaned_data = super().clean()
        user =  None
        try:
            user = User.objects.get(id=cleaned_data["user_id"])
        except:
            pass 
        return {"user": user, **cleaned_data}
    
    def clean(self):
        user = self.cleaned_data["user"]
        otp_token = self.cleaned_data["otp_token"]
        
        otp_services.validate_otp(user, otp_token)