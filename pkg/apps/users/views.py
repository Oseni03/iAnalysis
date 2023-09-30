from django.conf import settings
from django.shortcuts import render, redirect
from django.shortcuts import get_object_or_404
from django.contrib.auth import get_user_model
from django.urls import reverse
from django.urls import reverse_lazy
from django.contrib import messages
from django.contrib.auth import logout
from django.contrib.auth import authenticate, login
from django.contrib.auth.decorators import login_required
from django.contrib.auth.mixins import LoginRequiredMixin
from django.views.generic.edit import FormView
from django.views.generic import View
from django.utils.decorators import method_decorator

from allauth.decorators import rate_limit
from allauth.core import ratelimit

import qrcode

from . import forms, models, tokens, jwt, decorators, utils
from .services import otp as otp_services


# Create your views here.
@method_decorator(decorators.authentication_not_required, name="dispatch")
@method_decorator(rate_limit(action="login"), name="dispatch")
class LoginView(FormView):
    form_class = forms.UserLoginForm
    template_name = "users/login.html" 
    success_url = reverse_lazy("users:profile")
    
    def post(self, request, *args, **kwargs):
        form_class = self.get_form_class()
        form = self.get_form(form_class)
        if form.is_valid():
            return self.form_valid(form)
        else:
            return self.form_invalid(form)
        
    def form_valid(self, form):
        password = form.cleaned_data["password"]
        email = form.cleaned_data["email"]
        
        user = authenticate(username=email, password=password)
        
        if user is not None:
            if user.is_active:
                if user.otp_enabled and user.otp_verified:
                    context = {
                        "form": forms.ValidateOTPForm(initial={"user_id": user.id})
                    }
                    return render(request, "users/validate_otp.html", context)
                else:
                    login(self.request, user)
                    messages.success(self.request, "Login successful!")
            else:
                messages.info(self.request, "Check your emaill to activate your account!")
        else:
            messages.error(self.request, "Invalid credentials")
        return super().form_valid(form)


class LogoutView(LoginRequiredMixin, View):
    def get(self, request, *args, **kwargs):
        logout(request)
        return render(request, "users/login.html")


class UserProfileView(LoginRequiredMixin, View):
    
    def get(self, request, *args, **kwargs):
        profile = models.UserProfile.objects.prefetch_related("user", "avatar").get(user=request.user)
        profile_data = {
            "first_name": profile.first_name,
            "last_name": profile.last_name,
            # "email": request.user.email,
            "avatar": profile.avatar,
        }
        context = {
            "profile": profile, 
            "profile_form": forms.UserProfileForm(initial=profile_data),
            "password_change_form": forms.UserAccountChangePasswordForm(request.user),
        }
        if settings.SUBSCRIPTION_ENABLE:
            context["subscription"] = True
        else:
            context["subscription"] = False
        return render(request, "users/profile.html", context)
    
    def post(self, request, *args, **kwargs):
        profile = models.UserProfile.objects.prefetch_related("user", "avatar").get(user=request.user)
        profile_data = {
            "first_name": profile.first_name,
            "last_name": profile.last_name,
            # "email": request.user.email,
            "avatar": profile.avatar,
        }
        
        update_form = forms.UserProfileForm(request.POST, initial=profile_data)
        if update_form.has_changed():
            if update_form.is_valid():
                avatar = update_form.cleaned_data.get("avatar", None)
                if avatar:
                    update_form.validate_avatar(avatar)
                update_form.update(profile)
                messages.success(request, "Profile update successful!")
            else:
                for error in update_form.errors.values():
                    messages.error(request, error)
        
        context = {
            "profile": profile, 
            "profile_form": update_form,
            "password_change_form": forms.UserAccountChangePasswordForm(request.user),
        }
        
        if request.POST.get("new_password1"):
            password_change_form = forms.UserAccountChangePasswordForm(user=request.user, data=request.POST)
            if password_change_form.is_valid():
                password_change_form.save()
                utils.logout_on_password_change(request, request.user)
                messages.success(request, "Password change successful!")
            else:
                for error in password_change_form.errors.values():
                    messages.error(request, error)
            context["password_change_form"] = password_change_form
        return render(request, "users/profile.html", context)


