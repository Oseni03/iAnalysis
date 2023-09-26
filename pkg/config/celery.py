"""
Celery config file

https://docs.celeryproject.org/en/stable/django/first-steps-with-django.html

"""
from __future__ import absolute_import
import os
from celery import Celery
from django.conf import settings
from django.template.loader import render_to_string
from django.core.mail import send_mail

from apps.users import tokens

import enums

# This code is a copy of manage.py.
# Set the "celery Django" app's default Django settings module.
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings.development')

# you change the name here -Django Celery
app = Celery("config")

# read configuration from Django settings, creating celery Django with the CELERY namespace
# config keys have the prefix "CELERY" Django Celery
app.config_from_object('django.conf:settings', namespace='CELERY')

# load tasks.py in django apps - Django Celery
app.autodiscover_tasks(lambda: settings.INSTALLED_APPS)


@app.task
def send_mail(type: enums.EmailType, user: settings.AUTH_USER_MODEL, **kwargs):
    data={
        "domain": settings.DOMAIN,
        "site_name": settings.SITE_NAME,
        'user_id': user.id.hashid,
        **kwargs
    }
    if type == enums.ACCOUNT_CONFIRMATION:
        data["token"] = tokens.account_activation_token.make_token(user)
        subject = "Activate your Account"
        message = render_to_string(
            "users/emails/account_confirmation.html",
            data
        )
    elif type == enums.PASSWORD_RESET:
        data["token"] = tokens.password_reset_token.make_token(user)
        subject = "Reset your password"
        message = render_to_string(
            "users/emails/password_reset.html",
            data
        )
    elif type == enums.TRIAL_EXPIRES_SOON:
        subject = "Trial expires soon"
        message = render_to_string(
            "finances/emails/trial_expiring.html",
            data
        )
    elif type == enums.SUBSCRIPTION_ERROR:
        subject = "Subscription failure"
        message = render_to_string(
            "finances/emails/subscription_error.html",
            data
        )
    
    send_mail(subject, message, settings.DEFAULT_FROM_EMAIL, [user.email])
