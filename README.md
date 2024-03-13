# SyncVideo Project Defense

2023

SyncVideo is a simple and easy-to-use Django-based platform for watching videos and movies together with friends in real time through user-created virtual rooms. It integrates with YouTube and uses the YouTube API for pulling video information, as well as allowing users to upload their own videos in WebM format directly for instant viewing. Each room is provided with a real-time chat feature to enhance the social aspect. It leverages the WebSocket protocol through the django channels module to achieve real-time synchronization of video playback across all connected users. In addition to using PostgreSQL for persistent data management, Redis serves as a very fast in-memory data store for caching in the channel layer backend.

## 3rd-party libraries used:
- channels & channels-redis
- crispy-forms
- videojs
- bootstrap
- whitenoise

## Deployment

It's deployed on Render at https://syncvideo.onrender.com.

## Run locally

Start docker:

    docker compose up

Install and start django:
    
    pip install -r requirements.txt
    python manage.py runserver 8000

You must change Postgres and Redis URL/credentials in settings.py.
