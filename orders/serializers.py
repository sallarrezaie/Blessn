from rest_framework import serializers
from .models import Order
from .tasks import process_video_and_update_order

class OrderSerializer(serializers.ModelSerializer):
    class Meta:
        model = Order
        fields = '__all__'
        depth = 3

    def create(self, validated_data):
        blessn_file = validated_data.pop('blessn', None)
        order = Order.objects.create(**validated_data, video_processing=True)
        if blessn_file:
            order.blessn = blessn_file
            order.save()
            process_video_and_update_order.delay(order.id)
        return order

    def update(self, instance, validated_data):
        blessn_file = validated_data.pop('blessn', None)
        if blessn_file:
            instance.blessn = blessn_file
            instance.video_processing = True
            instance.save()
            process_video_and_update_order.delay(instance.id)
        return super().update(instance, validated_data)
