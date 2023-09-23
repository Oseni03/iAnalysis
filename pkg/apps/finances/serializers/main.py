from django.contrib import messages
from django.utils.translation import gettext as _
from djstripe import models as djstripe_models, enums as djstripe_enums
from rest_framework import serializers, exceptions


class AdminStripePaymentIntentRefundSerializer(serializers.Serializer):
    amount = serializers.IntegerField(write_only=True, label="Amount (in cents)", min_value=100)
    reason = serializers.ChoiceField(
        write_only=True,
        choices=(
            ('duplicate', 'Duplicate'),
            ('fraudulent', 'Fraudulent'),
            ('requested_by_customer', 'Requested By Customer'),
        ),
    )

    class Meta:
        fields = (
            'amount',
            'refund',
        )

    def validate(self, attrs):
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
            **attrs,
            'amount': amount,
            'amount_to_refund': amount_to_refund,
            'charge': charge,
        }

    def update(self, instance: djstripe_models.PaymentIntent, validated_data):
        amount = validated_data['amount']
        reason = validated_data['reason']
        charge: djstripe_models.Charge = validated_data['charge']
        amount_to_refund = validated_data['amount_to_refund'] / 100

        charge.refund(amount=amount, reason=reason)
        messages.add_message(
            self.context['request'],
            messages.INFO,
            f'Successfully refunded {amount_to_refund} {charge.currency}',
        )

        return instance

