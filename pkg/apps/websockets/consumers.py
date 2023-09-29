import json 
from channels.generic.websocket import AsyncWebsocketConsumer
from channels.db import database_sync_to_async

from django.template.loader import render_to_string
from apps.dashboard.models import Message

class NotificationConsumer(AsyncWebsocketConsumer):
    
    async def connect(self):
        self.group_name = "notifications"
        
        await self.accept()
        await self.channel_layer.group_add(self.group_name, self.channel_name)
    
    async def disconnect(self, close_code):
        await self.channel_layer.group_discard(self.group_name, self.channel_name)
        
    async def send_notification(self, event):
        message = event["message"]

        await self.send(
            text_data=json.dumps({
                "type": event["type"],
                "message": message
            })
        )


class ChatConsumer(AsyncWebsocketConsumer):
    async def connect(self):
        self.data_id = self.scope["url_route"]["kwargs"]["data_id"]
        self.room_group_name = "chat_%s" % self.data_id
        # Join room group
        await self.channel_layer.group_add(self.room_group_name, self.channel_name)
        await self.accept()
    
    async def disconnect(self, close_code):
        # Leave room group
        await self.channel_layer.group_discard(self.room_group_name, self.channel_name)
    
    # Receive message from WebSocket
    async def receive(self, text_data):
        text_data_json = json.loads(text_data)
        msg_id = text_data_json["msg_id"]
        # Send message to room group
        await self.channel_layer.group_send(
            self.room_group_name, {
                "type": "chat_message", 
                "msg_id": msg_id
            }
        )
    
    # Receive message from room group
    async def chat_message(self, event):
        msg_id = event["msg_id"]
        # Send message to WebSocket
        
        msg = await self.get_msg(msg_id)
        message = render_to_string(
            "dashboard/partials/_msg.html",
            {"msg": msg}
        )
        
        await self.send(text_data=json.dumps({"message": message}))
    
    @database_sync_to_async
    def get_msg(self, msg_id):
        return Message.objects.get(id=msg_id)