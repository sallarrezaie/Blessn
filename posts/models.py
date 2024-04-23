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
    media_type = models.CharField(
        max_length=255,
        blank=True
    )
    thumbnail = models.FileField(
        upload_to='post_files',
        blank=True,
        null=True
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


class Comment(models.Model):
    """
    A model to represent comments on a post or nested comments.
    """
    post = models.ForeignKey(
        'Post',
        on_delete=models.CASCADE,
        related_name='comments'
    )
    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='comments'
    )
    parent_comment = models.ForeignKey(
        'self',
        null=True,
        blank=True,
        on_delete=models.CASCADE,
        related_name='replies'
    )
    text = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        if self.parent_comment:
            return f"Reply by {self.user} on {self.parent_comment}"
        return f"Comment by {self.user} on {self.post}"


class CommentLike(models.Model):
    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='comment_likes'
    )
    comment = models.ForeignKey(
        Comment,
        on_delete=models.CASCADE,
        related_name='likes'
    )
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ('user', 'comment')

    def __str__(self):
        return f"{self.user} likes {self.comment}"
