from rest_framework import serializers
from .models import Post, PostFile, Like, Comment
from home.api.v1.serializers import UserSerializer as MiniUserSerializer

from users.serializers import UserSerializer


class PostFileSerializer(serializers.ModelSerializer):
    class Meta:
        model = PostFile
        fields = ['id', 'file', 'media_type', 'thumbnail', 'created_at']


class CommentSerializer(serializers.ModelSerializer):
    replies = serializers.SerializerMethodField()  # Fetch nested comments
    likes_count = serializers.SerializerMethodField()  # Total number of likes
    is_liked_by_user = serializers.SerializerMethodField()  # Check if user has liked the comment

    class Meta:
        model = Comment
        fields = ('id', 'post', 'user', 'text', 'created_at', 'parent_comment', 'replies', 'likes_count', 'is_liked_by_user')
        extra_kwargs = {
            "user": {
                "required": False
            }
        }

    def get_replies(self, obj):
        """
        Returns serialized replies for a given comment.
        """
        context = self.context if 'request' in self.context else {}
        if obj.replies.exists():
            return CommentSerializer(obj.replies, many=True, context=context).data
        return []

    def get_likes_count(self, obj):
        return obj.likes.count()  # Count the likes for this comment

    def get_is_liked_by_user(self, obj):
        """
        Check if the current user has liked this comment.
        """
        request = self.context.get('request', None)  # Safely get the request
        user = request.user if request else None  # Get the user from request
        if not user or not user.is_authenticated:
            return False
        return obj.likes.filter(user=user).exists()

    def to_representation(self, instance):
        rep = super().to_representation(instance)
        if instance.user:
            rep['user'] = MiniUserSerializer(instance.user).data
        return rep


class PostSerializer(serializers.ModelSerializer):
    post_files = PostFileSerializer(many=True, required=False)
    likes_count = serializers.SerializerMethodField()
    is_liked_by_user = serializers.SerializerMethodField()
    top_level_comments = serializers.SerializerMethodField()  # Top-level comments only
    comments_count = serializers.SerializerMethodField()  # Total comment count

    class Meta:
        model = Post
        fields = ('id', 'contributor', 'title', 'description', 'created_at', 'post_files', 'likes_count', 
                  'is_liked_by_user', 'top_level_comments', 'comments_count')
        extra_kwargs = {
            "contributor": {
                "required": False
            }
        }

    def create(self, validated_data):
        post_files_data = validated_data.pop('post_files', None)

        post = super().create(validated_data)

        if post_files_data is not None:
            for post_file_data in post_files_data:
                PostFile.objects.create(post=post, **post_file_data)
        return post

    def update(self, instance, validated_data):
        post_files_data = validated_data.pop('post_files', None)
        
        instance = super().update(instance, validated_data)
        if post_files_data is not None:

            instance.post_files.all().delete()  # Clear existing files
            for post_file_data in post_files_data:
                PostFile.objects.create(post=instance, **post_file_data)
        return instance

    def get_top_level_comments(self, obj):
        """
        Fetch only the top-level comments (those without a parent).
        """
        top_level_comments = Comment.objects.filter(post=obj, parent_comment__isnull=True)  # Only top-level comments
        return CommentSerializer(top_level_comments, many=True, context={'request': self.context.get('request')}).data

    def get_comments_count(self, obj):
        return obj.comments.count()  # Total count of comments

    def get_likes_count(self, obj):
        """Returns the count of likes for the post."""
        return Like.objects.filter(post=obj).count()

    def get_is_liked_by_user(self, obj):
        """Check if the post is liked by the authenticated user."""
        request = self.context.get('request', None)  # Safely get the request
        user = request.user if request else None  # Get the user from request

        if user and user.is_authenticated:  # Check if user is valid and authenticated
            return Like.objects.filter(post=obj, user=user).exists()  # Determine if the post is liked by the user
        return False

    def to_representation(self, instance):
        context = self.context if 'request' in self.context else {}  # Safe access to context
        rep = super().to_representation(instance)
        user = instance.contributor.user
        rep['user'] = UserSerializer(user, context=context).data  # Ensure context is passed
        return rep
