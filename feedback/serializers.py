from .models import Feedback

from rest_framework import serializers
from users.serializers import UserSerializer


class FeedbackSerializer(serializers.ModelSerializer):
    class Meta:
        model = Feedback
        fields = '__all__'
        extra_kwargs = {
            'user': {'required': False},
            'email': {'required': False},
            'responded': {'required': False}
        }

    def to_representation(self, instance):
        response = super().to_representation(instance)
        if instance.user:
            response['user'] = UserSerializer(instance.user).data
        return response
