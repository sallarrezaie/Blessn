from django.contrib.auth import get_user_model
from django.core.mail import EmailMessage
from django.core.exceptions import ObjectDoesNotExist
from django.contrib.auth.hashers import check_password

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
from .serializers import UserSerializer, ResetPasswordSerializer, CustomAuthTokenSerializer, OTPSerializer, ChangePasswordSerializer


User = get_user_model()


class UserViewSet(ModelViewSet):
    serializer_class = UserSerializer
    permission_classes = (IsPostOrIsAuthenticated,)
    authentication_classes  = [TokenAuthentication]
    queryset = User.objects.all()
    filter_backends = [DjangoFilterBackend, SearchFilter]
    filterset_fields = ['approved_contributor', 'contributor__category']
    search_fields = ['name']

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
