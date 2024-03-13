from django.apps import AppConfig


class RoomsConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'SyncVideo.rooms'

    def ready(self):
        import SyncVideo.rooms.signals
