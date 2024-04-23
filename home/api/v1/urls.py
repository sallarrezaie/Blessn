from django.urls import path, include
from rest_framework.routers import DefaultRouter

from home.api.v1.viewsets import (
    SignupViewSet,
    LoginViewSet,
)

from users.viewsets import UserViewSet
from contributors.views import ContributorPhotoVideoViewSet
from categories.views import CategoryViewSet
from feedback.views import FeedbackViewSet
from terms_and_conditions.views import TermAndConditionViewSet
from privacy_policy.views import PrivacyPolicyViewSet
from notifications.views import NotificationViewSet
from dropdowns.views import OccasionViewSet
from payments.views import PaymentViewSet
from orders.views import OrderViewSet
from posts.views import PostViewSet, CommentViewSet
from chat.views import ChatChannelViewSet
from customadmin.views import RegistrationStats, RegistrationStatsProfiles, ApplicationActivityStats, AdminUserViewSet, AdminFeedbackViewSet

router = DefaultRouter()
router.register("signup", SignupViewSet, basename="signup")
router.register("login", LoginViewSet, basename="login")
router.register("users", UserViewSet, basename="users")
router.register("contributors/photo-video", ContributorPhotoVideoViewSet, basename="contributors/photo-video")
router.register("categories", CategoryViewSet, basename="categories")
router.register("feedback", FeedbackViewSet, basename="feedback")
router.register("terms-and-conditions", TermAndConditionViewSet, basename="terms-and-conditions")
router.register("privacy-policy", PrivacyPolicyViewSet, basename="privacy-policy")
router.register("notifications", NotificationViewSet, basename="notifications")
router.register("occasions", OccasionViewSet, basename="occasions")
router.register("payments", PaymentViewSet, basename="payments")
router.register('orders', OrderViewSet, basename='orders')
router.register("posts", PostViewSet, basename='posts')
router.register("comments", CommentViewSet, basename='comments')
router.register("chat", ChatChannelViewSet, basename="chat")
router.register("admin/admin-users", AdminUserViewSet, basename="admin-users")
router.register("admin/admin-feedbacks", AdminFeedbackViewSet, basename="admin-feedbacks")

urlpatterns = [
    path("", include(router.urls)),
    path("socials/", include(("socialauth.urls", "socialauth"), namespace="socialauth")),
    path("admin/registration-stats/", RegistrationStats.as_view(), name="registration-stats"),
    path("admin/registration-stats-profiles/", RegistrationStatsProfiles.as_view(), name="registration-stats-profiles"),
    path("admin/application-activity-stats/", ApplicationActivityStats.as_view(), name="application-activity-stats"),
]
