from pathlib import Path
from django.core.management.utils import get_random_secret_key
from django.contrib import messages

import sys
import os
import datetime
import environ
import dj_database_url

# Build paths inside the project like this: BASE_DIR / 'subdir'.
BASE_DIR = Path(__file__).resolve().parent.parent.parent

env = environ.Env(
    # set casting, default value
    DEBUG=(bool, False),
)

# Take environment variables from .env file
environ.Env.read_env(os.path.join(BASE_DIR, '.env'))

# Quick-start development settings - unsuitable for production

SECRET_KEY = env("DJANGO_SECRET_KEY", default=get_random_secret_key())

# SECURITY WARNING: don't run with debug turned on in production!
DEBUG = env('DEBUG')

ALLOWED_HOSTS = env.list("DJANGO_ALLOWED_HOSTS", default=["127.0.00.1", "localhost", "api.localhost", "admin.localhost"])


DEVELOPMENT_MODE = env.bool("DEVELOPMENT_MODE", default=True)

# Application definition

INSTALLED_APPS = [
    "daphne",
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'django.contrib.sites',
    
    # Internal Apps 
    "apps.users",
    "apps.finances",
    "apps.notifications",
    "apps.websockets",
    
    # External Apps 
    "channels",
    'django_hosts',
    "rest_framework_simplejwt.token_blacklist",
    "storages",
    "djstripe",
    "widget_tweaks",
    # social apps
    'allauth',
    'allauth.account',
    'allauth.socialaccount',
    'allauth.socialaccount.providers.google',
    'allauth.socialaccount.providers.facebook',
    "django_htmx",
]


#-----------------------------------
# DJANGO-ALLAUTH SETTINGS
#-----------------------------------
SITE_ID = 1
# Provider specific settings
SOCIALACCOUNT_PROVIDERS = {
    'google': {
        # For each OAuth based provider, either add a ``SocialApp``
        # (``socialaccount`` app) containing the required client
        # credentials, or list them here:
        'APP': {
            'client_id': env("GOOGLE_AUTH_CLIENT_ID", default=""),
            'secret': env("GOOGLE_AUTH_SECRET_KEY", default=""),
            'key': env("GOOGLE_AUTH_KEY", default=""),
        },
        'SCOPE': ['profile', 'email'],
        'AUTH_PARAMS': {
            'access_type': 'online',
        },
        'OAUTH_PKCE_ENABLED': True,
    },
    'facebook': {
        'APP': {
            'client_id': env("FACEBOOK_AUTH_CLIENT_ID", default=""),
            'secret': env("FACEBOOK_AUTH_SECRET_KEY", default=""),
            'key': env("FACEBOOK_AUTH_KEY", default="")
        },
        'METHOD': 'oauth2',
        'SCOPE': ['email', 'public_profile'],
        'INIT_PARAMS': {'cookie': True},
        'FIELDS': [
            'id',
            'first_name',
            'last_name',
            'picture',
        ],
        'EXCHANGE_TOKEN': True,
        'VERIFIED_EMAIL': False,
        'GRAPH_API_URL': 'https://graph.facebook.com/v13.0',
    },
}
ACCOUNT_USER_MODEL_USERNAME_FIELD = None
ACCOUNT_EMAIL_REQUIRED = True
ACCOUNT_USERNAME_REQUIRED = False
ACCOUNT_AUTHENTICATION_METHOD = 'email'
ACCOUNT_LOGOUT_ON_PASSWORD_CHANGE = env.bool("LOGOUT_ON_PASSWORD_CHANGE", default=True)
ACCOUNT_RATE_LIMITS = {
    # Change password view (for users already logged in)
    "change_password": "5/m",
    # Email management (e.g. add, remove, change primary)
    "manage_email": "10/m",
    # Request a password reset, global rate limit per IP
    "reset_password": "20/m",
    # Rate limit measured per individual email address
    "reset_password_email": "5/m",
    # Password reset (the view the password reset email links to).
    "reset_password_from_key": "20/m",
    # Signups.
    "signup": "20/m",
    # Login 
    "login": "3/m",
}


