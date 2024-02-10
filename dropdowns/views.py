from rest_framework.authentication import TokenAuthentication
from home.permissions import IsGetOrIsAuthenticated
from rest_framework.viewsets import ModelViewSet

from .serializers import OccasionSerializer
from .models import Occasion


class OccasionViewSet(ModelViewSet):
    serializer_class = OccasionSerializer
    permission_classes = (IsGetOrIsAuthenticated,)
    authentication_classes  = [TokenAuthentication]
    queryset = Occasion.objects.all()
