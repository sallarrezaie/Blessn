from django.contrib.auth import get_user_model

from rest_framework import serializers

from .models import Consumer


User = get_user_model()


class ConsumerSerializer(serializers.ModelSerializer):
    class Meta:
        model = Consumer
        fields = '__all__'
