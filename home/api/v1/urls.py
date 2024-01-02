from django.urls import path, include
from rest_framework.routers import DefaultRouter

from home.api.v1.viewsets import (
    SignupViewSet,
    LoginViewSet,
)

from users.viewsets import UserViewSet
from contributors.views import ContributorPhotoVideoViewSet
from categories.views import CategoryViewSet
from terms_and_conditions.views import TermAndConditionViewSet
from privacy_policy.views import PrivacyPolicyViewSet

router = DefaultRouter()
router.register("signup", SignupViewSet, basename="signup")
router.register("login", LoginViewSet, basename="login")
router.register("users", UserViewSet, basename="users")
router.register("contributors/photo-video", ContributorPhotoVideoViewSet, basename="contributors/photo-video")
router.register("categories", CategoryViewSet, basename="categories")
router.register("terms-and-conditions", TermAndConditionViewSet, basename="terms-and-conditions")
router.register("privacy-policy", PrivacyPolicyViewSet, basename="privacy-policy")


urlpatterns = [
    path("", include(router.urls)),
]