@method_decorator(decorators.authentication_not_required, name="dispatch")
@method_decorator(rate_limit(action="signup"), name="dispatch")
class SignUpView(FormView):
    form_class = forms.UserSignupForm
    template_name = "users/signup.html" 
    success_url = reverse_lazy("users:profile")
    
    def post(self, request, *args, **kwargs):
        form_class = self.get_form_class()
        form = self.get_form(form_class)
        if form.is_valid():
            return self.form_valid(form)
        else:
            for error in form.errors.values():
                messages.error(request, error) 
            return self.form_invalid(form)
        
    def form_valid(self, form):
        form.save()
        return super().form_valid(form)


def account_confirmation(request, user, token):
    form = forms.UserAccountConfirmationForm(data={"user": user, "token": token})
    if form.is_valid():
        form.save()
        messages.success(request, "Account verification successful!")
        return redirect(reverse('users:profile'))
    for error in form.errors.values():
        messages.error(request, error)
    return redirect(reverse('users:login'))


@method_decorator(rate_limit(action="reset_password"), name="dispatch")
@method_decorator(decorators.authentication_not_required, name="dispatch")
class PasswordResetView(FormView):
    form_class = forms.PasswordResetForm
    template_name = "users/password_reset.html" 
    success_url = reverse_lazy("users:login") 
    
    def post(self, request, *args, **kwargs):
        form_class = self.get_form_class()
        form = self.get_form(form_class)
        if form.is_valid():
            return self.form_valid(form)
        else:
            for error in form.errors.values():
                messages.error(request, error) 
            return self.form_invalid(form)
    
    def form_valid(self, form):
        r429 = ratelimit.consume_or_429(
            self.request,
            action="reset_password_email",
            key=form.cleaned_data["email"].lower(),
        )
        if r429:
            return r429
        form.save()
        messages.info(self.request, "Email has been sent your email with instructions to reset your password")
        return super(PasswordResetView, self).form_valid(form)


def password_reset_confirm(request, user, token):
    user = get_object_or_404(models.User, id=user)
    
    if not tokens.password_reset_token.check_token(user, token):
        messages.error(request, "Malformed password reset token")
        return redirect("users:password_reset")
    if request.method == "POST":
        form = forms.PasswordResetConfirmationForm(user, request.POST)
        if form.is_valid():
            form.save()
            jwt.blacklist_user_tokens(user)
            messages.success(request, "Password reset successful!")
            return redirect("users:login")
        for error in form.errors.values():
            messages.error(request, error)
    form = forms.PasswordResetConfirmationForm(user)
    return render(request, "users/password_reset_confirm.html", {"form": form})


def get_qrcode_path(hashid):
    path = settings.BASE_DIR / "static" / "img" / "qrcode" / f"{hashid}.png"
    return path, f"img/qrcode/{hashid}.png"


class GenerateOTP(LoginRequiredMixin, FormView):
    """
    Enabling two-factor authentication with authentication app
    """
    
    form_class = forms.VerifyOTPForm
    template_name = "users/generate_otp.html" 
    success_url = reverse_lazy("users:profile") 
    
    def get_context_data(self, *args, **kwargs):
        context = super().get_context_data(*args, **kwargs)
        
        otp_base32, otp_auth_url = otp_services.generate_otp(self.request.user)
        qrcode_img_path, img_name = get_qrcode_path(self.request.user.id.hashid)
        print(otp_auth_url)
        qrcode.make(otp_auth_url).save(qrcode_img_path)
        
        context["img_name"] = img_name
        context["otp_auth_url"] = otp_auth_url
        return context
    
    def post(self, request, *args, **kwargs):
        form_class = self.get_form_class()
        form = self.get_form(form_class)
        if form.is_valid():
            return self.form_valid(form)
        else:
            for error in form.errors.values():
                messages.error(request, error)
            return self.form_invalid(form)
        
    def form_valid(self, form):
        return super().form_valid(form)


class ValidateOTP(FormView):
    """
        2FA Authentication 
    """
    
    form_class = forms.ValidateOTPForm
    template_name = "users/validate_otp.html" 
    success_url = reverse_lazy("users:profile") 
    
    def post(self, request, *args, **kwargs):
        form_class = self.get_form_class()
        form = self.get_form(form_class)
        if form.is_valid():
            return self.form_valid(form)
        else:
            for error in form.errors.values():
                messages.error(request, error)
            return self.form_invalid(form)
        
    def form_valid(self, form):
        login(self.request, user)
        messages.success(self.request, "Login successful!")
        return super().form_valid(form)


@login_required
def disableOTP(request):
    otp_services.disable_otp(request.user)
    messages.success(request, "OTP authentication disabled successfully!")
    return redirect(reverse("users:profile"))