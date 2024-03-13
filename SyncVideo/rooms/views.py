import json
from functools import wraps
from urllib.parse import urlparse, parse_qs

import requests
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.http import HttpResponse, JsonResponse, HttpResponseForbidden, HttpResponseNotFound, Http404
from django.shortcuts import render, redirect, get_object_or_404
from django.urls import reverse_lazy
from django.utils import timezone
from django.utils.decorators import method_decorator
from django.views.decorators.http import require_POST
from django.views.generic import CreateView

from SyncVideo import settings
from SyncVideo.common.util import is_ajax
from SyncVideo.rooms.forms import CreateRoomForm, EditRoomForm
from SyncVideo.rooms.models import Room, Video, ChatMessage
from SyncVideo.user_auth.models import AppUser


def protect_private_room(permission=None):

    def decorator(view_func):
        @wraps(view_func)
        def _wrapped_view(request, room_name, *args, **kwargs):
            try:
                room = Room.objects.get(url=room_name)
            except Room.DoesNotExist:
                return HttpResponseNotFound("Room not found")

            user = request.user

            if room.visibility == 'public' or user == room.creator or user in room.invited_users.all()\
                or permission is not None and user.has_perm(permission):
                return view_func(request, room_name, *args, **kwargs)
            return render(request, 'room/no_permission.html')

        return _wrapped_view
    return decorator


@method_decorator(login_required, name='dispatch')
class RoomCreateView(CreateView):
    model = Room
    form_class = CreateRoomForm
    template_name = 'room/create_room.html'

    def form_valid(self, form):
        form.instance.creator = self.request.user
        return super().form_valid(form)

    def get_success_url(self):
        print(self.object.url)
        return reverse_lazy('join room', kwargs={'room_name': self.object.url})


@login_required
def edit_room(request, room_name):
    room = Room.objects.get(url=room_name)

    if request.user.is_superuser or room.creator == request.user:
        if request.method == 'POST':
            form = EditRoomForm(request.POST, instance=room, user=request.user)
            if form.is_valid():
                form.save()
                return redirect('join room', room_name=room.url)

        form = EditRoomForm(instance=room)
        return render(request, 'room/edit_room.html', {'room': room, 'form': form})
    else:
        return render(request, '/')


@login_required
def delete_room(request, room_name):
    room = get_object_or_404(Room, url=room_name)

    if request.user.is_superuser or room.creator == request.user:
        if request.method == 'POST':
            room.delete()

            messages.success(request, 'Room deleted successfully.')
            return redirect('index')

        return render(request, 'room/delete_room.html', {'room': room})
    else:
        return redirect('index')


YOUTUBE_API_ENDPOINT = F'https://www.googleapis.com/youtube/v3/videos?id=%s&key={settings.YOUTUBE_API_KEY}&part=snippet'


@login_required
@protect_private_room(permission='rooms.change_video')
def set_video_playing(request, room_name, pk):
    """
    Set the currently playing video in a room by database ID.
    Determines and returns correct video ID (Youtube video ID or filename)
    """
    if is_ajax(request) and request.method == 'POST':
        Video.objects.filter(added_to__url=room_name, currently_playing=True).update(currently_playing=False)
        Video.objects.filter(pk=pk).update(currently_playing=True)

        video = Video.objects.get(pk=pk)
        video_id = video.file.name if video.file else video.video_id

        return JsonResponse({"video_id": video_id}, status=200)

    return JsonResponse({"error": "Not AJAX request"}, status=500)


@login_required
@protect_private_room(permission='rooms.delete_video')
def delete_video(request, room_name, pk):
    if request.method == 'DELETE' and is_ajax(request):
        Video.objects.filter(pk=pk).delete()

        return JsonResponse({"pk": pk}, status=200)
    return JsonResponse({"error": "Not AJAX request or Wrong request method"}, status=500)


