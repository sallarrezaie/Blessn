from django.contrib.auth import get_user_model

from rest_framework import serializers

from .models import Contributor, ContributorPhotoVideo
from categories.serializers import CategorySerializer


User = get_user_model()


class ContributorPhotoVideoSerializer(serializers.ModelSerializer):
    class Meta:
        model = ContributorPhotoVideo
        fields = '__all__'
        extra_kwargs = {'contributor': {'required': False}}


class ContributorSerializer(serializers.ModelSerializer):
    photos_videos = ContributorPhotoVideoSerializer(many=True, required=False)

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
        return rep
