import importlib
from django.conf import settings

module_name, package = settings.TASKS_BASE_HANDLER.rsplit(".", maxsplit=1)
Task = getattr(importlib.import_module(module_name), package)


class SendWebsocket(Task):
    def __init__(self, name: str):
        super().__init__(name=name, source='backend.websocket')
    
    def apply(self, channel: str, data, due_date=None):
        if data is None:
            data = {}

        super().apply(
            {
                "channel": channel,
                **data,
            },
            due_date,
        )


class BaseWebsocket:
    serializer_class = None

    def get_serializer(self, *args, **kwargs):
        serializer_class = self.get_serializer_class()
        if serializer_class is None:
            return None
        kwargs.setdefault('context', self.get_serializer_context())
        return serializer_class(*args, **kwargs)

    def get_serializer_class(self):
        return self.serializer_class

    def get_serializer_context(self):
        """
        Extra context provided to the serializer class.
        """
        return {}


class Websocket(BaseWebsocket):
    name = None

    def __init__(self, channel, data=None):
        self.channel = channel
        self.data = data
        if data is None:
            self.data = {}

    def send(self, due_date=None):
        send_data = None

        serializer = self.get_serializer(data=self.data)
        if serializer:
            serializer.is_valid(raise_exception=True)
            send_data = serializer.data

        ws_task = SendWebsocket(self.name)
        ws_task.apply(channel=self.channel, data=send_data, due_date=due_date)
        