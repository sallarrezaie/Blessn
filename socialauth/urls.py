from django.urls import path
from .views import (
    FacebookLogin,
    GoogleLogin,
    AppleLogin,
    FacebookConnect,
    GoogleConnect,
    AppleConnect,
)
from rest_auth.registration.views import (
    SocialAccountListView,
    SocialAccountDisconnectView,
)

urlpatterns = [
    # login endpoints - used in social login
    path("facebook/login/", FacebookLogin.as_view(), name="social_facebook_login"),
    path("google/login/", GoogleLogin.as_view(), name="social_google_login"),
    path("apple/login/", AppleLogin.as_view(), name="social_apple_login"),
    # connect endpoints - can be used to implement connect to existing account
    path("facebook/connect/", FacebookConnect.as_view(), name="social_facebook_connect"),
    path("google/connect/", GoogleConnect.as_view(), name="social_google_connect"),
    path("apple/connect/", AppleConnect.as_view(), name="social_apple_connect"),
    path(
        "socialaccounts/", SocialAccountListView.as_view(), name="social_account_list"
    ),
    # Allows to disconnect social account
    path(
        "socialaccounts/<int:pk>/disconnect/",
        SocialAccountDisconnectView.as_view(),
        name="social_account_disconnect",
    ),
]
