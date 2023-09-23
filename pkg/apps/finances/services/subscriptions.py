import pytz
from django.utils import timezone
from django.utils.translation import gettext as _
from djstripe import models as djstripe_models, enums as djstripe_enums, sync as djstripe_sync
from django.conf import settings

from ..exceptions import UserOrCustomerNotDefined, SubscriptionAndPriceDefinedTogether, SubscriptionOrPriceNotDefined


def initialize_user(user):
    """
    Primary purpose for separating this code into its own function is the ability to mock it during tests so we utilise
    a schedule created by factories instead of relying on stripe-mock response

    :param user:
    :return:
    """
    customer, _ = djstripe_models.Customer.get_or_create(user)
    if settings.SUBSCRIPTION_HAS_FREE_PLAN:
        price = models.Price.objects.get(id=settings.SUBSCRIPTION_FREE_PRICE_ID)
        create_schedule(customer=customer, price=price)
    elif settings.SUBSCRIPTION_HAS_TRIAL_PLAN:
        price = models.Price.objects.get(id=settings.SUBSCRIPTION_TRIAL_PRICE_ID)
        create_schedule(customer=customer, price=price)


def get_schedule(user=None, customer=None):
    if user:
        customer, _ = djstripe_models.Customer.get_or_create(user)
    if customer is None:
        raise UserOrCustomerNotDefined("Either user or customer must be defined")

    return customer.schedules.filter(status=djstripe_enums.SubscriptionScheduleStatus.active).first()


def create_schedule(
    subscription: djstripe_models.Subscription = None, price: djstripe_models.Price = None, user=None, customer=None
):
    if subscription and price:
        raise SubscriptionAndPriceDefinedTogether("Subscription and price can't be defined together")

    subscription_schedule_stripe_instance = None
    if price:
        if user:
            customer, _ = djstripe_models.Customer.get_or_create(user)
        if customer is None:
            raise UserOrCustomerNotDefined("Either user or customer must be defined")

        subscription_schedule_stripe_instance = djstripe_models.SubscriptionSchedule._api_create(
            customer=customer.id, 
            start_date='now', 
            end_behavior="release", 
            phases=[{'items': [{'price': price.id}]}]
        )

    if subscription:
        if isinstance(subscription, djstripe_models.StripeModel):
            subscription = subscription.id

        subscription_schedule_stripe_instance = djstripe_models.SubscriptionSchedule._api_create(
            from_subscription=subscription
        )

    if subscription_schedule_stripe_instance is None:
        raise SubscriptionOrPriceNotDefined("Either subscription or price must be defined")
    if user:
        djstripe_sync.sync_subscriber(user)
    else: 
        djstripe_sync.sync_subscriber(customer.subscriber)
    return djstripe_models.SubscriptionSchedule.sync_from_stripe_data(subscription_schedule_stripe_instance)


def update_schedule(instance: djstripe_models.SubscriptionSchedule, **kwargs):
    subscription_schedule_stripe_instance = instance._api_update(**kwargs)
    return djstripe_models.SubscriptionSchedule.sync_from_stripe_data(subscription_schedule_stripe_instance)


def get_valid_schedule_phases(schedule: djstripe_models.SubscriptionSchedule):
    return [
        phase
        for phase in schedule.phases
        if timezone.datetime.fromtimestamp(phase['end_date'], tz=pytz.UTC) > timezone.now()
    ]


def get_current_schedule_phase(schedule):
    phases = get_valid_schedule_phases(schedule)
    return phases[0]


def is_current_schedule_phase_plan(
    schedule: djstripe_models.SubscriptionSchedule, price_id
):
    current_phase = get_current_schedule_phase(schedule)
    current_price_id = current_phase['items'][0]['price']
    return current_price_id == price_id


def is_current_schedule_phase_trialing(schedule: djstripe_models.SubscriptionSchedule):
    current_phase = get_current_schedule_phase(schedule)
    if not current_phase['trial_end']:
        return False

    trial_end = timezone.datetime.fromtimestamp(current_phase['trial_end'], tz=pytz.UTC)
    return trial_end > timezone.now()


def cancel_active_subscription(user):
    instance = get_schedule(user=user)
    if not has_paid_subscription(user):
        raise _('Customer has no paid subscription to cancel')
    
    if settings.SUBSCRIPTION_HAS_FREE_PLAN:
        next_phase = {'items': [{'price': settings.SUBSCRIPTION_FREE_PRICE_ID}]}
    else:
        next_phase = {}
        
    current_phase = get_current_schedule_phase(schedule=instance)

    if is_current_schedule_phase_trialing(schedule=instance):
        current_phase['end_date'] = current_phase['trial_end']

    return update_schedule(instance, phases=[current_phase, next_phase])


def has_paid_subscription(user):
    instance = get_schedule(user=user)
    if is_current_schedule_phase_plan(schedule=instance, price_id=settings.SUBSCRIPTION_TRIAL_PRICE_ID) or is_current_schedule_phase_plan(schedule=instance, price_id=settings.SUBSCRIPTION_FREE_PRICE_ID):
        return False
    return True


def upgrade_active_subscription(user, price_id):
    instance = get_schedule(user=user)
    
    next_phase = {
        'items': [{'price': price_id}],
        "start_date": "now"
    }
    
    current_phase = get_current_schedule_phase(schedule=instance)
    current_phase["end_date"] = "now"
    
    return update_schedule(instance, phases=[current_phase, next_phase])


def downgrade_active_subscription(user, price_id):
    instance = get_schedule(user=user)
    
    next_phase = {
        'items': [{'price': price_id}],
    }
    
    current_phase = get_current_schedule_phase(schedule=instance)
    
    return update_schedule(instance, phases=[current_phase, next_phase])