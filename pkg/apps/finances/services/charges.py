from django.contrib.auth import get_user_model

from djstripe.enums import RefundStatus

from djstripe.models import Refund, PaymentIntent, Customer, Subscription 

from ..models import Price

User = get_user_model()

def fail_charge_refund(refund: Refund, reason: str):
    refund.failure_reason = reason
    refund.status = RefundStatus.failed
    refund.save()


def set_paid_until(charge):
    intent = PaymentIntent.objects.get(id=charge.payment_intent)
    if intent.customer:
        customer = Customer.object.get(id=intent.customer) 
        if customer:
            subscr = Subscription.objects.get(id=customer.subscriptions.data[0].id)
            current_period_end = subscr.current_period_end
        try:
            user = User.objects.get(id=customer.subscriber)
        except:
            User.DoesNotExist()
            return False 
        user.set_paid_until(current_period_end)
    else:
        price = Price.objects.filter(unit_amount=intent.amount).first()
        if price.recurring.interval == "month":
            pass 
        elif price.recurring.interval == "year":
            pass