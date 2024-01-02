from rest_framework import authentication, permissions
from .models import PrivacyPolicy
from .serializers import PrivacyPolicySerializer
from rest_framework import viewsets


class PrivacyPolicyViewSet(viewsets.ModelViewSet):
    serializer_class = PrivacyPolicySerializer
    permission_classes = [permissions.AllowAny]
    authentication_classes = (
        authentication.SessionAuthentication,
        authentication.TokenAuthentication,
    )

    queryset = PrivacyPolicy.objects.filter(is_active=True).order_by('-updated_at')[0:1]
