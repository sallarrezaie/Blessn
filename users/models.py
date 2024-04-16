from django.contrib.auth.models import AbstractUser
from django.db import models
from django.urls import reverse
from django.utils.translation import ugettext_lazy as _


class User(AbstractUser):
    # First Name and Last Name do not cover name patterns
    # around the globe.
    username = models.CharField(_("Username"), unique=False, max_length=255, blank=True, null=True)
    name = models.CharField(_("Name of User"), blank=True, null=True, max_length=255)
    first_name = models.CharField(_("First Name"), blank=True, max_length=255)
    last_name = models.CharField(_("Last Name"), blank=True, max_length=255)
    email = models.EmailField(_("Email of User"), unique=True)
    dob = models.DateField(_("Date of Birth"), blank=True, null=True)
    picture = models.ImageField(_("Profile Picture"), blank=True, null=True, upload_to="users/pictures")
    about_me = models.TextField(_("About Me"), blank=True)
    terms_accepted = models.BooleanField(default=False)
    otp = models.CharField(max_length=6, blank=True)
    activation_key = models.CharField(max_length=255, blank=True)
    applied_contributor = models.BooleanField(default=False)
    approved_contributor = models.BooleanField(default=False)
    denied_contributor = models.BooleanField(default=False)
    missing_information = models.TextField(blank=True)
    registration_id = models.CharField(max_length=500, blank=True)
    country = models.CharField(max_length=255, blank=True)
    state = models.CharField(max_length=255, blank=True)
    city = models.CharField(max_length=255, blank=True)
    address = models.CharField(max_length=255, blank=True)
    latitude = models.FloatField(blank=True, null=True)
    longitude = models.FloatField(blank=True, null=True)
    postal_code = models.CharField(max_length=255, blank=True)
    is_paused = models.BooleanField(default=False)

    # Notification Settings
    master_notification = models.BooleanField(default=True)
    in_app_notification = models.BooleanField(default=True)
    push_notification = models.BooleanField(default=True)
    email_notification = models.BooleanField(default=True)
    sms_notification = models.BooleanField(default=True)

    blocked_users = models.ManyToManyField('self', blank=True, related_name="blockers", symmetrical=False)

    USERNAME_FIELD = 'email'  # Use email as the login identifier
    REQUIRED_FIELDS = []

    def get_absolute_url(self):
        return reverse("users:detail", kwargs={"username": self.username})


class Follow(models.Model):
    follower = models.ForeignKey(User, related_name="following", on_delete=models.CASCADE)
    followed = models.ForeignKey(User, related_name="followers", on_delete=models.CASCADE)
    created = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ('follower', 'followed')  # Ensures one cannot follow the same person more than once

    def __str__(self):
        return f"{self.follower} follows {self.followed}"
