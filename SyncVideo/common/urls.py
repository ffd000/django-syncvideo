from django.urls import path

from SyncVideo.common.views import index, search_rooms

urlpatterns = [
    path('', index, name="index"),
    path("search_rooms/", search_rooms, name='search_rooms'),
]