from rest_framework import serializers

from chat.models import ChatChannel, ChatMessage
from home.api.v1.serializers import UserSerializer
from orders.serializers import OrderSerializer



class ChatMessageSerializer(serializers.ModelSerializer):
    sender = UserSerializer(required=False)

    class Meta:
        model = ChatMessage
        fields = '__all__'

    def to_representation(self, instance):
        rep = super().to_representation(instance)
        rep['id'] = str(rep['id'])
        rep['channel'] = str(rep['channel'])
        return rep


class ChatChannelSerializer(serializers.ModelSerializer):
    messages = ChatMessageSerializer(many=True)
    order = OrderSerializer(required=False)

    class Meta:
        model = ChatChannel
        fields = '__all__'


    def to_representation(self, instance):
        rep = super().to_representation(instance)
        if instance.users:
            rep['users'] = UserSerializer(instance.users.all(), many=True).data
        return rep


class MyChatChannelSerializer(serializers.ModelSerializer):
    last_message = serializers.SerializerMethodField()
    unread_messages_count = serializers.SerializerMethodField()
    order = OrderSerializer(required=False)

    class Meta:
        model = ChatChannel
        exclude = ('users',)


    def get_last_message(self, obj):
        try:
            message = obj.messages.latest('timetoken')
        except ChatMessage.DoesNotExist:
            serializer = None
        else:
            serializer = ChatMessageSerializer(message).data
        return serializer

    def get_unread_messages_count(self, obj):
        current_user = self.context['request'].user
        unread_messages = obj.messages.exclude(sender=current_user).filter(read=False).count()
        return unread_messages

    def to_representation(self, instance):
        rep = super().to_representation(instance)
        if instance.users:
            rep['users'] = UserSerializer(instance.users.all(), many=True).data
        return rep
