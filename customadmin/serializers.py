from rest_framework import serializers


class RegistrationCountSerializer(serializers.Serializer):
    period = serializers.CharField()
    count = serializers.IntegerField()
