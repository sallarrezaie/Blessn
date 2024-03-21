from rest_framework import status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.viewsets import ModelViewSet
from rest_framework.permissions import IsAuthenticated

from .serializers import OrderSerializer
from .models import Order, Review

from payments.models import Payment

from django_filters.rest_framework import DjangoFilterBackend

from datetime import datetime

import stripe

from blessn.settings import STRIPE_LIVE_MODE, STRIPE_LIVE_SECRET_KEY, STRIPE_TEST_SECRET_KEY, CONNECTED_SECRET, BOOKING_FEE

if STRIPE_LIVE_MODE == True:
    stripe.api_key = STRIPE_LIVE_SECRET_KEY
else:
    stripe.api_key = STRIPE_TEST_SECRET_KEY


class OrderViewSet(ModelViewSet):
    serializer_class = OrderSerializer
    permission_classes = (IsAuthenticated,)
    queryset = Order.objects.all()
    filter_backends = (DjangoFilterBackend,)
    filterset_fields = ['consumer', 'contributor', 'status', 'archived']


    @action(detail=False, methods=['post'])
    def mark_as_delivered(self, request):
        order_id = request.data.get('order_id')
        order = Order.objects.get(id=order_id)
        order.status = 'Delivered'
        order.delivered_at = datetime.now()
        order.save()
        return Response(status=status.HTTP_200_OK)

    @action(detail=False, methods=['post'])
    def request_new_video(self, request):
        order_id = request.data.get('order_id')
        order = Order.objects.get(id=order_id)
        order.status = 'Redo Requested'
        order.redo_requested_at = datetime.now()
        order.save()
        return Response(status=status.HTTP_200_OK)

    @action(detail=False, methods=['post'])
    def mark_as_redone(self, request):
        order_id = request.data.get('order_id')
        order = Order.objects.get(id=order_id)
        order.status = 'Redone'
        order.redone_at = datetime.now()
        order.save()
        return Response(status=status.HTTP_200_OK)

    @action(detail=False, methods=['post'])
    def request_refund(self, request):
        order_id = request.data.get('order_id')
        order = Order.objects.get(id=order_id)
        order.status = 'Refund Requested'
        order.refund_requested_at = datetime.now()
        order.save()
        return Response(status=status.HTTP_200_OK)

    @action(detail=False, methods=['post'])
    def mark_as_refunded(self, request):
        order_id = request.data.get('order_id')
        order = Order.objects.get(id=order_id)

        payments = Payment.objects.filter(order=order)
        for payment in payments:
            payment_intent = payment.consumer_payment_intent.id
            stripe.Refund.create(
                payment_intent=payment_intent,
            )
            payment.refunded = True
            payment.save()

        order.refunded_at = datetime.now()
        order.status = 'Refunded'
        order.save()
        return Response(status=status.HTTP_200_OK)

    @action(detail=False, methods=['post'])
    def mark_as_archived(self, request):
        order_id = request.data.get('order_id')
        order = Order.objects.get(id=order_id)
        order.archived = True
        order.save()
        return Response(status=status.HTTP_200_OK)

    @action(detail=False, methods=['post'])
    def mark_as_flagged(self, request):
        flagged_reason = request.data.get('flagged_reason', '')
        order_id = request.data.get('order_id')
        order = Order.objects.get(id=order_id)
        order.status = 'Flagged'
        order.flagged = True
        order.flagged_reason = flagged_reason
        order.flagged_at = datetime.now()
        order.save()
        
        payments = Payment.objects.filter(order=order)
        for payment in payments:
            payment_intent = payment.consumer_payment_intent.id
            stripe.Refund.create(
                payment_intent=payment_intent,
            )
            payment.refunded = True
            payment.save()

        return Response(status=status.HTTP_200_OK)


    @action(detail=False, methods=['post'])
    def mark_as_unarchived(self, request):
        order_id = request.data.get('order_id')
        order = Order.objects.get(id=order_id)
        order.archived = False
        order.save()
        return Response(status=status.HTTP_200_OK)

    @action(detail=False, methods=['post'])
    def leave_a_review(self, request):
        order_id = request.data.get('order_id')
        order = Order.objects.get(id=order_id)
        rating = int(request.data.get('rating'))

        if rating < 1 or rating > 5:
            return Response("Rating must be between 1 and 5", status=status.HTTP_400_BAD_REQUEST)
        if Review.objects.filter(order_id=order_id).exists():
            return Response("Order has already been reviewed", status=status.HTTP_400_BAD_REQUEST)

        Review.objects.create(
            contributor=order.contributor,
            consumer=order.consumer,
            order=order,
            rating=rating
        )
        return Response(status=status.HTTP_200_OK)

    @action(detail=False, methods=['post'])
    def request_cancellation(self, request):
        order_id = request.data.get('order_id')
        order = Order.objects.get(id=order_id)
        order.status = 'Cancel Requested'
        order.cancel_requested_at = datetime.now()
        order.save()
        return Response(status=status.HTTP_200_OK)

    @action(detail=False, methods=['post'])
    def mark_as_cancelled(self, request):
        cancel_reason = request.data.get('cancel_reason', '')
        order_id = request.data.get('order_id')
        order = Order.objects.get(id=order_id)
        order.status = 'Cancelled'
        order.cancelled_at = datetime.now()
        order.cancel_reason = cancel_reason
        order.save()

        payments = Payment.objects.filter(order=order)
        for payment in payments:
            payment_intent = payment.consumer_payment_intent.id
            stripe.Refund.create(
                payment_intent=payment_intent,
            )
            payment.refunded = True
            payment.save()
        return Response(status=status.HTTP_200_OK)
