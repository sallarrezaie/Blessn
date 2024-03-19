from rest_framework import serializers
from .models import Post, PostFile, Like

from users.serializers import UserSerializer


class PostFileSerializer(serializers.ModelSerializer):
    class Meta:
        model = PostFile
        fields = ['id', 'file', 'media_type', 'thumbnail', 'created_at']


class PostSerializer(serializers.ModelSerializer):
    post_files = PostFileSerializer(many=True, required=False)
    likes_count = serializers.SerializerMethodField()
    is_liked_by_user = serializers.SerializerMethodField() 

    class Meta:
        model = Post
        fields = '__all__'
        extra_kwargs = {
            'contributor': {
                'required': False
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

    def get_likes_count(self, obj):
        """Returns the count of likes for the post."""
        return Like.objects.filter(post=obj).count()

    def get_is_liked_by_user(self, obj):
        """Check if the post is liked by the authenticated user."""
        user = self.context.get('request').user
        if user and user.is_authenticated:
            return Like.objects.filter(post=obj, user=user).exists()
        return False

    def to_representation(self, instance):
        request = self.context.get('request')
        rep = super().to_representation(instance)
        rep['user'] = UserSerializer(instance.contributor.user, context={'request': request}).data
        return rep
