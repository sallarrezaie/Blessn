from rest_framework.authentication import TokenAuthentication
from home.permissions import IsGetOrIsAuthenticated
from rest_framework.viewsets import ModelViewSet

from .serializers import CategorySerializer
from .models import Category


class CategoryViewSet(ModelViewSet):
    serializer_class = CategorySerializer
    permission_classes = (IsGetOrIsAuthenticated,)
    authentication_classes  = [TokenAuthentication]
    queryset = Category.objects.all()
