from django.db import models
from django.contrib.auth import get_user_model


User = get_user_model()


class Consumer(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    stripe_account = models.ForeignKey(
        'djstripe.Customer',
        null=True,
        blank=True,
        on_delete=models.CASCADE
    )
