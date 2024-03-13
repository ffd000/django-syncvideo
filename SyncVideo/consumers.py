import json

from channels.db import database_sync_to_async
from channels.generic.websocket import AsyncWebsocketConsumer

from SyncVideo.rooms.models import Room

_connected_users = {}
_guests = 0


class WatchRoomConsumer(AsyncWebsocketConsumer):
    def __init__(self, *args, **kwargs):
        super().__init__(args, kwargs)
        self.room_name = None
        self.room_group_name = None
        self.room = None
        self.user = None

    async def connect(self):
        self.room_name = self.scope['url_route']['kwargs']['room_name']
        self.room_group_name = f'room_{self.room_name}'
        self.room = await self.get_room()
        self.user = self.scope['user']

        global _guests

        # Add the user to the list of connected users in the room
        if self.room_group_name not in _connected_users:
            _connected_users[self.room_group_name] = {}
            _guests = 0

        if self.user.is_authenticated:
            if self.user.username not in _connected_users[self.room_group_name]:
                _connected_users[self.room_group_name][self.user.username] = self.channel_name
        else:
            _guests += 1

        await self.channel_layer.group_add(
            self.room_group_name,
            self.channel_name
        )

        await self.accept()

        await self.send_user_list()
        await self._request_timestamp()

    async def disconnect(self, close_code):
        global _guests

        if self.user.username in _connected_users[self.room_group_name]:
            del _connected_users[self.room_group_name][self.user.username]

        if not self.user.is_authenticated:
            _guests -= 1
            if _guests < 0:
                _guests = 0

        await self.send_user_list()

        # remove user from the room's group
        await self.channel_layer.group_discard(
            self.room_group_name,
            self.channel_name)


    async def _request_timestamp(self):
        first_socket_channel = self.get_first_socket(self.room_group_name)

        if first_socket_channel:
            # Send the message to the first connected socket
            await self.channel_layer.send(
                first_socket_channel,
                {
                    'type': 'timestamp_requested',
                    'socket': self.channel_name,
                }
            )

    async def timestamp_requested(self, event):
        socket_channel = event.get('socket')

        if not socket_channel or socket_channel == self.channel_name:
            return

        # notify the client that timestamp has been requested of it
        await self.send(text_data=json.dumps({
            'type': 'timestamp_requested',
        }))

    """
    Handler receives messages from client (browser) and broadcasts them to other consumers.
    Messages sent by Consumer with self.send are handled in Javascript.
    """
    async def receive(self, text_data):
        json_data = json.loads(text_data)

        # broadcast to all clients in room
        await self.channel_layer.group_send(
            self.room_group_name, {
                "type": "broadcast_message",
                "payload": json_data
            })

    async def send_user_list(self):
        global _guests
        if self.room_group_name in _connected_users:
            user_list = list(_connected_users[self.room_group_name].keys())
        else:
            user_list = []

        json_data = {
            'type': 'user_list',
            'users': user_list,
            'guests': _guests
        }

        await self.channel_layer.group_send(
            self.room_group_name, {
                "type": "broadcast_message",
                "payload": json_data
            })

    def get_first_socket(self, group_name):
        # Get all channel names in the group
        channel_names = [channel_name for user, channel_name in _connected_users[group_name].items() if user != self.user.username]

        return channel_names[0] if channel_names else None

    async def send_timestamp_request(self):
        # Send the timestamp request to the connected socket
        await self.send(text_data=json.dumps({'type': 'request_timestamp'}))

    async def send_timestamp(self, event):
        # Send the timestamp to the connected socket
        timestamp = event['timestamp']
        await self.send(text_data=json.dumps({'type': 'receive_timestamp', 'timestamp': timestamp}))

    async def broadcast_message(self, event):
        await self.send(text_data=json.dumps(event['payload']))

    @database_sync_to_async
    def get_room(self):
        return Room.objects.get(url=self.room_name)
