from django.db import models

from users.models import User


# released
class Feedback(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='feedback')
    email = models.CharField(max_length=255, blank=True)
    message = models.TextField()
    responded = models.BooleanField(default=False)
    response = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    admin_read = models.BooleanField(default=False)

    class Meta:
        verbose_name_plural = "Feedback"

    def __str__(self):
        return self.email
