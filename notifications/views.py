from rest_framework import status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.viewsets import ModelViewSet
from rest_framework.permissions import IsAuthenticated
from notifications.models import Notification
from notifications.serializers import NotificationSerializer


class NotificationViewSet(ModelViewSet):
    serializer_class = NotificationSerializer
    permission_classes = (IsAuthenticated,)
    queryset = Notification.objects.all()

    def get_queryset(self):
        return Notification.objects.filter(user=self.request.user)

    @action(detail=False, methods=['get', 'post'])
    def read(self, request):
        user = request.user
        if request.method == "GET":
            user.notifications.all().update(read=True)
        else:
            notif = request.data.get('notification', None)
            if notif:
                try:
                    notif_obj = Notification.objects.get(id=notif)
                    notif_obj.read = True
                    notif_obj.save()
                except Notification.DoesNotExist:
                    return Response({'detail': 'Invalid Notification ID'}, status=status.HTTP_400_BAD_REQUEST)
        serializer = NotificationSerializer(user.notifications.all(), many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)

    @action(detail=False, methods=['get'], permission_classes=[IsAuthenticated])
    def generate_sample_notification(self, request):
        """
        Generates a sample notification for the request.user.
        """
        user = request.user
        sample_notification = Notification.objects.create(
            user=user,
            title="Sample Notification",
            content="This is a sample notification content.",
            data_type="Sample Type",
            data="Sample Data",
            read=False
        )

        serializer = NotificationSerializer(sample_notification)
        return Response(serializer.data, status=status.HTTP_201_CREATED)