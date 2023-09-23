from django.urls import path, re_path, include

from . import views

app_name = "users"

urlpatterns = [
    path("login/", views.LoginView.as_view(), name="login"),
    path("logout/", views.LogoutView.as_view(), name="logout"),
    path("profile/", views.UserProfileView.as_view(), name="profile"),
    path("signup/", views.SignUpView.as_view(), name="signup"),
    path("activation/<user>/<token>/", views.account_confirmation, name="activation"),
    path("password-reset/", views.PasswordResetView.as_view(), name="password_reset"),
    path("password-reset/<user>/<token>/", views.password_reset_confirm, name="password_reset_confirm"),
    
    ## OTP URLS
    path("generate-otp/", views.GenerateOTP.as_view(), name="generate_OTP"),
    path("validate-otp/", views.ValidateOTP.as_view(), name="validate_OTP"),
    path("disable-otp/", views.disableOTP, name="disable_OTP"),
]