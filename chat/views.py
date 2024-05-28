from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.viewsets import ModelViewSet
from rest_framework.permissions import IsAuthenticated

from django.contrib.auth import get_user_model

from rest_framework import status

from .models import ChatChannel, ChatMessage
from .serializers import ChatChannelSerializer, MyChatChannelSerializer

from blessn.settings import PUBNUB_PUBLISH_KEY, PUBNUB_SUBSCRIBE_KEY
from django_filters.rest_framework import DjangoFilterBackend

from customadmin.utils import contains_banned_words

User = get_user_model()


from pubnub.pubnub import PubNub
from pubnub.exceptions import PubNubException
from pubnub.pnconfiguration import PNConfiguration
from django.core.files.storage import default_storage


class ChatChannelViewSet(ModelViewSet):
    serializer_class = ChatChannelSerializer
    permission_classes = (IsAuthenticated,)
    queryset = ChatChannel.objects.all()
    filter_backends = [DjangoFilterBackend]
    filterset_fields = ['order']

    @action(detail=False, methods=["get"])
    def my_chats(self, request):
        user_channels = request.user.chat_channels.all()
        serializer = MyChatChannelSerializer(user_channels, many=True, context={"request": request})
        serialized_data = serializer.data

        # Sum up the unread messages count from each channel in the serialized data
        total_unread_messages = sum(channel.get('unread_messages_count', 0) for channel in serialized_data)

        # Include the total unread messages count in the response
        response_data = {
            'channels': serialized_data,
            'total_unread_messages': total_unread_messages
        }

        return Response(response_data)

    @action(detail=False, methods=["post"])
    def publish_message(self, request):
        text = request.data.get('text', '')
        user = request.user
        sender_uuid = str(user.id)
        channel_id = request.data.get('channel')

        if contains_banned_words(text):
            return Response({"error": "Text contains banned words."}, status=status.HTTP_400_BAD_REQUEST)

        try:
            channel = ChatChannel.objects.get(id=channel_id)
        except ChatChannel.DoesNotExist:
            return Response({"error": "Channel not found"}, status=status.HTTP_404_NOT_FOUND)

        file = request.FILES.get('file', None)
        file_url = None  # Initialize file_url
        file_type = ""
        filename = ""
        if file:
            # Save file and get filename
            filename = default_storage.save(file.name, file)
            # Generate URL for PubNub message
            file_url = default_storage.url(filename)
            file_type = file.content_type

        mypubnubconfig = PNConfiguration()
        mypubnubconfig.subscribe_key = PUBNUB_SUBSCRIBE_KEY
        mypubnubconfig.publish_key = PUBNUB_PUBLISH_KEY
        mypubnubconfig.user_id = sender_uuid
        pubnub = PubNub(mypubnubconfig)

        message_data = {
            'content': text,
            'sender_uuid': sender_uuid,
            'channel': str(channel.id),
        }

        if file:
            message_data['file'] = {
                'name': file.name,
                'url': file_url,  # Use the S3 URL
                'size': file.size,
                'type': file.content_type,
            }

        try:
            ChatMessage.objects.create(
                text=text,
                sender=user,
                channel=channel,
                file=filename if file else None,
                file_type=file_type
            )

            pubnub.publish().channel(str(channel.id)).message(message_data).sync()

            return Response("Message Sent", status=status.HTTP_200_OK)
        except PubNubException as e:
            return Response(f"Message not sent due to the following error: {str(e)}", status=status.HTTP_400_BAD_REQUEST)

    @action(detail=False, methods=["post"])
    def mark_as_read(self, request):
        channel_id = request.data.get('channel_id')
        channel = ChatChannel.objects.get(id=channel_id)
        user = request.user
        messages = channel.messages.exclude(sender=user)
        messages.update(read=True)
        return Response("Messages marked as read", status=status.HTTP_200_OK)
