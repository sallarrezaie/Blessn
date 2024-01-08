from rest_framework.authentication import TokenAuthentication
from home.permissions import IsGetOrIsAuthenticated
from rest_framework.viewsets import ModelViewSet

from .serializers import ContributorSerializer, ContributorPhotoVideoSerializer
from .models import Contributor, ContributorPhotoVideo


class ContributorPhotoVideoViewSet(ModelViewSet):
    serializer_class = ContributorPhotoVideoSerializer
    permission_classes = (IsGetOrIsAuthenticated,)
    authentication_classes  = [TokenAuthentication]
    queryset = ContributorPhotoVideo.objects.all()
