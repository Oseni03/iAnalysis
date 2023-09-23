import os
import boto3
import json
from datetime import datetime

from django.conf import settings
from django.template.loader import render_to_string


client = boto3.client('ses')


def send_email(event, context):
    detail_type = event.get("DetailType")
    source = event.get("Source")
    event_bus = event.get("EventBusName")
    detail = event.get("Detail")
    
    to = detail.get("to")
    elif detail_type == "SUBSCRIPTION_ERROR":
        body_html = render_to_string(
            "emails/subscription_error.html",
            detail
        )
        subject = "Subscription Error"
    elif detail_type == "ACCOUNT_ACTIVATION":
        body_html = render_to_string(
            "users/emails/account_confirmation.html",
            detail
        )
        subject = "Account Confirmation"
    elif detail_type == "PASSWORD_RESET":
        body_html = render_to_string(
            "users/emails/password_reset.html",
            detail
        )
        subject = "Password Reset"
    elif detail_type == "TRIAL_EXPIRES_SOON":
        body_html = render_to_string(
            "finances/emails/trial_expiring.html",
            detail
        )
        subject = "Trial expires soon!"
    
    email_message = {
        'Body': {
            'Html': {
                'Charset': 'utf-8',
                'Data': body_html,
            },
        },
        'Subject': {
            'Charset': 'utf-8',
            'Data': subject,
        },
    }

    client.send_email(
        Destination={
            'ToAddresses': [to],
        },
        Message=email_message,
        Source=settings.DEFAULT_FROM_EMAIL,
    )