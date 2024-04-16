from django.db import models
from djstripe.models import PaymentMethod, PaymentIntent

from orders.models import Order
from consumers.models import Consumer



class Payment(models.Model):
    """
    A model to represent the Order Payments
    """
    order = models.ForeignKey(
        Order,
        on_delete=models.CASCADE,
        null=True,
        related_name='payments'
    )
    consumer = models.ForeignKey(
        Consumer,
        on_delete=models.CASCADE,
        null=True,
        related_name='payments'
    )
    amount = models.DecimalField(
        max_digits=8,
        decimal_places=2
    )
    consumer_payment_intent = models.ForeignKey(
        PaymentIntent,
        on_delete=models.SET_NULL,
        related_name='payments',
        null=True
    )
    payment_method = models.ForeignKey(
        PaymentMethod,
        on_delete=models.SET_NULL,
        related_name='payments',
        null=True
    )
    charge_id = models.CharField(
        max_length=255,
        blank=True,
        null=True
    )
    created_at = models.DateTimeField(
        auto_now_add=True
    )
    refunded = models.BooleanField(
        default=False
    )


class BookingFee(models.Model):
    """
    A model to represent the Booking Fees
    """
    fee = models.DecimalField(
        max_digits=8,
        decimal_places=2
    )
