from django.db import models
from contributors.models import Contributor


class Category(models.Model):
    name = models.CharField(max_length=255)
    picture = models.ImageField(upload_to="categories/pictures", blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name_plural = "Categories"

    def __str__(self):
        return self.name

    def contributor_count(self):
        return Contributor.objects.filter(category=self).count()