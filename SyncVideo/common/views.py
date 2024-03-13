from django.db.models import Q
from django.http import HttpResponse
from django.shortcuts import render
from django.template.loader import render_to_string

from SyncVideo.common.util import is_ajax
from SyncVideo.rooms.models import Room


def get_allowed_rooms(user):
    if user.has_perm('rooms.view_room'):
        return Room.objects.all()

    public_rooms = Room.objects.filter(visibility='public')
    private_rooms = Room.objects.filter(visibility='private', invited_users__in=[user.id] if user.is_authenticated else [])
    print(private_rooms)
    user_owned_rooms = Room.objects.filter(creator=user.id)

    allowed_rooms = (public_rooms | private_rooms | user_owned_rooms).distinct()

    return allowed_rooms


def index(request):
    user = request.user
    allowed_rooms = get_allowed_rooms(user).order_by('url')
    context = {"rooms": allowed_rooms}

    return render(request, 'common/home-page.html', context)


def search_rooms(request):
    if request.method == 'GET' and is_ajax(request):
        search_query = request.GET.get('search')

        allowed_rooms = get_allowed_rooms(request.user).filter(
            Q(url__icontains=search_query) |
            Q(description__icontains=search_query) |
            Q(categories__name__icontains=search_query)
        ).distinct().order_by('url')

        html = render_to_string('common/partials/search_rooms.html',
                                {'rooms': allowed_rooms})

        return HttpResponse(html)


def handler404(request, exception):
    return render(request, 'common/404.html', status=404)