from django.contrib.auth import get_user_model, authenticate
from django.utils import timezone
from datetime import timedelta
from django.db.models import Q, Sum
from rest_framework import serializers

from contributors.models import Contributor
from contributors.serializers import ContributorSerializer, TagSerializer
from consumers.models import Consumer
from consumers.serializers import ConsumerSerializer
from home.utils import verifyOTP
from posts.models import Post
from .models import Follow


User = get_user_model()


class UserSerializer(serializers.ModelSerializer):
    """
    Custom serializer for creating a User
    """
    consumer = ConsumerSerializer(required=False)
    contributor = ContributorSerializer(required=False)
    password_2 = serializers.CharField(required=False)
    is_blocked = serializers.SerializerMethodField()
    is_followed = serializers.SerializerMethodField()


    class Meta:
        model = get_user_model()
        fields = ('id', 'username', 'name', 'first_name', 'last_name', 'email', 'password', 'password_2', 'terms_accepted', 'dob', 'about_me',
                  'consumer', 'contributor', 'applied_contributor', 'approved_contributor', 'picture', 'master_notification', 'in_app_notification', 
                  'push_notification', 'email_notification','sms_notification', 'registration_id', 'country', 'state', 'city', 'address', 'latitude', 
                  'longitude', 'postal_code', 'is_blocked', 'is_followed')
        extra_kwargs = {'password': {'write_only': True, 'min_length': 5},
                        'password_2': {'write_only': True, 'min_length': 5},
                        'email': {'required': True},
                        'name': {'required': False},
                        }

    def validate_email(self, value):
        value = value.lower()
        User = get_user_model()
        if self.instance and self.instance.pk:
            # If the email belongs to the same user, allow it
            if User.objects.filter(email=value).exclude(pk=self.instance.pk).exists():
                raise serializers.ValidationError({"Validation Error": 'User with this email address already exists.'})
        else:
            # This is for the case when creating a new user, should not happen
            # in the update scenario, but just in case you use the same serializer
            # for both create and update actions.

            if User.objects.filter(email=value).exists():
                raise serializers.ValidationError({"Validation Error": 'User with this email address already exists.'})
        return value

    def create(self, validated_data):
        password = validated_data.pop('password')
        password_2 = validated_data.pop('password_2')
        if password != password_2:
            raise serializers.ValidationError({'password': 'Passwords do not match'})
        validated_data['email'] = validated_data['email'].lower()
        email = validated_data.get('email')
        username = validated_data.get('username', None)
        if not username:
            validated_data['username'] = email

        # Set name based on first_name and last_name
        first_name = validated_data.get('first_name', '')
        last_name = validated_data.get('last_name', '')
        validated_data['name'] = f"{first_name} {last_name}".strip()

        user = User.objects.create(**validated_data)
        user.set_password(password)
        user.save()
        Consumer.objects.create(user=user)
        return user


    def update(self, instance, validated_data):
        email = validated_data.get('email', None)
        if email:
            email = email.lower()
            if User.objects.filter(email=email).exists():
                raise serializers.ValidationError({"Validation Error": 'User with this email address already exists.'})
        username = validated_data.get('username', None)
        if username:
            if User.objects.filter(username=username).exclude(pk=instance.pk).exists():
                raise serializers.ValidationError({"Validation Error": 'User with this username already exists.'})

        first_name = validated_data.get('first_name', instance.first_name)
        last_name = validated_data.get('last_name', instance.last_name)
        validated_data['name'] = f"{first_name} {last_name}".strip()

        created = False
        if 'consumer' in validated_data:
            nested_serializer = self.fields['consumer']
            nested_instance = instance.consumer
            nested_data = validated_data.pop('consumer')
            nested_serializer.update(nested_instance, nested_data)
        if 'contributor' in validated_data:
            nested_serializer = self.fields['contributor']
            nested_instance, created = Contributor.objects.get_or_create(user=instance)
            nested_data = validated_data.pop('contributor')
            nested_serializer.update(nested_instance, nested_data)
        user = super().update(instance, validated_data)
        if created:
            user.applied_contributor = True
            user.save()
        return user

    def get_is_blocked(self, obj):
        request = self.context.get('request', None)
        if request and hasattr(request, 'user') and request.user.is_authenticated:
            return request.user.blocked_users.filter(pk=obj.pk).exists()
        return False

    def get_is_followed(self, obj):
        request = self.context.get('request', None)
        if request and hasattr(request, 'user') and request.user.is_authenticated:
            return Follow.objects.filter(follower=request.user, followed=obj).exists()
        return False


