from django.db import models
from django.contrib.auth import get_user_model


User = get_user_model()


class Contributor(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    phone = models.CharField(max_length=20, blank=True)
    state = models.CharField(max_length=255, blank=True)
    city = models.CharField(max_length=255, blank=True)
    website = models.CharField(max_length=255, blank=True)
    category = models.ForeignKey(
        "categories.Category",
        on_delete=models.SET_NULL,
        null=True,
        blank=True
    )


class ContributorPhotoVideo(models.Model):
    contributor = models.ForeignKey(Contributor, on_delete=models.CASCADE, related_name="photos_videos")
    file = models.FileField(upload_to="contributor_display_files")
    title = models.CharField(max_length=255, blank=True)
    description = models.TextField(blank=True)
