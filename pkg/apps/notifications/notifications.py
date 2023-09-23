import logging

from common import websockets
from . import websocket_serializers

logger = logging.getLogger(__name__)


class UserNotification(websockets.Websocket):
    def __init__(self, user, data=None):
        channel = self.get_channel(user)
        super().__init__(channel=channel, data=data)
    
    def get_channel(self, user):
        return "notifications"


class SendUserNotification(UserNotification):
    name = 'NOTIFICATION'
    serializer_class = websocket_serializers.NotificationSerializer