@login_required
@protect_private_room(permission='rooms.add_video')
def upload_video_url_form(request, room_name):
    if request.method == 'POST' and is_ajax(request):
        video_url = request.POST.get('video_url', None)

        if not video_url:
            return JsonResponse({"error": "Video URL is missing"}, status=400)

        # parse youtube link
        url = urlparse(video_url)
        if not video_url.startswith('https'):
            return JsonResponse({"error": "link must be HTTPS"}, status=400)

        if url.netloc == 'youtu.be':
            video_url = url.path.replace('/', '')
        elif url.netloc == 'youtube.com' or url.netloc == 'www.youtube.com' or url.netloc == 'm.youtube.com':
            video_url = parse_qs(url.query)['v'][0]
        else:
            return JsonResponse({"error": "Unsupported provider: " + url.netloc}, status=400)

        if Video.objects.filter(video_id=video_url).exists():
            title = Video.objects.filter(video_id=video_url).first().title
        else:
            req = requests.get(url=YOUTUBE_API_ENDPOINT % video_url)
            data = json.loads(req.text.encode('utf-8'))

            if "items" not in data:
                print("Error reaching Youtube Data API")
                title = "Untitled"
            else:
                title = data['items'][0]['snippet']['title']

        try:
            video = Video.objects.create(
                video_id=video_url,
                added_to=Room.objects.get(url=room_name),
                added_by=request.user,
                provider="youtube",
                title=title
            )
        except Room.DoesNotExist:
            return JsonResponse({"error": "Room does not exist"}, status=400)

        return JsonResponse({"title": title, "pk": video.id, "provider": "youtube"})

    return JsonResponse({"error": "Not AJAX request"}, status=400)


@protect_private_room(permission='rooms.view_room')
def RoomView(request, room_name):
    room = Room.objects.get(url=room_name)
    videos = Video.objects.filter(added_to=room)
    current_video = Video.objects.filter(added_to=room, currently_playing=True).first()

    if current_video is not None:
        vid = current_video.video_id if current_video.video_id else current_video.file
    else:
        vid = None

    chat = ChatMessage.objects.filter(room=room)
    context = {
        'room': room,
        'playlist': videos,
        'current_video': vid,
        'chat': chat
    }

    return render(request,
                  'room/room.html',
                  context)


@login_required
@protect_private_room(permission='rooms.add_chatmessage')
def send_chat_message(request, room_name):
    """
    Save message object in the database
    If the most recent message was sent by the same user, append the new message
    to the existing message object rather than creating a new one.
    This makes the chat UI compact by consolidating consecutive messages from the same sender.
    """
    if request.method == 'POST':
        message_text = request.POST.get('message', '')
        if message_text:
            user = request.user
            room = Room.objects.get(url=room_name)
            chat_history = ChatMessage.objects.filter(room=room)
            if chat_history:
                latest_message = chat_history.latest('timestamp')
                if latest_message and latest_message.user == user:
                    # A single message can be at most 100 characters, so make the limit for 10 concatenated messages
                    if len(latest_message.message + '\n' + message_text) < 1000:
                        latest_message.message += '\n' + message_text
                        latest_message.timestamp = timezone.now()
                        latest_message.save()

                        return JsonResponse({'success': True})

            ChatMessage.objects.create(room=room, user=user, message=message_text)
        return JsonResponse({'success': True})
    else:
        return JsonResponse({'error: request not AJAX': 500})


@protect_private_room(permission='rooms.view_chatmessage')
def get_chat_history(request, room_name):
    """
    Retrieve the 50 latest chat messages for the room as HTML.
    """
    chat_history = ChatMessage.objects.filter(room__url=room_name)[:50]
    chat_html = render(request, 'room/partials/messages.html', {'chat': chat_history})
    return HttpResponse(chat_html)


import time

