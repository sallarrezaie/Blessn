from rest_framework import serializers

from .models import Occasion


class OccasionSerializer(serializers.ModelSerializer):
    class Meta:
        model = Occasion
        fields = '__all__'
