from rest_framework import viewsets, permissions, status
from rest_framework.decorators import action
from rest_framework.response import Response

from django.db.models import Count, Avg, F, Case, When, Value, IntegerField, FloatField, ExpressionWrapper
from django.db.models.functions import Coalesce

from .models import Post, Like
from .serializers import PostSerializer

from django_filters.rest_framework import DjangoFilterBackend

from rest_framework.pagination import CursorPagination
from home.permissions import IsGetOrIsAuthenticated


class RankedPostsCursorPagination(CursorPagination):
    page_size = 10
    ordering = '-ranking_score'


class PostViewSet(viewsets.ModelViewSet):
    queryset = Post.objects.all()
    serializer_class = PostSerializer
    permission_classes = [IsGetOrIsAuthenticated]
    filter_backends = [DjangoFilterBackend]
    filterset_fields = ['contributor']
 

    def perform_create(self, serializer):
        serializer.save(contributor=self.request.user.contributor)

    @action(detail=True, methods=['post'])
    def like(self, request, pk=None):
        post = self.get_object()
        user = request.user
        like, created = Like.objects.get_or_create(user=user, post=post)
        if created:
            return Response('Like added', status=status.HTTP_201_CREATED)
        else:
            return Response('Like already exists', status=status.HTTP_400_BAD_REQUEST)

    @action(detail=True, methods=['post'])
    def unlike(self, request, pk=None):
        post = self.get_object()
        user = request.user
        try:
            like = Like.objects.get(user=user, post=post)
            like.delete()
            return Response('Like removed', status=status.HTTP_200_OK)
        except Like.DoesNotExist:
            return Response('Like does not exist', status=status.HTTP_400_BAD_REQUEST)

    @action(detail=False, methods=['get'])
    def ranked_posts(self, request):
        if request.user and request.user.is_authenticated:
            followed_contributors_ids = request.user.following.values_list('followed__id', flat=True)
        else:
            followed_contributors_ids = []

        # Annotate posts with likes count, followers count, average rating, and follow status
        posts = Post.objects.annotate(
            likes_count=Count('likes'),
            follows_count=Count('contributor__followers', distinct=True),
            average_rating=Coalesce(Avg('contributor__reviews__rating'), 0.0),
            is_followed=Case(
                When(contributor__id__in=followed_contributors_ids, then=Value(1)),
                default=Value(0),
                output_field=IntegerField()
            )
        ).annotate(
            # Calculate the ranking score considering follow status and weighted factors
            ranking_score=ExpressionWrapper(
                F('is_followed') * Value(0.45) +
                F('likes_count') * Value(0.15) +
                F('follows_count') * Value(0.15) +
                F('average_rating') * Value(0.15),
                output_field=FloatField()
            )
        ).order_by('-ranking_score')

        # Apply cursor-based pagination
        paginator = RankedPostsCursorPagination()
        page = paginator.paginate_queryset(posts, request, self)
        if page is not None:
            serializer = self.get_serializer(page, many=True)
            return paginator.get_paginated_response(serializer.data)

        # Fallback, in case pagination is not applied
        serializer = self.get_serializer(posts, many=True)
        return Response(serializer.data)