from django.db.models.functions import TruncDay, TruncMonth, TruncYear
from django.db.models import Count, Q
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework.filters import SearchFilter

from rest_framework.permissions import IsAuthenticated, IsAdminUser
from rest_framework.views import APIView
from rest_framework.viewsets import ModelViewSet
from rest_framework.response import Response
from rest_framework import status
from rest_framework.decorators import action

from datetime import datetime

from .models import BannedWord
from .serializers import RegistrationCountSerializer, BannedWordSerializer
from users.serializers import AdminUserSerializer, UserSerializer
from users.models import User
from orders.models import Order
from orders.serializers import OrderSerializer
from categories.models import Category
from categories.serializers import CategorySerializer
from contributors.models import Tag, Contributor
from contributors.serializers import AdminTagSerializer
from posts.models import Post
from posts.serializers import PostSerializer
from payments.models import BookingFee

from feedback.serializers import FeedbackSerializer
from feedback.models import Feedback


class RegistrationStats(APIView):
    permission_classes = [IsAuthenticated, IsAdminUser]

    def get(self, request):
        # Get date range from query parameters
        start_date = request.query_params.get('start_date')
        end_date = request.query_params.get('end_date')
        group_by = request.query_params.get('group_by', 'day')  # Default to day if not specified

        if not start_date or not end_date:
            return Response({"error": "start_date and end_date parameters are required."}, status=status.HTTP_400_BAD_REQUEST)

        # Convert dates from string to datetime objects
        try:
            start_date = datetime.strptime(start_date, "%Y-%m-%d")
            end_date = datetime.strptime(end_date, "%Y-%m-%d")
        except ValueError:
            return Response({"error": "Invalid date format. Use YYYY-MM-DD."}, status=status.HTTP_400_BAD_REQUEST)

        # Map group_by to corresponding Django Trunc functions
        trunc_mappings = {
            'day': TruncDay,
            'month': TruncMonth,
            'year': TruncYear
        }

        if group_by not in trunc_mappings:
            return Response({"error": "Invalid group_by parameter. Choose 'day', 'month', or 'year'."}, status=status.HTTP_400_BAD_REQUEST)

        # Group and count registrations
        queryset = User.objects.filter(date_joined__range=(start_date, end_date))
        queryset = queryset.annotate(period=trunc_mappings[group_by]('date_joined')).values('period').annotate(count=Count('id')).order_by('period')

        # Serialize data
        serializer = RegistrationCountSerializer(queryset, many=True)
        return Response(serializer.data)


class RegistrationStatsProfiles(APIView):
    permission_classes = [IsAuthenticated, IsAdminUser]

    def get(self, request):
        # Get date range from query parameters
        search_term = request.query_params.get('search_term')
        start_date = request.query_params.get('start_date')
        end_date = request.query_params.get('end_date')
        applied_contributors = request.query_params.get('applied_contributors', False)

        if not start_date or not end_date:
            return Response({"error": "start_date and end_date parameters are required."}, status=status.HTTP_400_BAD_REQUEST)

        # Convert dates from string to datetime objects
        try:
            start_date = datetime.strptime(start_date, "%Y-%m-%d")
            end_date = datetime.strptime(end_date, "%Y-%m-%d")
        except ValueError:
            return Response({"error": "Invalid date format. Use YYYY-MM-DD."}, status=status.HTTP_400_BAD_REQUEST)

        # Group and count registrations
        queryset = User.objects.filter(date_joined__range=(start_date, end_date))

        if search_term:
            search_terms = search_term.split()
            if len(search_terms) > 1:
                # Assume first and last name are provided
                queryset = queryset.filter(
                    Q(email__icontains=search_term) |
                    Q(first_name__icontains=search_terms[0]) &
                    Q(last_name__icontains=search_terms[-1])
                )
            else:
                queryset = queryset.filter(
                    Q(email__icontains=search_term) |
                    Q(first_name__icontains=search_term) |
                    Q(last_name__icontains=search_term)
                )

        if applied_contributors:
            queryset = queryset.filter(applied_contributor=True)

        # Serialize data
        serializer = UserSerializer(queryset, many=True)
        return Response(serializer.data)


