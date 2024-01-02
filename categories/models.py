from django.db import models


class Category(models.Model):
    name = models.CharField(max_length=255)
    picture = models.ImageField(upload_to="categories/pictures", blank=True, null=True)

    class Meta:
        verbose_name_plural = "Categories"

    def __str__(self):
        return self.name
