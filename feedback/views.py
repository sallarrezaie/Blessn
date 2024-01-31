from rest_framework.authentication import TokenAuthentication
from rest_framework.permissions import IsAuthenticated
from rest_framework.viewsets import ModelViewSet

from .serializers import FeedbackSerializer
from .models import Feedback


class FeedbackViewSet(ModelViewSet):
    serializer_class = FeedbackSerializer
    permission_classes = (IsAuthenticated,)
    authentication_classes  = [TokenAuthentication]
    queryset = Feedback.objects.all()

    def perform_create(self, serializer):
        serializer.save(user=self.request.user)
