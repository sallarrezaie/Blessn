from django.contrib.auth import get_user_model
from django.db.models import Avg, Sum

from rest_framework import serializers
from rest_framework.exceptions import ValidationError

from .models import Contributor, ContributorPhotoVideo, Tag
from categories.serializers import CategorySerializer

from blessn.settings import BOOKING_FEE
from users.models import Follow
from customadmin.utils import contains_banned_words


User = get_user_model()


class TagSerializer(serializers.ModelSerializer):
    class Meta:
        model = Tag
        fields = '__all__'


class AdminTagSerializer(serializers.ModelSerializer):
    user_count = serializers.SerializerMethodField()

    class Meta:
        model = Tag
        fields = '__all__'

    def get_user_count(self, obj):
        return obj.contributors.count()


class ContributorPhotoVideoSerializer(serializers.ModelSerializer):
    class Meta:
        model = ContributorPhotoVideo
        fields = '__all__'
        extra_kwargs = {'contributor': {'required': False}}

    def validate_title(self, value):
        if contains_banned_words(value):
            raise ValidationError("Title contains banned words.")
        return value

    def validate_description(self, value):
        if contains_banned_words(value):
            raise ValidationError("Description contains banned words.")
        return value


class ContributorSerializer(serializers.ModelSerializer):
    photos_videos = ContributorPhotoVideoSerializer(many=True, required=False)
    tags = TagSerializer(many=True, required=False)

    class Meta:
        model = Contributor
        fields = '__all__'

    def update(self, instance, validated_data):
        photos_videos_data = validated_data.pop('photos_videos', None)
        contributor = super().update(instance, validated_data)

        if photos_videos_data is not None:
            for photo_video_data in photos_videos_data:
                photo_video_serializer = ContributorPhotoVideoSerializer(data=photo_video_data)
                if photo_video_serializer.is_valid(raise_exception=True):
                    photo_video_serializer.save(contributor=contributor)
                    
        return contributor

    def to_representation(self, instance):
        rep = super().to_representation(instance)
        if instance.category:
            rep['category'] = CategorySerializer(instance.category).data
        rep['rating'] = instance.reviews.aggregate(Avg('rating'))['rating__avg']
        rep['rating_count'] = instance.reviews.count()
        rep['post_count'] = instance.posts.all().count()
        user = instance.user
        followers_count = Follow.objects.filter(followed=user).count()
        following_count = Follow.objects.filter(follower=user).count()

        rep['followers_count'] = followers_count
        rep['following_count'] = following_count

        earnings = instance.orders.aggregate(total_earnings=Sum('video_fee'))['total_earnings']
        earnings = earnings if earnings is not None else 0

        rep['earnings'] = earnings

        pending_booking_requests = instance.orders.filter(status='Pending').count()
        rep['pending_booking_requests'] = pending_booking_requests
        rep['booking_fee'] = BOOKING_FEE
        return rep
