from django.contrib.auth import get_user_model
from django.db.models import Avg, Sum

from rest_framework import serializers

from .models import Contributor, ContributorPhotoVideo, Tag
from categories.serializers import CategorySerializer

from blessn.settings import BOOKING_FEE
from users.models import Follow


User = get_user_model()


class TagSerializer(serializers.ModelSerializer):
    class Meta:
        model = Tag
        fields = '__all__'


class ContributorPhotoVideoSerializer(serializers.ModelSerializer):
    class Meta:
        model = ContributorPhotoVideo
        fields = '__all__'
        extra_kwargs = {'contributor': {'required': False}}


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
            for photo_video in photos_videos_data:
                ContributorPhotoVideo.objects.create(
                        **photo_video,
                        contributor=contributor
                    )
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
