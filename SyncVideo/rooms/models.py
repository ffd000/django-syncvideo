from django.core.exceptions import ValidationError
from django.core.validators import FileExtensionValidator
from django.db import models

from SyncVideo.user_auth.models import AppUser

from django.utils.text import slugify

# Rooms - 4 independent models

class Category(models.Model):
    name = models.CharField(max_length=50)
    color = models.CharField(max_length=20) # CSS-valid color, e.g. hex or color word

    def __str__(self):
        return self.name


class Room(models.Model):
    PUBLIC = 'public'
    PRIVATE = 'private'
    VISIBILITY_CHOICES = (
        (PUBLIC, 'Public'),
        (PRIVATE, 'Private'),
        # (UNLISTED, 'Unlisted'),
    )

    url = models.SlugField(max_length=40, primary_key=True)

    creator = models.ForeignKey(AppUser, related_name='%(class)s_room_creator', on_delete=models.CASCADE)
    description = models.TextField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True, null=True)
    visibility = models.CharField(max_length=10, choices=VISIBILITY_CHOICES, default=PUBLIC)
    categories = models.ManyToManyField('Category')

    invited_users = models.ManyToManyField(to=AppUser, blank=True)

    def __str__(self):
        return self.url


class Video(models.Model):
    added_to = models.ForeignKey(Room, on_delete=models.CASCADE)
    added_by = models.ForeignKey(AppUser, on_delete=models.CASCADE)
    date_added = models.DateTimeField(auto_now_add=True, null=True)

    provider = models.CharField(max_length=20)
    video_id = models.CharField(max_length=200, blank=True)
    file = models.FileField(
        upload_to='user-videos/',
        blank=True,
        validators=[FileExtensionValidator(allowed_extensions=['webm'])])

    title = models.CharField(max_length=200, blank=True, null=True)
    currently_playing = models.BooleanField(default=False)

    class Meta:
        ordering = ["date_added"]

    def clean(self):
        if not self.video_id and not self.file:
            raise ValidationError("Either 'video_id' or 'file' must be provided.")
        if self.video_id and self.file:
            raise ValidationError("Provide either 'video_id' or 'file', but not both.")


class ChatMessage(models.Model):
    room = models.ForeignKey(Room, on_delete=models.CASCADE)
    user = models.ForeignKey(AppUser, on_delete=models.CASCADE)
    message = models.TextField()
    timestamp = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['timestamp']

    def __str__(self):
        return f"{self.user.username}: {self.message}"