@login_required
@protect_private_room(permission='rooms.add_video')
def upload_video(request, room_name):
    """
    Handle file upload chunk by chunk.
    Create the video if upload is successful.
    """
    if request.method == 'POST':
        file = request.FILES['file'].read()
        file_name = request.POST['filename']
        existing_path = request.POST['existingPath']
        eof = request.POST['eof']
        next_slice = request.POST['nextSlice']
        title = request.POST['title']

        if file == "" or file_name == "" or existing_path == "" or eof == "" or next_slice == "":
            return JsonResponse({'data': 'Invalid Request'})
        else:
            if existing_path == 'undefined' or existing_path == 'null':
                unix_filename = str(int(time.time())) + ".webm"
                path = os.path.join(settings.MEDIA_ROOT, unix_filename)
                with open(path, 'wb+') as destination:
                    destination.write(file)

                video = Video()
                video.added_to = Room.objects.get(url=room_name)
                video.provider = "html5"
                video.title = title if len(title.split()) > 0 else "Untitled"
                video.file = unix_filename
                video.added_by = request.user
                video.save()

                if int(eof):
                    return JsonResponse({"title": video.title, "pk": video.id, "provider": "html5"})
                else:
                    return JsonResponse({'existingPath': unix_filename})
            else:
                path = os.path.join(settings.MEDIA_ROOT, existing_path)
                video = Video.objects.get(file=existing_path)
                with open(path, 'ab+') as destination:
                    destination.write(file)
                    if int(eof):
                        return JsonResponse({"title": video.title, "pk": video.id, "provider": "html5"})
                    else:
                        return JsonResponse({'existingPath': existing_path})
    return JsonResponse({'error:", "request not AJAX'}, 500)


import os

@protect_private_room(permission='rooms.view_video')
def serve_video(request, path):
    """
    Serve video so that it can be displayed dynamically on the webpage
    Only permitted users, or the uploader of the video, can view videos added to private rooms.
    """
    video = get_object_or_404(Video, file=path)
    room = video.added_to
    user = request.user

    if room.visibility == "private":
        if request.user.is_authenticated or user == room.creator or user == video.added_by or user.has_perm(
                'rooms.view_room') or user in room.invited_users.all():
            pass
        else:
            return HttpResponseNotFound()

    video_path = os.path.join(settings.MEDIA_ROOT, path)
    if os.path.exists(video_path):
        with open(video_path, 'rb') as f:
            response = HttpResponse(f.read(), content_type='video/webm')
    else:
        return HttpResponseNotFound()
    return response


@require_POST
def invite_user(request, room_name):
    user_id = request.POST.get("username")

    try:
        room = Room.objects.get(url=room_name)
        user_to_invite = AppUser.objects.get(username=user_id)

        if request.user != room.creator and not request.user.is_staff:
            return JsonResponse({"error": "Only room owners can invite users."}, status=400)

        if user_to_invite == room.creator:
            return JsonResponse({"error": "User cannot be room owner"}, status=400)

        if user_to_invite in room.invited_users.all():
            return JsonResponse({"error": "User was already invited"}, status=400)

        room.invited_users.add(user_to_invite)
        room.save()

        return JsonResponse({"message": "Invitation sent successfully"})
    except (Room.DoesNotExist, AppUser.DoesNotExist):
        return JsonResponse({"error": "Room or user not found"}, status=400)


@require_POST
def uninvite_user(request, room_name):
    user_id = request.POST.get("username")

    try:
        room = Room.objects.get(url=room_name)
        user_to_uninvite = AppUser.objects.get(username=user_id)

        if request.user != room.creator and not request.user.is_staff:
            return JsonResponse({"error": "Only room owners can uninvite users."}, status=400)

        if user_to_uninvite == room.creator:
            return JsonResponse({"error": "User cannot be room owner"}, status=400)

        if user_to_uninvite not in room.invited_users.all():
            return JsonResponse({"error": "User was not invited"}, status=400)

        room.invited_users.remove(user_to_uninvite)
        room.save()

        return JsonResponse({"message": "User uninvited successfully"})
    except (Room.DoesNotExist, AppUser.DoesNotExist):
        return JsonResponse({"error": "Room or user not found"}, status=400)

