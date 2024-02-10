from django.db import models

from contributors.models import Contributor
from users.models import User


class Post(models.Model):
    """
    A model to represent the Posts of a Contributor
    """
    contributor = models.ForeignKey(
        Contributor,
        on_delete=models.CASCADE,
        related_name='posts'
    )
    title = models.CharField(
        max_length=255
    )
    description = models.TextField(
        blank=True
    )
    created_at = models.DateTimeField(
        auto_now_add=True
    )


class PostFile(models.Model):
    """
    A model to represent images and videos of a Post
    """
    post = models.ForeignKey(
        Post,
        on_delete=models.CASCADE,
        related_name='post_files'
    )
    file = models.FileField(
        upload_to='post_files'
    )
    created_at = models.DateTimeField(
        auto_now_add=True
    )


class Like(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='likes')
    post = models.ForeignKey(Post, on_delete=models.CASCADE, related_name='likes')
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ('user', 'post')  # Ensures a user can only like a post once

    def __str__(self):
        return f"{self.user} likes {self.post}"
