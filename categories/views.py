from rest_framework.authentication import TokenAuthentication
from rest_framework.permissions import IsAuthenticated
from rest_framework.viewsets import ModelViewSet

from .serializers import CategorySerializer
from .models import Category


class CategoryViewSet(ModelViewSet):
    serializer_class = CategorySerializer
    permission_classes = (IsAuthenticated,)
    authentication_classes  = [TokenAuthentication]
    queryset = Category.objects.all()
