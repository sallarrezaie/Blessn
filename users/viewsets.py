from django.contrib.auth import get_user_model
from django.core.mail import EmailMessage
from django.core.exceptions import ObjectDoesNotExist
from django.contrib.auth.hashers import check_password
from django.db.models import Q, Avg
from math import radians, cos

from django_filters.rest_framework import DjangoFilterBackend

from rest_framework import status
from rest_framework.authtoken.models import Token
from rest_framework.authentication import TokenAuthentication
from rest_framework.decorators import action
from rest_framework.filters import SearchFilter
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.viewsets import ModelViewSet

from blessn.settings import SENDGRID_EMAIL
from home.utils import send_otp, auth_token, send_email
from home.permissions import IsPostOrIsAuthenticated
from .serializers import UserSerializer, ResetPasswordSerializer, CustomAuthTokenSerializer, OTPSerializer, ChangePasswordSerializer, \
    ExtendedUserSerializer
from .models import Follow
from contributors.models import Tag
from contributors.serializers import TagSerializer


User = get_user_model()


class UserViewSet(ModelViewSet):
    serializer_class = UserSerializer
    permission_classes = (IsPostOrIsAuthenticated,)
    authentication_classes  = [TokenAuthentication]
    queryset = User.objects.all()
    filter_backends = [DjangoFilterBackend, SearchFilter]
    filterset_fields = ['approved_contributor', 'contributor__category', 'city', 'state', 'country']
    search_fields = ['name']

    def get_queryset(self):
        queryset = super().get_queryset()
        tags = self.request.query_params.getlist('tags')
        min_rating = self.request.query_params.get('min_rating', None)

        queryset = queryset.annotate(
            average_rating=Avg('contributor__reviews__rating')
        )

        if tags:
            queryset = queryset.filter(contributor__tags__name__in=tags).distinct()

        if min_rating:
            queryset = queryset.filter(average_rating__gte=min_rating)

        lat = self.request.query_params.get('latitude')
        lon = self.request.query_params.get('longitude')
        if lat and lon:
            # Convert latitude and longitude to floats
            lat = float(lat)
            lon = float(lon)

            # Assuming a rough approximation of 69 miles per degree
            miles_per_degree = 69.0
            distance = 50  # Distance in miles

            # Calculate the latitude and longitude deltas
            delta_lat = distance / miles_per_degree
            delta_lon = distance / (miles_per_degree * cos(radians(lat)))

            # Calculate the square bounding box
            min_lat = lat - delta_lat
            max_lat = lat + delta_lat
            min_lon = lon - delta_lon
            max_lon = lon + delta_lon

            queryset = queryset.filter(latitude__gte=min_lat, latitude__lte=max_lat,
                                       longitude__gte=min_lon, longitude__lte=max_lon)

        return queryset

    # Create User and return Token + Profile
    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        self.perform_create(serializer)
        headers = self.get_success_headers(serializer.data)
        token, created = Token.objects.get_or_create(user=serializer.instance)
        return Response({'user': serializer.data, 'token': token.key}, status=status.HTTP_201_CREATED, headers=headers) 

    @action(detail=False, methods=['post'], permission_classes=[IsAuthenticated])
    def reset_password(self, request):
        serializer = ResetPasswordSerializer(data=request.data)
        if serializer.is_valid():
            user = request.user
            user.set_password(serializer.validated_data['password_1'])
            user.save()
            return Response({'detail': "Password Updated Successfully"}, status=status.HTTP_200_OK)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    @action(detail=False, methods=['post'], permission_classes=[IsAuthenticated])
    def change_password(self, request):
        serializer = ChangePasswordSerializer(data=request.data)
        if serializer.is_valid():
            user = request.user
            current_password = serializer.validated_data['current_password']
            
            # Check if the current password is correct
            if not check_password(current_password, user.password):
                return Response({'detail': "Current password is incorrect"}, status=status.HTTP_400_BAD_REQUEST)

            # If the current password is correct, proceed to set the new password
            user.set_password(serializer.validated_data['password_1'])
            user.save()
            return Response({'detail': "Password Updated Successfully"}, status=status.HTTP_200_OK)
        
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    # Login a User
    @action(detail=False, methods=['post'])
    def login(self, request, **kwargs):
        serializer = CustomAuthTokenSerializer(data=request.data, context = {'request':request})
        if serializer.is_valid():
            user = serializer.validated_data['user']
            if not user.is_active:
                return Response({'detail': 'This user has been deactivated. Please contact support for assistance.'}, status=status.HTTP_401_UNAUTHORIZED)
            token = auth_token(user)
            serializer = UserSerializer(user, context = {'request':request})
            return Response({'token': token.key, 'user': serializer.data}, status=status.HTTP_200_OK)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    # Logout a Client
    @action(detail=False, methods=['get'])
    def logout(self, request):
        try:
            request.user.auth_token.delete()
            request.user.save()
        except (AttributeError, ObjectDoesNotExist):
            return Response({'detail': 'Authentication Token Missing or Invalid'}, status=status.HTTP_401_UNAUTHORIZED)
        return Response(status=status.HTTP_200_OK)

    # Request OTP for Login
    @action(detail=False, methods=['post'])
    def request_otp(self, request):
        try:
            email = request.data.get('email')
            user = User.objects.get(email=email)
        except ObjectDoesNotExist:
            return Response({"Validation Error: Email does not match an existing account"}, status=status.HTTP_400_BAD_REQUEST)
        send_otp(user)
        return Response(status=status.HTTP_200_OK)

    # Verify OTP
    @action(detail=False, methods=['post'])
    def verify_otp(self, request):
        serializer = OTPSerializer(data=request.data)
        if serializer.is_valid():
            user = serializer.validated_data['user']
            token = auth_token(user)
            user.otp_confirmed = True
            user.save()
            serializer = UserSerializer(user, context={'request': request})
            return Response({'token': token.key, 'user': serializer.data}, status=status.HTTP_200_OK)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    # Invite Contributor
    @action(detail=False, methods=['post'])
    def invite_contributor(self, request):
        recipient = request.data.get('recipient')
        subject = "Blessn Invitation", 
        message = """You have been invited to join the Blessn Community as a Contributor. Follow the link below to create
                   an account now! <a href="www.blessn.com">www.blessn.com</a>"""
        
        email_msg = EmailMessage(subject, message, from_email=SENDGRID_EMAIL, to=[recipient])
        email_msg.content_subtype = "html"
        email_msg.send()
        return Response(status=status.HTTP_200_OK)


    @action(detail=False, methods=['post'])
    def invite_consumer(self, request):
        recipient = request.data.get('recipient')
        subject = "Blessn Invitation", 
        message = """You have been invited to join the Blessn Community as a Consumer. Follow the link below to create
                   an account now! <a href="www.blessn.com">www.blessn.com</a>"""
        
        email_msg = EmailMessage(subject, message, from_email=SENDGRID_EMAIL, to=[recipient])
        email_msg.content_subtype = "html"
        email_msg.send()
        return Response(status=status.HTTP_200_OK)

    @action(detail=False, methods=['delete'], permission_classes=[IsAuthenticated])
    def deactivate_account(self, request):
        user = request.user
        user.is_active = False
        user.save()
        return Response({'detail': 'Account has been deactivated'}, status=status.HTTP_200_OK)

    @action(detail=False, methods=['delete'], permission_classes=[IsAuthenticated])
    def delete_account(self, request):
        user = request.user
        user.delete()
        return Response({'detail': 'Account has been deleted'}, status=status.HTTP_200_OK)

    @action(detail=False, methods=['post'], permission_classes=[IsAuthenticated])
    def follow(self, request):
        user_to_follow = User.objects.get(pk=request.data.get('user'))
        follow, created = Follow.objects.get_or_create(follower=request.user, followed=user_to_follow)
        if created:
            return Response('You are now following this user.', status=status.HTTP_200_OK)
        else:
            return Response('You are already following this user.', status=status.HTTP_400_BAD_REQUEST)

    @action(detail=False, methods=['post'], permission_classes=[IsAuthenticated])
    def unfollow(self, request):
        user_to_unfollow = User.objects.get(pk=request.data.get('user'))
        follow = Follow.objects.get(follower=request.user, followed=user_to_unfollow)
        follow.delete()
        return Response('You have unfollowed this user.', status=status.HTTP_200_OK)

    @action(detail=False, methods=['get'], permission_classes=[IsAuthenticated])
    def list_following(self, request):
        user_id = request.query_params.get('user_id')
        search = request.query_params.get('search', None)
        user = User.objects.get(id=user_id)

        if search:
            following_users = User.objects.filter(
                Q(followers__follower=user) &
                (
                    Q(name__icontains=search) |
                    Q(first_name__icontains=search) |
                    Q(last_name__icontains=search)
                )
            ).distinct()
        else:
            following_users = User.objects.filter(following__follower=user).distinct()
        serializer = ExtendedUserSerializer(following_users, many=True, context={'request': request})
        return Response(serializer.data)

    @action(detail=False, methods=['get'], permission_classes=[IsAuthenticated])
    def list_followers(self, request):
        user_id = request.query_params.get('user_id')
        search = request.query_params.get('search', None)
        user = User.objects.get(id=user_id)

        if search:
            followers = User.objects.filter(
                Q(following__followed=user) &
                (
                    Q(name__icontains=search) |
                    Q(first_name__icontains=search) |
                    Q(last_name__icontains=search)
                )
            ).distinct()
        else:
            followers = User.objects.filter(following__followed=user).distinct()

        serializer = ExtendedUserSerializer(followers, many=True, context={'request': request})
        return Response(serializer.data)

    @action(detail=False, methods=['post'])
    def add_tag(self, request):
        contributor = request.user.contributor
        tag_name = request.data.get('tag')
        tag, created = Tag.objects.get_or_create(name=tag_name)
        contributor.tags.add(tag)
        return Response({"status": "Tag added"}, status=status.HTTP_200_OK)

    @action(detail=False, methods=['post'])
    def remove_tag(self, request):
        contributor = request.user.contributor
        tag_name = request.data.get('tag')
        try:
            tag = Tag.objects.get(name=tag_name)
            contributor.tags.remove(tag)
            return Response({"status": "Tag removed"}, status=status.HTTP_200_OK)
        except Tag.DoesNotExist:
            return Response({"error": "Tag not found"}, status=status.HTTP_404_NOT_FOUND)

    @action(detail=False, methods=['get'])
    def list_tags(self, request):
        tags = Tag.objects.filter(display=True)
        serializer = TagSerializer(tags, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)
