from django.contrib import admin
from django.urls import path, include

urlpatterns = [
    path('admin/', admin.site.urls),
    path('', include('SyncVideo.common.urls')),
    path('accounts/', include('SyncVideo.user_auth.urls')),
    path('room/', include('SyncVideo.rooms.urls')),
]

handler404 = 'SyncVideo.common.views.handler404'