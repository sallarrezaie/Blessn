from rest_framework import serializers

from .models import BannedWord


class RegistrationCountSerializer(serializers.Serializer):
    period = serializers.CharField()
    count = serializers.IntegerField()


class BannedWordSerializer(serializers.ModelSerializer):
    class Meta:
        model = BannedWord
        fields = '__all__'
