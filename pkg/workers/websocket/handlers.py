import os
import json

from channels.layers import get_channel_layer
from asgiref.sync import async_to_sync


def send_notification(event, context):
    detail_type = event.get("DetailType")
    source = event.get("Source")
    event_bus = event.get("EventBusName")
    detail = event.get("Detail")
    
    channel_layer = get_channel_layer()
    async_to_sync(channel_layer.group_send)(
        detail.get("channel", "notification"),
        {
            "type": "detail_type",
            "message": detail.get("message")
        }
    )