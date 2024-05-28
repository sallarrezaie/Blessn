from rest_framework.authentication import TokenAuthentication
from rest_framework.exceptions import ValidationError
from rest_framework.permissions import IsAuthenticated
from rest_framework.viewsets import ModelViewSet

from .serializers import FeedbackSerializer
from .models import Feedback
from customadmin.utils import contains_banned_words


class FeedbackViewSet(ModelViewSet):
    serializer_class = FeedbackSerializer
    permission_classes = (IsAuthenticated,)
    authentication_classes  = [TokenAuthentication]
    queryset = Feedback.objects.all()


    def perform_create(self, serializer):
        message = serializer.validated_data.get('message', '')

        # Check for banned words in the feedback text
        if contains_banned_words(message):
            raise ValidationError("Feedback contains banned words.")

        serializer.save(user=self.request.user)
