from django.db.models.signals import post_save, pre_delete
from django.dispatch import receiver
from .models import ChatMessage, Room, Video
from ..user_auth.models import AppUser


@receiver(post_save, sender=ChatMessage)
def limit_messages(sender, instance, **kwargs):
    max_messages = 50
    if sender.objects.count() > max_messages:
        sender.objects.order_by('timestamp').first().delete()


@receiver(pre_delete, sender=AppUser)
def delete_related_videos(sender, instance, **kwargs):
    Room.objects.filter(creator=instance).delete()


@receiver(pre_delete, sender=Room)
def delete_related_videos(sender, instance, **kwargs):
    Video.objects.filter(added_to=instance).delete()