MIDDLEWARE = [
    # Django-hosts config
    'django_hosts.middleware.HostsRequestMiddleware',
    'django.middleware.security.SecurityMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
    "django_htmx.middleware.HtmxMiddleware",
    # allauth middleware
    "allauth.account.middleware.AccountMiddleware",
    # Django-hosts config
    'django_hosts.middleware.HostsResponseMiddleware',
]

#-----------------------------------
# DJANGO-HOSTS SETTINGS
#+-----------------------------------
ROOT_URLCONF = 'config.urls.main'
ROOT_HOSTCONF = "config.hosts"
DEFAULT_HOST = "main"
PARENT_HOST = "localhost:8000"


#-----------------------------------
# DJANGO TEMPLATES SETTINGS
#+-----------------------------------
TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [BASE_DIR / "templates"],
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.debug',
                'django.template.context_processors.request',
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',
            ],
        },
    },
]


#-----------------------------------
# APPLICATION SETTINGS
#-----------------------------------
ASGI_APPLICATION = "config.asgi.application"
WSGI_APPLICATION = 'config.wsgi.application'
    

#-----------------------------------
# EMAIL SETTINGS
#-----------------------------------
DEFAULT_FROM_EMAIL = env("AWS_SES_FROM_EMAIL")
# https://docs.djangoproject.com/en/dev/ref/settings/#server-email
SERVER_EMAIL = env("SERVER_EMAIL", default=DEFAULT_FROM_EMAIL)
# https://docs.djangoproject.com/en/dev/ref/settings/#email-subject-prefix
EMAIL_SUBJECT_PREFIX = env("EMAIL_SUBJECT_PREFIX", default="[SaaS]")


#-----------------------------------
# AWS SES SETTINGS(EMAIL)
#-----------------------------------
AWS_SES_ACCESS_KEY_ID = env("AWS_SES_ACCESS_KEY_ID")
AWS_SES_SECRET_ACCESS_KEY = env("AWS_SES_SECRET_ACCESS_KEY")
AWS_SES_REGION_NAME = env("AWS_SES_REGION_NAME")
AWS_SES_REGION_ENDPOINT = f"email.{AWS_SES_REGION_NAME}.amazonaws.com"
AWS_SES_FROM_EMAIL = env("AWS_SES_FROM_EMAIL", default="")
USE_SES_V2 = True


#-----------------------------------
# MY SITE SETTINGS
#-----------------------------------
DOMAIN = env("DOMAIN", default="localhost")
SITE_NAME = env("SITE_NAME", default="Saas Boilerplate")


#-----------------------------------
# PASSWORD SETTINGS & AUTHENTICATION 
#-----------------------------------
AUTH_PASSWORD_VALIDATORS = [
    {
        'NAME': 'django.contrib.auth.password_validation.UserAttributeSimilarityValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.CommonPasswordValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.NumericPasswordValidator',
    },
]

AUTHENTICATION_BACKENDS = [
    # Needed to login by username in Django admin, regardless of `allauth`
    'django.contrib.auth.backends.ModelBackend',
    # `allauth` specific authentication methods, such as login by e-mail
    'allauth.account.auth_backends.AuthenticationBackend',
]

PASSWORD_HASHERS = env.list(
    "DJANGO_PASSWORD_HASHERS",
    default=[
        'django.contrib.auth.hashers.PBKDF2PasswordHasher',
        'django.contrib.auth.hashers.PBKDF2SHA1PasswordHasher',
        'django.contrib.auth.hashers.Argon2PasswordHasher',
        'django.contrib.auth.hashers.BCryptSHA256PasswordHasher',
    ],
)

#-----------------------------------
# INTERNATIONALIZATION
#-----------------------------------

LANGUAGE_CODE = 'en-us'

TIME_ZONE = 'UTC'

USE_I18N = True

USE_TZ = True
    

# Default primary key field type

DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'

HASHID_FIELD_SALT = env("HASHID_FIELD_SALT", default=get_random_secret_key())

AUTH_USER_MODEL = "users.User"

LOGIN_REDIRECT_URL = "/users/profile/"

LOGIN_URL = "/users/login/"

RATELIMIT_IP_META_KEY = "common.utils.get_client_ip"

NOTIFICATIONS_STRATEGIES = ["InAppNotificationStrategy"]


