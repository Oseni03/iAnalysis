import pytz
from django.conf import settings
from django.contrib import messages
from django.utils import timezone
from django.core import validators
from django.utils.translation import gettext as _
from djstripe import models as djstripe_models, enums as djstripe_enums
from django import forms
from django.core import exceptions

from . import models, utils
from .services import subscriptions, customers


class PaymentIntentForm(forms.ModelForm):
    """**IMPORTANT:** Update this serializer with real products and prices created in Stripe"""

    price = forms.ModelChoiceField(queryset=models.Price.objects.all(), empty_label=None)

    class Meta:
        model = djstripe_models.PaymentIntent
        fields = ('price',)

    def save(self, commit=True):
        price = self.cleaned_data["price"]
        
        payment_intent_response = djstripe_models.PaymentIntent._api_create(
            amount=price.unit_amount,
            currency="usd",
            payment_method_types=["card"],
            setup_future_usage="off_session",
        )
        return djstripe_models.PaymentIntent.sync_from_stripe_data(payment_intent_response)

    def update(self, instance: djstripe_models.PaymentIntent):
        price = self.cleaned_data["price"]
        payment_intent_response = instance._api_update(amount=price.unit_amount)
        return djstripe_models.PaymentIntent.sync_from_stripe_data(payment_intent_response)


class PaymentMethodForm(forms.ModelForm):
    card = forms.JSONField()
    
    class Meta:
        model = djstripe_models.PaymentMethod
        fields = ('type', 'card')


class ProductForm(forms.ModelForm):
    class Meta:
        model = models.Product
        fields = ('id', 'name')


class PriceForm(forms.ModelForm):
    product = ProductForm()

    class Meta:
        model = djstripe_models.Price
        fields = ('id', 'product', 'unit_amount')


class CancelUserActiveSubscriptionForm(forms.ModelForm):
    def clean(self):
        cleaned_data = super().clean()
        if subscriptions.is_current_schedule_phase_plan(schedule=self.instance, price_id=settings.SUBSCRIPTION_TRIAL_OR_FREE_PRODUCT_ID):
            raise forms.ValidationError(
                _('Customer has no paid subscription to cancel'), code='no_paid_subscription'
            )

        return cleaned_data

    def update(self, instance: djstripe_models.SubscriptionSchedule):
        free_plan_price = models.Price.objects.get(id=settings.SUBSCRIPTION_TRIAL_OR_FREE_PRODUCT_ID)
        current_phase = subscriptions.get_current_schedule_phase(schedule=instance)
        next_phase = {'items': [{'price': free_plan_price.id}]}

        if subscriptions.is_current_schedule_phase_trialing(schedule=instance):
            current_phase['end_date'] = current_phase['trial_end']

        return subscriptions.update_schedule(instance, phases=[current_phase, next_phase])

    class Meta:
        model = djstripe_models.SubscriptionSchedule
        fields = ()


class AdminStripePaymentIntentRefundForm(forms.Form):
    amount = forms.IntegerField(label="Amount (in cents)", min_value=100)
    reason = forms.ChoiceField(        choices=(
            ('duplicate', 'Duplicate'),
            ('fraudulent', 'Fraudulent'),
            ('requested_by_customer', 'Requested By Customer'),
        ),
    )

    class Meta:
        fields = (
            'amount',
            'reason',
        )

    def clean(self):
        cleaned_data = super().clean()
        amount = attrs['amount'] / 100
        try:
            charge = djstripe_models.Charge.objects.get(
                payment_intent=self.instance, status=djstripe_enums.ChargeStatus.succeeded
            )
        except djstripe_models.Charge.DoesNotExist:
            raise exceptions.ValidationError({'amount': _('Successful charge does not exist')})

        amount_to_refund = charge._calculate_refund_amount(amount=amount)
        if amount_to_refund <= 0:
            raise exceptions.ValidationError({'amount': _('Charge has already been fully refunded')})

        return {
            **cleaned_data,
            'amount': amount,
            'amount_to_refund': amount_to_refund,
            'charge': charge,
        }

    def update(self, instance: djstripe_models.PaymentIntent):
        cleaned_data = self.cleaned_data
        amount = cleaned_data['amount']
        reason = cleaned_data['reason']
        charge: djstripe_models.Charge = cleaned_data['charge']
        amount_to_refund = cleaned_data['amount_to_refund'] / 100

        charge.refund(amount=amount, reason=reason)
        messages.add_message(
            self.context['request'],
            messages.INFO,
            f'Successfully refunded {amount_to_refund} {charge.currency}',
        )

        return instance

