from django.utils import timezone

from rest_framework import status
from rest_framework.decorators import action
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.viewsets import ModelViewSet

from payments.models import Payment
from payments.serializers import PaymentSerializer

from orders.models import Order

from users.models import User

from contributors.models import Contributor

from dropdowns.models import Occasion

import stripe
import djstripe


from blessn.settings import STRIPE_LIVE_MODE, STRIPE_LIVE_SECRET_KEY, STRIPE_TEST_SECRET_KEY, CONNECTED_SECRET, BOOKING_FEE


if STRIPE_LIVE_MODE == True:
    stripe.api_key = STRIPE_LIVE_SECRET_KEY
else:
    stripe.api_key = STRIPE_TEST_SECRET_KEY


class PaymentViewSet(ModelViewSet):
    serializer_class = PaymentSerializer
    permission_classes = (IsAuthenticated,)
    queryset = Payment.objects.all()

    @action(detail=False, methods=['get'], permission_classes=[IsAuthenticated])
    def test_payment_method(self, request):
        payment_method = stripe.PaymentMethod.create(
        type="card",
        card={
            "number": "4000000000000077",
            "exp_month": 2,
            "exp_year": 2025,
            "cvc": "314",
        },
        )
        return Response(payment_method)


    @action(detail=False, methods=['post'], permission_classes=[IsAuthenticated])
    def place_an_order(self, request):
        payment_method = request.data.get('payment_method')
        consumer = request.user.consumer
        contributor = Contributor.objects.get(id=request.data.get('contributor_id'))

        turnaround_selected = request.data.get('turnaround_selected')
        if turnaround_selected == 'normal':
            video_fee = contributor.normal_delivery_price
            turnaround = "Normal"
        elif turnaround_selected == 'fast':
            video_fee = contributor.fast_delivery_price
            turnaround = "Fast"
        elif turnaround_selected =='same_day':
            video_fee = contributor.same_day_delivery_price
            turnaround = "Same Day"
        else:
            return Response({'detail': 'Invalid turnaround selected'}, status=status.HTTP_400_BAD_REQUEST)

        if request.data.get('occasion_id') is not None:
            occasion = Occasion.objects.get(id=request.data.get('occasion_id'))
        else:
            occasion = None

        booking_fee = video_fee * (BOOKING_FEE / 100)

        order = Order.objects.create(
            user=request.user,
            consumer=consumer,
            contributor=contributor,
            video_fee=video_fee,
            booking_fee=booking_fee,
            turnaround_selected=turnaround,
            video_for=request.data.get('video_for', ''),
            introduce_yourself=request.data.get('introduce_yourself', ''),
            video_to_say=request.data.get('video_to_say', ''),
            occasion=occasion
        )
        
        amount_to_charge = order.total

        if order.status != 'Pending':
            return Response({'detail': 'Order needs to be in Pending status'}, status=status.HTTP_400_BAD_REQUEST)

        try:
            # Get the Stripe Customer Infomration
            customers_data = stripe.Customer.list().data
            customer = None
            for customer_data in customers_data:
                if customer_data.email == request.user.email:
                    customer = customer_data
                    break
            if customer is None:
                customer = stripe.Customer.create(email=request.user.email)

            djstripe_customer = djstripe.models.Customer.sync_from_stripe_data(customer)
            payment_method = stripe.PaymentMethod.retrieve(payment_method)
            if payment_method.customer is None:
                if payment_method.customer != djstripe_customer.id:
                    payment_method = stripe.PaymentMethod.attach(payment_method, customer=customer)
                else:
                    return Response({"detail": "Payment method belongs to another cusomter"}, status=status.HTTP_400_BAD_REQUEST)
            dj_payment_method = djstripe.models.PaymentMethod.sync_from_stripe_data(payment_method)

        except Exception as e:
            return Response({"detail": str(e)}, status=status.HTTP_400_BAD_REQUEST)

        request.user.consumer.stripe_account = djstripe_customer
        request.user.consumer.stripe_account.save()

        # Create a PaymentIntent instead of Charge
        try:
            consumer_payment_intent = stripe.PaymentIntent.create(
                customer=request.user.consumer.stripe_account.id,
                payment_method=payment_method,
                amount=int(amount_to_charge * 100),
                currency='usd',
                description=f'Charge for Order {order.id}',
                confirm=True,
            )
        except Exception as e:
            return Response({"detail": str(e)}, status=status.HTTP_400_BAD_REQUEST)
        
        charge_id = consumer_payment_intent.charges.data[0].id
        # Sync with djstripe models
        dj_consumer_payment_intent = djstripe.models.PaymentIntent.sync_from_stripe_data(consumer_payment_intent)

        Payment.objects.create(
            order=order,
            consumer=request.user.consumer,
            amount=order.total,
            consumer_payment_intent=dj_consumer_payment_intent,
            payment_method=dj_payment_method,
            charge_id=charge_id
        )
        order.status = 'In Progress'
        order.paid_at = timezone.now()
        order.consumer_charge_id = charge_id
        order.save()

        request.user.consumer.save()
        
        return Response("Payment Successful", status=status.HTTP_201_CREATED)

    @action(detail=False, methods=['get'], permission_classes=[IsAuthenticated])
    def my_cards(self, request):
        profile = request.user.consumer
        if profile.stripe_account:
            customer_id = profile.stripe_account.id
        else:
            customers_data = stripe.Customer.list().data
            customer = None
            for customer_data in customers_data:
                if customer_data.email == request.user.email:
                    customer = customer_data
                    break
            if customer is None:
                customer = stripe.Customer.create(email=request.user.email)
            djstripe_customer = djstripe.models.Customer.sync_from_stripe_data(customer)
            profile.stripe_account = djstripe_customer
            profile.stripe_account.save()
            customer_id = djstripe_customer.id
        payment_methods = stripe.PaymentMethod.list(customer=customer_id, type='card')
        return Response(payment_methods)

    @action(detail=False, methods=['post'], permission_classes=[IsAuthenticated])
    def set_default(self, request):
        payment_method_id = request.data.get('payment_method', None)
        if payment_method_id is None:
            return Response({'detail': 'Missing Payment Method ID'}, status=status.HTTP_400_BAD_REQUEST)
        profile = request.user.consumer
        if profile.stripe_account:
            customer_id = profile.stripe_account.id
        else:
            customer_id = None
        if not customer_id:
            customers_data = stripe.Customer.list().data
            customer = None
            for customer_data in customers_data:
                if customer_data.email == request.user.email:
                    customer = customer_data
                    break
            if customer is None:
                customer = stripe.Customer.create(email=request.user.email)
            djstripe_customer = djstripe.models.Customer.sync_from_stripe_data(customer)
            profile.stripe_account = djstripe_customer
            profile.stripe_account.save()
            customer_id = djstripe_customer.id
        last_default_pms = stripe.PaymentMethod.list(customer=customer_id, type='card')
        for method in last_default_pms:
            if method.metadata:
                stripe.PaymentMethod.modify(
                    method.id,
                    metadata={"default": "False"}
                )
        payment_method = stripe.PaymentMethod.modify(
            payment_method_id,
            metadata={"default": "True"})
        djstripe.models.PaymentMethod.sync_from_stripe_data(payment_method)
        payment_methods = stripe.PaymentMethod.list(customer=customer_id, type='card')
        return Response(payment_methods)

    @action(detail=False, methods=['post'], permission_classes=[IsAuthenticated])
    def revoke_payment_method(self, request):
        payment_method_id = request.data.get('payment_method', None)
        if payment_method_id is None:
            return Response({'detail': 'Missing Payment Method ID'}, status=status.HTTP_400_BAD_REQUEST)
        profile = request.user.consumer
        if profile.stripe_account:
            customer_id = profile.stripe_account.id
        else:
            customer_id = None
        if not customer_id:
            customers_data = stripe.Customer.list().data
            customer = None
            for customer_data in customers_data:
                if customer_data.email == request.user.email:
                    customer = customer_data
                    break
            if customer is None:
                customer = stripe.Customer.create(email=request.user.email)
            djstripe_customer = djstripe.models.Customer.sync_from_stripe_data(customer)
            profile.stripe_account = djstripe_customer
            profile.stripe_account.save()
            customer_id = djstripe_customer.id
        payment_method = stripe.PaymentMethod.detach(payment_method_id)
        djstripe.models.PaymentMethod.sync_from_stripe_data(payment_method)
        payment_methods = stripe.PaymentMethod.list(customer=customer_id, type='card')
        return Response(payment_methods)

    @action(detail=False, methods=['post'], permission_classes=[IsAuthenticated])
    def add_payment_method(self, request):
        profile = request.user.consumer
        billing_details = request.data.get('billing_details')
        if profile.stripe_account:
            customer_id = profile.stripe_account.id
        else:
            customer_id = None
        if not customer_id:
            customers_data = stripe.Customer.list().data
            customer = None
            for customer_data in customers_data:
                if customer_data.email == request.user.email:
                    customer = customer_data
                    break
            if customer is None:
                customer = stripe.Customer.create(email=request.user.email)
            djstripe_customer = djstripe.models.Customer.sync_from_stripe_data(customer)
            profile.stripe_account = djstripe_customer
            profile.stripe_account.save()
            profile.save()
            customer_id = djstripe_customer.id
        payment_method_id = request.data.get('payment_method', None)
        if payment_method_id is None:
            return Response({'detail': 'Missing Payment Method ID'}, status=status.HTTP_400_BAD_REQUEST)
        payment_method = stripe.PaymentMethod.attach(payment_method_id, customer=customer_id)
        payment_method = stripe.PaymentMethod.modify(
            payment_method['id'],
            billing_details={
                "address": {
                    "city": billing_details["address"]["city"],
                    "country": billing_details["address"]["country"],
                    "line1": billing_details["address"]["line1"],
                    "postal_code": billing_details["address"]["postal_code"],
                    "state": billing_details["address"]["state"]
                },
                "name": billing_details["name"],
            }
        )
        stripe.Customer.modify(
            customer_id,
            invoice_settings={
                'default_payment_method': payment_method['id'],
            },
        )
        djstripe.models.PaymentMethod.sync_from_stripe_data(payment_method)
        payment_methods = stripe.PaymentMethod.list(customer=customer_id, type='card')
        return Response(payment_methods)

    # Check Business Account
    @action(detail=False, methods=['get'], permission_classes=[IsAuthenticated])
    def check(self, request):
        profile = request.user.contributor
        connect_account = profile.connect_account
        account = stripe.Account.retrieve(connect_account.id)
        djstripe_account = djstripe.models.Account.sync_from_stripe_data(account)
        profile.connect_account = djstripe_account
        profile.save()
        if profile.connect_account.payouts_enabled:
            return Response(status=status.HTTP_200_OK)
        return Response("Account payouts not enabled. Reattempt account creation to add additional details.", status=status.HTTP_400_BAD_REQUEST)

    # Business Account
    @action(detail=False, methods=['get'], permission_classes=[IsAuthenticated])
    def account(self, request):
        profile = request.user.contributor
        device = request.query_params.get('device', False)
        if profile.connect_account:
            account_id = profile.connect_account.id
            if device == "mobile":
                link = stripe.AccountLink.create(
                    account=account_id,
                    refresh_url="http://localhost:8080/reauth/",
                    return_url="http://localhost:8080/return/",
                    type="account_onboarding",
                )
                return Response({'link': link})

            else:
                link = stripe.AccountLink.create(
                    account=account_id,
                    refresh_url="https://fasterdrivers.com/restaurant/settings/stripe?reauth=true",
                    return_url="https://fasterdrivers.com/restaurant/settings/stripe?return=true",
                    type="account_onboarding",
                )
                return Response({'link': link})

        business_name = 'Fast Drivers'
        account = stripe.Account.create(
            country="US",
            type="express",
            capabilities={
                "transfers": {"requested": True},
            },
            business_type="individual",
            business_profile={"name": business_name},
        )
        djstripe_account = djstripe.models.Account.sync_from_stripe_data(account)
        profile.connect_account = djstripe_account
        profile.save()
        link = stripe.AccountLink.create(
            account=account['id'],
            refresh_url="http://localhost:8080/reauth/",
            return_url="http://localhost:8080/return/",
            type="account_onboarding",
        )
        return Response({'link': link})

    @action(detail=False, methods=['POST'])
    def connected(self, request):
        event = None
        payload = request.body
        sig_header = request.META['HTTP_STRIPE_SIGNATURE']

        try:
            event = stripe.Webhook.construct_event(
                payload, sig_header, CONNECTED_SECRET
            )
        except ValueError as e:
            # Invalid payload
            raise e
        except stripe.error.SignatureVerificationError as e:
            # Invalid signature
            raise e

        # Handle the event
        if event.type == 'account.updated':
            data = event.data.get("object", {})
            payouts_enabled = data.get('payouts_enabled')
            account_id = data.get('id')

            user = User.objects.get(
                consumer__connect_account__id=account_id
            )
            profile = user.consumer

            # Conditional can be removed if we are just updating the account info
            if payouts_enabled == True:
                account = stripe.Account.retrieve(account_id)
                djstripe_account = djstripe.models.Account.sync_from_stripe_data(account)
                profile.connect_account = djstripe_account
                profile.save()
            else:
                # Change if any flags are required
                account = stripe.Account.retrieve(account_id)
                djstripe_account = djstripe.models.Account.sync_from_stripe_data(account)
                profile.connect_account = djstripe_account
                profile.save()
        return Response(status=status.HTTP_200_OK)
