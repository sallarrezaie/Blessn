from .models import Feedback

from rest_framework import serializers


class FeedbackSerializer(serializers.ModelSerializer):
    class Meta:
        model = Feedback
        fields = '__all__'
        extra_kwargs = {
            'user': {'required': False},
            'email': {'required': False},
            'responded': {'required': False}
        }
