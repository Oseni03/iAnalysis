from django.db.models.signals import post_save
from django.dispatch import receiver
from django.conf import settings

from . import models


@receiver(post_save, sender=models.Notification)
def notify_about_entry(sender, instance: models.Notification, created, update_fields, **kwargs):
    if created:
        channel_layer = get_channel_layer()
        async_to_sync(channel_layer.group_send)(
            "notifications",
            {
                "type": "send_notification",
                "message": "New notification"
            }
        )
        
