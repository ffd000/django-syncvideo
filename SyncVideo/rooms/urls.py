from django.urls import path, include

from SyncVideo.rooms import views

urlpatterns = [
    path('create/', views.RoomCreateView.as_view(), name='create room'),
    path('<slug:room_name>/', include([
        path('watch/', views.RoomView, name='join room'),
        path('edit/', views.edit_room, name='edit room'),
        path('delete/', views.delete_room, name='delete room'),
        path('video_url/', views.upload_video_url_form, name='upload video url'),
        path('set_playing/<int:pk>/', views.set_video_playing, name='set video playing'),
        path('send_message/', views.send_chat_message, name='send message'),
        path('chat_messages/', views.get_chat_history, name='messages'),
        path('invite/', views.invite_user, name='invite user'),
        path('uninvite/', views.uninvite_user, name='uninvite user'),
        path('delete_video/<int:pk>/', views.delete_video, name='delete video'),
        path('upload/', views.upload_video, name='upload video'),
    ])),
    path('media/<path:path>/', views.serve_video, name='serve video'),
]