class ApplicationActivityStats(APIView):
    permission_classes = [IsAuthenticated, IsAdminUser]

    def get(self, request):
        # Get date range from query parameters
        start_date = request.query_params.get('start_date')
        end_date = request.query_params.get('end_date')
        group_by = request.query_params.get('group_by', 'day')  # Default to day if not specified

        if not start_date or not end_date:
            return Response({"error": "start_date and end_date parameters are required."}, status=status.HTTP_400_BAD_REQUEST)

        # Convert dates from string to datetime objects
        try:
            start_date = datetime.strptime(start_date, "%Y-%m-%d")
            end_date = datetime.strptime(end_date, "%Y-%m-%d")
        except ValueError:
            return Response({"error": "Invalid date format. Use YYYY-MM-DD."}, status=status.HTTP_400_BAD_REQUEST)

        # Map group_by to corresponding Django Trunc functions
        trunc_mappings = {
            'day': TruncDay,
            'month': TruncMonth,
            'year': TruncYear
        }

        if group_by not in trunc_mappings:
            return Response({"error": "Invalid group_by parameter. Choose 'day', 'month', or 'year'."}, status=status.HTTP_400_BAD_REQUEST)

        # Group and count registrations
        contributor_requests = User.objects.filter(date_joined__range=(start_date, end_date), applied_contributor=True).count()
        approved_contributors = User.objects.filter(date_joined__range=(start_date, end_date), applied_contributor=True, approved_contributor=True).count()
        videos_created = Order.objects.filter(status="Delivered").count()
        refunds_requested = Order.objects.filter(status="Refund Requested").count()

        # Serialize data
        return Response({
            "contributor_requests": contributor_requests,
            "approved_contributors": approved_contributors,
            "videos_created": videos_created,
            "refunds_requested": refunds_requested,
        })



