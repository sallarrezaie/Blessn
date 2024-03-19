from django.db import models
from django.contrib.auth import get_user_model


User = get_user_model()


class Tag(models.Model):
    name = models.CharField(max_length=100, unique=True)
    display = models.BooleanField(default=False)

    def __str__(self):
        return self.name


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
    connect_account = models.ForeignKey(
        'djstripe.Account',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        help_text="The Contributor's Stripe Connect Account object, if it exists"
    )
    normal_delivery_price = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        default=50
    )
    fast_delivery_price = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        default=100
    )
    same_day_delivery_price = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        default=150
    )
    tags = models.ManyToManyField(Tag, related_name='contributors', blank=True)


class ContributorPhotoVideo(models.Model):
    contributor = models.ForeignKey(Contributor, on_delete=models.CASCADE, related_name="photos_videos")
    file = models.FileField(upload_to="contributor_display_files")
    title = models.CharField(max_length=255, blank=True)
    description = models.TextField(blank=True)
    media_type = models.CharField(max_length=255, blank=True)
    thumbnail = models.FileField(upload_to="contributor_display_files", blank=True, null=True)
