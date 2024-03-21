from django.db import models

from consumers.models import Consumer
from contributors.models import Contributor
from dropdowns.models import Occasion


class Order(models.Model):
    consumer = models.ForeignKey(
        Consumer,
        on_delete=models.SET_NULL,
        null=True,
        related_name="orders"
    )
    contributor = models.ForeignKey(
        Contributor,
        on_delete=models.SET_NULL,
        null=True,
        related_name="orders"
    )
    video_for = models.CharField(
        max_length=255,
        blank=True
    )
    introduce_yourself = models.TextField(
        blank=True
    )
    video_to_say = models.TextField(
        blank=True
    )
    occasion = models.ForeignKey(
        Occasion,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="orders"
    )
    turnaround_selected = models.CharField(
        max_length=255,
        choices=(
            ('Normal', 'Normal'),
            ('Fast', 'Fast'),
            ('Same Day', 'Same Day')
        ),
        default='Normal'
    )
    video_fee = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        default=0
    )
    booking_fee = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        default=0
    )
    total = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        default=0
    )
    status = models.CharField(
        max_length=255,
        choices=(
            ('Pending', 'Pending'),
            ('In Progress', 'In Progress'),
            ('Delivered', 'Delivered'),
            ('Redo Requested', 'Redo Requested'),
            ('Redone', 'Redone'),
            ('Refund Requested', 'Refund Requested'),
            ('Refunded', 'Refunded'),
            ('Cancel Requested', 'Cancel Requested'),
            ('Cancelled', 'Cancelled'),
            ('Flagged', 'Flagged')
        ),
        default='Pending'
    )
    consumer_charge_id = models.CharField(
        max_length=255,
        blank=True,
        null=True
    )
    blessn = models.FileField(
        upload_to="blessn_files/videos",
        blank=True,
        null=True
    )
    cancel_requested_at = models.DateTimeField(
        blank=True,
        null=True
    )
    cancelled_at = models.DateTimeField(
        blank=True,
        null=True
    )
    cancel_reason = models.TextField(
        blank=True
    )
    flagged = models.BooleanField(
        default=False
    )
    flagged_at = models.DateTimeField(
        blank=True,
        null=True
    )
    flagged_reason = models.TextField(
        blank=True
    )
    paid_at = models.DateTimeField(
        blank=True,
        null=True
    )
    delivered_at = models.DateTimeField(
        blank=True,
        null=True
    )
    redo_requested_at = models.DateTimeField(
        blank=True,
        null=True
    )
    redone_at = models.DateTimeField(
        blank=True,
        null=True
    )
    refund_requested_at = models.DateTimeField(
        blank=True,
        null=True
    )
    refunded_at = models.DateTimeField(
        blank=True,
        null=True
    )
    created_at = models.DateTimeField(
        auto_now_add=True
    )
    updated_at = models.DateTimeField(
        auto_now=True
    )
    archived = models.BooleanField(
        default=False
    )
    reviewed = models.BooleanField(
        default=False
    )
    rating = models.IntegerField(
        default=0
    )

    def save(self, *args, **kwargs):
        self.total = self.video_fee + self.booking_fee
        super().save(*args, **kwargs)


class Review(models.Model):
    consumer = models.ForeignKey(
        Consumer,
        on_delete=models.SET_NULL,
        null=True,
        related_name="reviews"
    )
    contributor = models.ForeignKey(
        Contributor,
        on_delete=models.SET_NULL,
        null=True,
        related_name="reviews"
    )
    order = models.OneToOneField(
        Order,
        on_delete=models.SET_NULL,
        null=True,
        related_name="review"
    )
    rating = models.IntegerField(
        default=0
    )
    created_at = models.DateTimeField(
        auto_now_add=True
    )