class AdminUserViewSet(ModelViewSet):
    serializer_class = AdminUserSerializer
    permission_classes = [IsAuthenticated, IsAdminUser]
    queryset = User.objects.all()
    filter_backends = [DjangoFilterBackend, SearchFilter]
    filterset_fields = ['approved_contributor', 'contributor__category', 'city', 'state', 'country', 'is_superuser']
    search_fields = ['name']

    @action(detail=False, methods=['post'])
    def approve(self, request):
        user_id = request.data.get('user_id')
        if not user_id:
            return Response({"error": "user_id parameter is required."}, status=status.HTTP_400_BAD_REQUEST)

        try:
            user = User.objects.get(id=user_id)
        except User.DoesNotExist:
            return Response({"error": "User does not exist."}, status=status.HTTP_400_BAD_REQUEST)

        user.approved_contributor = True
        user.save()

        return Response({"message": "User approved."}, status=status.HTTP_200_OK)

    @action(detail=False, methods=['post'])
    def deny(self, request):
        user_id = request.data.get('user_id')
        if not user_id:
            return Response({"error": "user_id parameter is required."}, status=status.HTTP_400_BAD_REQUEST)

        try:
            user = User.objects.get(id=user_id)
        except User.DoesNotExist:
            return Response({"error": "User does not exist."}, status=status.HTTP_400_BAD_REQUEST)

        user.missing_information = request.data.get('missing_information', '')
        user.denied_contributor = True
        user.approved_contributor = False
        user.save()

        return Response({"message": "User denied."}, status=status.HTTP_200_OK)

    @action(detail=False, methods=['get'])
    def orders(self, request):
        user_id = request.query_params.get('user_id')
        role_type = request.query_params.get('role_type')

        if not user_id:
            return Response({"error": "user_id parameter is required."}, status=status.HTTP_400_BAD_REQUEST)
        if role_type not in ['contributor', 'consumer']:
            return Response({"error": "Invalid or missing role_type parameter. Choose 'contributor' or 'consumer'."}, status=status.HTTP_400_BAD_REQUEST)

        try:
            user = User.objects.get(id=user_id)
        except User.DoesNotExist:
            return Response({"error": "User does not exist."}, status=status.HTTP_400_BAD_REQUEST)

        if role_type == 'contributor':
            if hasattr(user, 'contributor'):
                orders = Order.objects.filter(contributor=user.contributor)
            else:
                return Response({"error": "This user does not have a contributor profile."}, status=status.HTTP_404_NOT_FOUND)
        elif role_type == 'consumer':
            if hasattr(user, 'consumer'):
                orders = Order.objects.filter(consumer=user.consumer)
            else:
                return Response({"error": "This user does not have a consumer profile."}, status=status.HTTP_404_NOT_FOUND)

        serializer = OrderSerializer(orders, many=True)
        return Response(serializer.data)

    @action(detail=False, methods=['post'])
    def close_account(self, request):
        user_id = request.data.get('user_id')
        if not user_id:
            return Response({"error": "user_id parameter is required."}, status=status.HTTP_400_BAD_REQUEST)

        try:
            user = User.objects.get(id=user_id)
        except User.DoesNotExist:
            return Response({"error": "User does not exist."}, status=status.HTTP_400_BAD_REQUEST)

        user.is_active = False
        user.save()

        return Response({"message": "User account deactivated."}, status=status.HTTP_200_OK)

    @action(detail=False, methods=['post'])
    def open_account(self, request):
        user_id = request.data.get('user_id')
        if not user_id:
            return Response({"error": "user_id parameter is required."}, status=status.HTTP_400_BAD_REQUEST)

        try:
            user = User.objects.get(id=user_id)
        except User.DoesNotExist:
            return Response({"error": "User does not exist."}, status=status.HTTP_400_BAD_REQUEST)

        user.is_active = True
        user.save()

        return Response({"message": "User account activated."}, status=status.HTTP_200_OK)

    @action(detail=False, methods=['post'])
    def pause_account(self, request):
        user_id = request.data.get('user_id')
        if not user_id:
            return Response({"error": "user_id parameter is required."}, status=status.HTTP_400_BAD_REQUEST)

        try:
            user = User.objects.get(id=user_id)
        except User.DoesNotExist:
            return Response({"error": "User does not exist."}, status=status.HTTP_400_BAD_REQUEST)

        user.is_paused = True
        user.save()

        return Response({"message": "User account paused."}, status=status.HTTP_200_OK)

    @action(detail=False, methods=['post'])
    def resume_account(self, request):
        user_id = request.data.get('user_id')
        if not user_id:
            return Response({"error": "user_id parameter is required."}, status=status.HTTP_400_BAD_REQUEST)

        try:
            user = User.objects.get(id=user_id)
        except User.DoesNotExist:
            return Response({"error": "User does not exist."}, status=status.HTTP_400_BAD_REQUEST)

        user.is_paused = False
        user.save()

        return Response({"message": "User account resumed."}, status=status.HTTP_200_OK)

    @action(detail=False, methods=['post'])
    def add_tag(self, request):
        user_id = request.data.get('user_id')
        if not user_id:
            return Response({"error": "user_id parameter is required."}, status=status.HTTP_400_BAD_REQUEST)

        try:
            user = User.objects.get(id=user_id)
        except User.DoesNotExist:
            return Response({"error": "User does not exist."}, status=status.HTTP_400_BAD_REQUEST)

        tag_name = request.data.get('tag')
        if not tag_name:
            return Response({"error": "tag parameter is required."}, status=status.HTTP_400_BAD_REQUEST)

        contributor = user.contributor
        tag, created = Tag.objects.get_or_create(name=tag_name)
        contributor.tags.add(tag)
        return Response({"status": "Tag added"}, status=status.HTTP_200_OK)

    @action(detail=False, methods=['post'])
    def remove_tag(self, request):
        user_id = request.data.get('user_id')
        if not user_id:
            return Response({"error": "user_id parameter is required."}, status=status.HTTP_400_BAD_REQUEST)

        try:
            user = User.objects.get(id=user_id)
        except User.DoesNotExist:
            return Response({"error": "User does not exist."}, status=status.HTTP_400_BAD_REQUEST)

        tag_name = request.data.get('tag')
        if not tag_name:
            return Response({"error": "tag parameter is required."}, status=status.HTTP_400_BAD_REQUEST)

        contributor = user.contributor
        tag, created = Tag.objects.get_or_create(name=tag_name)
        contributor.tags.remove(tag)
        return Response({"status": "Tag removed"}, status=status.HTTP_200_OK)

    @action(detail=False, methods=['get'])
    def turnaround_times(self, request):
        user_id = request.query_params.get('user_id')
        if not user_id:
            return Response({"error": "user_id parameter is required."}, status=status.HTTP_400_BAD_REQUEST)

        try:
            user = User.objects.get(id=user_id)
        except User.DoesNotExist:
            return Response({"error": "User does not exist."}, status=status.HTTP_400_BAD_REQUEST)

        contributor = user.contributor
        normal = Order.objects.filter(contributor=contributor, turnaround_selected="Normal").count()
        fast = Order.objects.filter(contributor=contributor, turnaround_selected="Fast").count()
        same_day = Order.objects.filter(contributor=contributor, turnaround_selected="Same Day").count()

        return Response({
            "normal": normal,
            "fast": fast,
            "same_day": same_day
        })

    @action(detail=False, methods=['get'])
    def posts(self, request):
        user_id = request.query_params.get('user_id')
        if not user_id:
            return Response({"error": "user_id parameter is required."}, status=status.HTTP_400_BAD_REQUEST)

        try:
            user = User.objects.get(id=user_id)
        except User.DoesNotExist:
            return Response({"error": "User does not exist."}, status=status.HTTP_400_BAD_REQUEST)

        posts = Post.objects.filter(contributor=user.contributor)
        serializer = PostSerializer(posts, many=True, context={"request": request})
        return Response(serializer.data)


    @action(detail=False, methods=['post'])
    def change_booking_fee(self, request):
        fee = request.data.get('fee')
        BookingFee.objects.all().update(fee=fee)
        return Response({"message": "Fee changed."}, status=status.HTTP_200_OK)

    @action(detail=False, methods=['get'])
    def get_booking_fee(self, request):
        return Response({"fee": BookingFee.objects.first().fee}, status=status.HTTP_200_OK)

    @action(detail=False, methods=['get'])
    def list_global_tags(self, request):
        search_name = request.query_params.get('search_name')

        tags = Tag.objects.filter(display=True)
        if search_name:
            tags = tags.filter(name__icontains=search_name)
        serializer = AdminTagSerializer(tags, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)

    @action(detail=False, methods=['post'])
    def deactivate_global_tag(self, request):
        tag_name = request.data.get('tag')
        if not tag_name:
            return Response({"error": "tag parameter is required."}, status=status.HTTP_400_BAD_REQUEST)

        try:
            tag = Tag.objects.get(name=tag_name)
        except Tag.DoesNotExist:
            return Response({"error": "Tag does not exist."}, status=status.HTTP_400_BAD_REQUEST)

        tag.active = False
        tag.save()

        return Response({"message": "Tag deactivated."}, status=status.HTTP_200_OK)

    @action(detail=False, methods=['post'])
    def add_global_tag(self, request):
        tag_name = request.data.get('tag')
        active = request.data.get('active').lower()
        if not tag_name:
            return Response({"error": "tag parameter is required."}, status=status.HTTP_400_BAD_REQUEST)

        tag, created = Tag.objects.get_or_create(name=tag_name)
        tag.display = True
        if active == 'true':
            tag.active = True
        else:
            tag.active = False
        tag.save()

        return Response({"message": "Tag added."}, status=status.HTTP_200_OK)

    @action(detail=False, methods=['post'])
    def delete_global_tag(self, request):
        tag_name = request.data.get('tag')
        if not tag_name:
            return Response({"error": "tag parameter is required."}, status=status.HTTP_400_BAD_REQUEST)

        try:
            tag = Tag.objects.get(name=tag_name)
        except Tag.DoesNotExist:
            return Response({"error": "Tag does not exist."}, status=status.HTTP_400_BAD_REQUEST)

        tag.delete()

        return Response({"message": "Tag deleted."}, status=status.HTTP_200_OK)

    @action(detail=False, methods=['get'])
    def users_by_tag(self, request):
        tag_name = request.query_params.get('tag_name')
        search_name = request.query_params.get('search_name')

        if not tag_name:
            return Response({'error': 'Tag name is required'}, status=status.HTTP_400_BAD_REQUEST)

        try:
            # Filter users whose associated contributors are tagged with the specified tag name
            users = User.objects.filter(
                contributor__tags__name__icontains=tag_name
            ).distinct()
            if search_name:
                users = users.filter(name__icontains=search_name)

            serializer = AdminUserSerializer(users, many=True)
            return Response(serializer.data)
        except Exception as e:
            return Response({'error': str(e)}, status=status.HTTP_400_BAD_REQUEST)

    @action(detail=False, methods=['get'])
    def list_categories(self, request):
        search_name = request.query_params.get('search_name')

        categories = Category.objects.all()
        if search_name:
            categories = categories.filter(name__icontains=search_name)
        serializer = CategorySerializer(categories, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)

    @action(detail=False, methods=['delete'])
    def delete_category(self, request):
        category_id = request.query_params.get('category_id')
        if not category_id:
            return Response({'error': 'Category ID is required'}, status=status.HTTP_400_BAD_REQUEST)

        try:
            category = Category.objects.get(id=category_id)
        except Category.DoesNotExist:
            return Response({'error': 'Category does not exist'}, status=status.HTTP_400_BAD_REQUEST)

        category.delete()

        return Response('Category deleted', status=status.HTTP_200_OK)

    @action(detail=False, methods=['get'])
    def list_contributors_by_category(self, request):
        category_id = request.query_params.get('category_id')
        search_name = request.query_params.get('search_name')

        if not category_id:
            return Response({'error': 'Category ID is required'}, status=status.HTTP_400_BAD_REQUEST)

        try:
            users = User.objects.filter(contributor__category_id=category_id).distinct()
            if search_name:
                users = users.filter(name__icontains=search_name)
            serializer = AdminUserSerializer(users, many=True)
            return Response(serializer.data)
        except ValueError:
            return Response({'error': 'Invalid Category ID'}, status=status.HTTP_400_BAD_REQUEST)

    @action(detail=False, methods=['get'])
    def refund_requests(self, request):
        search_name = request.query_params.get('search_name')
        orders = Order.objects.filter(status="Refund Requested")
        if search_name:
            orders = orders.filter(
                Q(contributor__user__name__icontains=search_name) | 
                Q(consumer__user__name__icontains=search_name)
            )
        serializer = OrderSerializer(orders, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)


