from rest_framework import serializers

from .models import Category


class CategorySerializer(serializers.ModelSerializer):
    contributor_count = serializers.SerializerMethodField()

    class Meta:
        model = Category
        fields = '__all__'

    def get_contributor_count(self, obj):
        return obj.contributor_count()
