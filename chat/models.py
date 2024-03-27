from django.contrib.auth import get_user_model
from django.db import models

from orders.models import Order


User = get_user_model()


class ChatChannel(models.Model):
    users = models.ManyToManyField(
        User,
        blank=True,
        related_name='chat_channels'
    )
    order = models.OneToOneField(
        Order,
        on_delete=models.CASCADE,
        related_name='chat_channel',
        blank=True,
        null=True
    )
    created_at = models.DateTimeField(
        auto_now_add=True
    )


class ChatMessage(models.Model):
    channel = models.ForeignKey(
        ChatChannel,
        related_name='messages',
        on_delete=models.CASCADE
    )
    text = models.TextField(blank=True)
    timetoken = models.DateTimeField(auto_now_add=True)
    sender = models.ForeignKey(
        User,
        related_name='sent_messages',
        on_delete=models.CASCADE,
        blank=True,
        null=True
    )
    file = models.FileField(
        blank=True,
        null=True,
        upload_to='messages/files'
    )
    file_type = models.CharField(
        max_length=255,
        blank=True
    )
    read = models.BooleanField(default=False)

    class Meta:
        ordering = ['-timetoken']