class AdminBannedWordViewSet(ModelViewSet):
    serializer_class = BannedWordSerializer
    permission_classes = [IsAuthenticated, IsAdminUser]
    queryset = BannedWord.objects.all()


class AdminFeedbackViewSet(ModelViewSet):
    serializer_class = FeedbackSerializer
    permission_classes = [IsAuthenticated, IsAdminUser]
    queryset = Feedback.objects.all()

    def perform_create(self, serializer):
        serializer.save(user=self.request.user)

    @action(detail=False, methods=['post'])
    def respond(self, request):
        feedback_id = request.data.get('feedback_id')
        if not feedback_id:
            return Response({"error": "feedback_id parameter is required."}, status=status.HTTP_400_BAD_REQUEST)

        try:
            feedback = Feedback.objects.get(id=feedback_id)
        except Feedback.DoesNotExist:
            return Response({"error": "Feedback does not exist."}, status=status.HTTP_400_BAD_REQUEST)

        feedback.respond = True
        feedback.response = request.data.get('response', '')
        feedback.save()

        return Response({"message": "Feedback responded."}, status=status.HTTP_200_OK)

    @action(detail=False, methods=['post'])
    def mark_read(self, request):
        feedback_id = request.data.get('feedback_id')
        if not feedback_id:
            return Response({"error": "feedback_id parameter is required."}, status=status.HTTP_400_BAD_REQUEST)

        try:
            feedback = Feedback.objects.get(id=feedback_id)
        except Feedback.DoesNotExist:
            return Response({"error": "Feedback does not exist."}, status=status.HTTP_400_BAD_REQUEST)

        feedback.admin_read = True
        feedback.save()

        return Response({"message": "Feedback marked as read."}, status=status.HTTP_200_OK)

    @action(detail=False, methods=['get'])
    def mark_all_read(self, request):
        Feedback.objects.all().update(admin_read=True)
        return Response({"message": "Feedbacks marked as read."}, status=status.HTTP_200_OK)

    @action(detail=False, methods=['get'])
    def mark_selected_read(self, request):
        feedback_ids = request.query_params.get('feedback_ids')
        if not feedback_ids:
            return Response({"error": "feedback_ids parameter is required."}, status=status.HTTP_400_BAD_REQUEST)

        feedback_ids = feedback_ids.split(',')
        Feedback.objects.filter(id__in=feedback_ids).update(admin_read=True)
        return Response({"message": "Feedbacks marked as read."}, status=status.HTTP_200_OK)

    @action(detail=False, methods=['delete'])
    def delete_selected_feedback(self, request):
        feedback_ids = request.query_params.get('feedback_ids')
        if not feedback_ids:
            return Response({"error": "feedback_ids parameter is required."}, status=status.HTTP_400_BAD_REQUEST)

        feedback_ids = feedback_ids.split(',')
        Feedback.objects.filter(id__in=feedback_ids).delete()

        return Response({"message": f"Deleted feedback(s)."}, status=status.HTTP_200_OK)


class AdminCategoryViewSet(ModelViewSet):
    serializer_class = CategorySerializer
    permission_classes = [IsAuthenticated, IsAdminUser]
    queryset = Category.objects.all()
