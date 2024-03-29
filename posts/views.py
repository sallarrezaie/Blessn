from rest_framework import viewsets, permissions, status
from rest_framework.decorators import action
from rest_framework.response import Response

from django.db.models import Count, Avg, F, Value, IntegerField, FloatField, ExpressionWrapper, Case, When

from django.db.models.functions import Coalesce

from .models import Post, Like
from .serializers import PostSerializer

from django_filters.rest_framework import DjangoFilterBackend

from rest_framework.pagination import CursorPagination
from home.permissions import IsGetOrIsAuthenticated

from users.models import Follow


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

    @action(detail=False, methods=['post'])
    def like(self, request):
        post = Post.objects.get(id=request.data.get("post"))
        user = request.user
        like, created = Like.objects.get_or_create(user=user, post=post)
        if created:
            return Response('Like added', status=status.HTTP_201_CREATED)
        else:
            return Response('Like already exists', status=status.HTTP_400_BAD_REQUEST)

    @action(detail=False, methods=['post'])
    def unlike(self, request):
        post = Post.objects.get(id=request.data.get("post"))
        user = request.user
        try:
            like = Like.objects.get(user=user, post=post)
            like.delete()
            return Response('Like removed', status=status.HTTP_200_OK)
        except Like.DoesNotExist:
            return Response('Like does not exist', status=status.HTTP_400_BAD_REQUEST)

    @action(detail=False, methods=['get'])
    def ranked_posts(self, request):
        # Only fetch followed_contributors_ids if user is authenticated
        if request.user.is_authenticated:
            followed_contributors_ids = Follow.objects.filter(follower=request.user).values_list('followed__contributor__id', flat=True)
        else:
            followed_contributors_ids = []

        posts = Post.objects.annotate(
            likes_count=Count('likes', distinct=True),
            follows_count=Count('contributor__user__followers', distinct=True),  # Assuming a reverse relation from User to Follow
            average_rating=Coalesce(Avg('contributor__reviews__rating'), 0.0),
        )

        if request.user.is_authenticated:
            posts = posts.annotate(
                is_followed=Case(
                    When(contributor__id__in=followed_contributors_ids, then=Value(1)),
                    default=Value(0),
                    output_field=IntegerField()
                ),
                ranking_score=ExpressionWrapper(
                    F('is_followed') * Value(1.35) +  # Adjusting weight for follow status
                    F('likes_count') * Value(0.2) +  # New weight considering follow status
                    F('follows_count') * Value(0.2) +  # Adjusted weight
                    F('average_rating') * Value(0.25),  # Adjusted weight
                    output_field=FloatField()
                )
            )
        else:
            # For unauthenticated users, or when follow status doesn't apply
            posts = posts.annotate(
                ranking_score=ExpressionWrapper(
                    F('likes_count') * Value(0.3) +
                    F('follows_count') * Value(0.3) +
                    F('average_rating') * Value(0.4),
                    output_field=FloatField()
                )
            )

        posts = posts.order_by('-ranking_score')

        paginator = RankedPostsCursorPagination()
        page = paginator.paginate_queryset(posts, request, self)
        if page is not None:
            serializer = self.get_serializer(page, many=True)
            return paginator.get_paginated_response(serializer.data)

        serializer = self.get_serializer(posts, many=True)
        return Response(serializer.data)