class ExtendedUserSerializer(UserSerializer):
    new_posts_count = serializers.SerializerMethodField()

    class Meta(UserSerializer.Meta):
        fields = list(UserSerializer.Meta.fields) + ['new_posts_count']

    def get_new_posts_count(self, obj):
        if hasattr(obj, 'contributor'):
            time_threshold = timezone.now() - timedelta(days=1)
            return Post.objects.filter(contributor=obj.contributor, created_at__gte=time_threshold).count()
        else:
            return None


class ResetPasswordSerializer(serializers.Serializer):
    """
    Custom serializer used to set the password for a User
    """
    password_1 = serializers.CharField(
        min_length=4,
        write_only=True,
        required=True,
        style={'input_type': 'password'}
    )
    password_2 = serializers.CharField(
        min_length=4,
        write_only=True,
        required=True,
        style={'input_type': 'password'}
    )

    def validate(self, attrs):
        pass1 = attrs.get('password_1')
        pass2 = attrs.get('password_2')
        if pass1 != pass2:
            raise serializers.ValidationError({'detail': 'Passwords do not match'})
        return super().validate(attrs)


class ChangePasswordSerializer(serializers.Serializer):
    """
    Custom serializer used to set the password for a User
    """
    password_1 = serializers.CharField(
        min_length=4,
        write_only=True,
        required=True,
        style={'input_type': 'password'}
    )
    password_2 = serializers.CharField(
        min_length=4,
        write_only=True,
        required=True,
        style={'input_type': 'password'}
    )
    current_password = serializers.CharField(
        min_length=4,
        write_only=True,
        required=True,
        style={'input_type': 'password'}
    )

    def validate(self, attrs):
        pass1 = attrs.get('password_1')
        pass2 = attrs.get('password_2')
        if pass1 != pass2:
            raise serializers.ValidationError({'detail': 'Passwords do not match'})
        return super().validate(attrs)


class CustomAuthTokenSerializer(serializers.Serializer):
    """
    Serializer for returning an authenticated User and Token
    """
    email = serializers.EmailField(required=True)
    password = serializers.CharField(style={'input_type': 'password'}, trim_whitespace=False, required=True)

    def validate(self, attrs):
        email = attrs.get('email')
        password = attrs.get('password')
        user = authenticate(
            request=self.context.get('request'),
            email=email,
            password=password
        )
        if not user:
            raise serializers.ValidationError({'Validation Error:' 'The email and/or the password do not match an existing account.'})
        attrs['user'] = user
        return attrs


class OTPSerializer(serializers.Serializer):
    """
    Custom serializer to verify an OTP
    """
    otp = serializers.CharField(max_length=6, required=True)
    email = serializers.CharField(required=True)

    def validate(self, attrs):
        email = attrs.get('email').lower()
        otp = attrs.get('otp')
        try:
            user = User.objects.get(email=email)
        except User.DoesNotExist:
            raise serializers.ValidationError({'detail': 'Invalid Email'})
        else:
            if verifyOTP(otp=otp, user=user):
                user.activation_key = ''
                user.otp = ''
                user.save()
                attrs['user'] = user
                return attrs
            else:
                raise serializers.ValidationError({'detail': 'Invalid or Expired OTP, please try again'})


class AdminUserSerializer(serializers.ModelSerializer):
    """
    Custom serializer for creating a User
    """
    consumer = ConsumerSerializer(required=False)
    contributor = ContributorSerializer(required=False)
    tags = TagSerializer(required=False, many=True)
    contributor_video_count = serializers.SerializerMethodField()
    consumer_refund_count = serializers.SerializerMethodField()
    consumer_video_count = serializers.SerializerMethodField()
    consumer_spent_amount = serializers.SerializerMethodField()

    class Meta:
        model = get_user_model()
        fields = '__all__'

    def get_contributor_video_count(self, obj):
        if hasattr(obj, 'contributor'):
            return obj.contributor.orders.filter(status="Delivered").count()
        else:
            return None

    def get_consumer_video_count(self, obj):
        if hasattr(obj, 'consumer'):
            return obj.consumer.orders.all().count()
        else:
            return None

    def get_consumer_refund_count(self, obj):
        if hasattr(obj, 'consumer'):
            return obj.consumer.orders.filter(Q(status="Refunded") | Q(status="Refund Requested")).count()
        else:
            return None

    def get_consumer_spent_amount(self, obj):
        if hasattr(obj, 'consumer'):
            return obj.consumer.payments.filter(refunded=False).aggregate(Sum('amount'))['amount__sum']
        else:
            return None
