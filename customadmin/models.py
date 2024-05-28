from django.db import models


class BannedWord(models.Model):
    word = models.CharField(
        max_length=255
    )
