import os

from django.core.asgi import get_asgi_application
from channels.auth import AuthMiddlewareStack
from channels.routing import ProtocolTypeRouter, URLRouter
from channels.security.websocket import AllowedHostsOriginValidator

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings.development')

from apps.websockets import routing

application = ProtocolTypeRouter({
    # Django's ASGI application to handle traditional HTTP requests
    "http": get_asgi_application(),
    # # websocket handler
    "websocket": AllowedHostsOriginValidator(
        AuthMiddlewareStack(URLRouter(
            routing.websocket_urlpatterns
        )),
    )
})