#-----------------------------------
# LOGGING 
#-----------------------------------
ADMINS = [DEFAULT_FROM_EMAIL]
LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'handlers': {
        'console': {
            'class': 'logging.StreamHandler',
        },
        "mail_admins": {
            "level": "ERROR",
            "class": "django.utils.log.AdminEmailHandler",
            "include_html": True,
        },
    },
    'root': {
        'handlers': ['console'],
        'level': env('DJANGO_LOG_LEVEL', default='INFO'),
    },
    'loggers': {
        '*': {
            'handlers': ['console'],
            'level': env('DJANGO_LOG_LEVEL', default='INFO'),
            'propagate': False,
        },
    },
}


#-----------------------------------
# MESSAGE TAGS 
#-----------------------------------
MESSAGE_TAGS = {
    messages.DEBUG: "debug",
    messages.INFO: "info",
    messages.SUCCESS: "success",
    messages.WARNING: "warning",
    messages.ERROR: "danger",
}


#-----------------------------------
# OTP 
#-----------------------------------
OTP_AUTH_ISSUER_NAME = SITE_NAME
OTP_AUTH_TOKEN_COOKIE = 'otp_token'
OTP_AUTH_TOKEN_LIFETIME_MINUTES = datetime.timedelta(minutes=env('OTP_AUTH_TOKEN_LIFETIME_MINUTES', default=5))
OTP_VALIDATE_PATH = "/auth/validate-otp"


#-----------------------------------
# DJ-STRIPE 
#-----------------------------------
STRIPE_LIVE_MODE = env.bool("STRIPE_LIVE_MODE", default=False)
DJSTRIPE_WEBHOOK_SECRET = env("DJSTRIPE_WEBHOOK_SECRET")  # We don't use this, but it must be set
DJSTRIPE_USE_NATIVE_JSONFIELD = False
DJSTRIPE_FOREIGN_KEY_TO_FIELD = "id"
DJSTRIPE_WEBHOOK_VALIDATION="retrieve_event" # verify_signature
# DJSTRIPE_SUBSCRIBER_MODEL = "users.Profile"
STRIPE_CHECKS_ENABLED = env.bool("STRIPE_CHECKS_ENABLED", default=True)
if not STRIPE_CHECKS_ENABLED:
    SILENCED_SYSTEM_CHECKS.append("djstripe.C001")
    
    
#-----------------------------------
# SUBSCRIPTION
#-----------------------------------
SUBSCRIPTION_ENABLE = env.bool("SUBSCRIPTION_ENABLE", default=True)
SUBSCRIPTION_HAS_FREE_PLAN = env.bool("SUBSCRIPTION_HAS_FREE_PLAN", default=False)
SUBSCRIPTION_HAS_TRIAL_PLAN = env.bool("SUBSCRIPTION_HAS_TRIAL_PLAN", default=True)
SUBSCRIPTION_TRIAL_PRICE_ID = env("SUBSCRIPTION_TRIAL_PRICE_ID", default="")
SUBSCRIPTION_FREE_PRICE_ID = env("SUBSCRIPTION_FREE_PRICE_ID", default="")
SUBSCRIPTION_TRIAL_PERIOD_DAYS = env.int("SUBSCRIPTION_TRIAL_PERIOD_DAYS", default=7)


#-----------------------------------
# AWS WORKER 
#-----------------------------------
TASKS_BASE_HANDLER = env("TASKS_BASE_HANDLER", default="common.tasks.Task")
WORKERS_EVENT_BUS_NAME = env("WORKERS_EVENT_BUS_NAME", default=None)
AWS_ENDPOINT_URL = env("AWS_ENDPOINT_URL", default=None)
TASKS_LOCAL_URL = env("TASKS_LOCAL_URL", default=None)


#-----------------------------------
# USER FILE 
#-----------------------------------
UPLOADED_DOCUMENT_SIZE_LIMIT = env.int("UPLOADED_DOCUMENT_SIZE_LIMIT", default=10 * 1024 * 1024)
USER_DOCUMENTS_NUMBER_LIMIT = env.int("USER_DOCUMENTS_NUMBER_LIMIT", default=10)

