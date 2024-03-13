from channels.auth import AuthMiddlewareStack
from channels.routing import ProtocolTypeRouter, URLRouter
from django.core.asgi import get_asgi_application
from django.urls import re_path
from SyncVideo import consumers

# URLs that handle the WebSocket connection are placed here.
websocket_urlpatterns=[
        re_path(
            r'^ws/room/(?P<room_name>[^/]+)$', consumers.WatchRoomConsumer.as_asgi()
        ),
    ]


application = ProtocolTypeRouter({
  'websocket': AuthMiddlewareStack(
        URLRouter(
           websocket_urlpatterns
        )
    ),
})