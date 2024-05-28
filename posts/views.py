from rest_framework import viewsets, permissions, status
from rest_framework.decorators import action
from rest_framework.response import Response

import math
from django.db.models import Count, Avg, F, Value, IntegerField, FloatField, ExpressionWrapper, Case, When, Q

from django.db.models.functions import Coalesce

from users.models import User
from users.serializers import UserSerializer
from categories.models import Category
from categories.serializers import CategorySerializer
from contributors.models import Contributor, Tag

from .models import Post, Like, Comment, CommentLike
from .serializers import PostSerializer, CommentSerializer

from django_filters.rest_framework import DjangoFilterBackend

from rest_framework.pagination import CursorPagination, PageNumberPagination
from rest_framework.exceptions import ValidationError
from home.permissions import IsGetOrIsAuthenticated

from users.models import Follow
from customadmin.utils import contains_banned_words


class CustomPageNumberPagination(PageNumberPagination):
    def get_paginated_response(self, data):
        # Calculate the total number of pages
        page_size = self.page_size  # The number of items per page
        total_items = self.page.paginator.count  # Total count of items
        total_pages = math.ceil(total_items / page_size)  # Compute total pages
        
        # Add total pages to the response
        return Response({
            'count': total_items,  # Total number of items
            'total_pages': total_pages,  # New field for total pages
            'results': data,  # Paginated data
        })


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
        title = serializer.validated_data.get('title', '')
        if contains_banned_words(title):
            raise ValidationError({"error": "Post title contains banned words."})

        description = serializer.validated_data.get('description', '')
        if contains_banned_words(description):
            raise ValidationError({"error": "Post description contains banned words."})

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
            serializer = self.get_serializer(page, many=True, context={'request': request})

            return paginator.get_paginated_response(serializer.data)

        serializer = self.get_serializer(posts, many=True, context={'request': request})
        
        return Response(serializer.data)

    @action(detail=False, methods=['get'], url_path='global_search')
    def global_search(self, request):
        """
        Global search with pagination, returning paginated results for Posts, Users, or Categories.
        """
        query = request.query_params.get('q', None)  # Search query
        if not query:
            return Response({"error": "Query parameter 'q' is required."}, status=status.HTTP_400_BAD_REQUEST)

        obj_type = request.query_params.get('type', None)  # Object type to filter
        paginator = CustomPageNumberPagination()
        paginator.page_size = 10  # Default items per page

        response_data = {}

        if obj_type in [None, "posts"]:  # Return Posts by default or if specified
            matching_posts = Post.objects.filter(
                Q(title__icontains=query) | Q(description__icontains=query)
            ).order_by('-created_at')
            paginated_posts = paginator.paginate_queryset(matching_posts, request)
            post_serializer = PostSerializer(paginated_posts, many=True)
            response_data["posts"] = paginator.get_paginated_response(post_serializer.data).data

        if obj_type in [None, "users"]:  # Return Users if specified or by default
            tag_matches = Tag.objects.filter(name__icontains=query)
            matching_contributors = Contributor.objects.filter(tags__in=tag_matches).distinct()
            matching_users = User.objects.filter(Q(contributor__in=matching_contributors) | Q(name__icontains=query))
            paginated_users = paginator.paginate_queryset(matching_users, request)
            user_serializer = UserSerializer(paginated_users, many=True)
            response_data["users"] = paginator.get_paginated_response(user_serializer.data).data

        if obj_type in [None, "categories"]:  # Return all matching Categories
            matching_categories = Category.objects.filter(name__icontains=query).distinct()
            category_serializer = CategorySerializer(matching_categories, many=True)
            response_data["categories"] = category_serializer.data  # No pagination

        return Response(response_data, status=status.HTTP_200_OK)


class CommentViewSet(viewsets.ModelViewSet):
    queryset = Comment.objects.all()
    serializer_class = CommentSerializer
    permission_classes = [IsGetOrIsAuthenticated]
    filter_backends = [DjangoFilterBackend]
    filterset_fields = ['post']


    def perform_create(self, serializer):
        """
        Assigns the user and optionally a parent comment during creation, while checking for banned words in the comment text.
        """
        user = self.request.user
        text = serializer.validated_data.get('text', '')
        
        if contains_banned_words(text):
            raise ValidationError("Comment contains banned words.")

        parent_comment_id = self.request.data.get("parent_comment")
        parent_comment = None
        if parent_comment_id:
            try:
                parent_comment = Comment.objects.get(id=parent_comment_id)
            except Comment.DoesNotExist:
                raise ValidationError({"parent_comment": "Invalid parent comment ID provided."})

        serializer.save(user=user, parent_comment=parent_comment)

    @action(detail=True, methods=['post'])
    def like(self, request, pk=None):
        """
        Like a comment.
        """
        user = request.user
        comment = self.get_object()  # Get the current comment
        if CommentLike.objects.filter(user=user, comment=comment).exists():
            return Response("Comment already liked", status=status.HTTP_400_BAD_REQUEST)  # Already liked
        CommentLike.objects.create(user=user, comment=comment)  # Create like
        return Response(status=status.HTTP_201_CREATED)

    @action(detail=True, methods=['delete'])
    def unlike(self, request, pk=None):
        """
        Unlike a comment.
        """
        user = request.user
        comment = self.get_object()  # Get the current comment
        try:
            like = CommentLike.objects.get(user=user, comment=comment)  # Get the like
            like.delete()  # Delete the like
            return Response(status=status.HTTP_204_NO_CONTENT)
        except CommentLike.DoesNotExist:
            return Response("Comment must be liked first to unlike", status=status.HTTP_404_NOT_FOUND)
