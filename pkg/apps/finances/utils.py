from django.conf import settings
from django.contrib.auth.models import Group 
from django.utils.text import slugify

from djstripe import models as djstripe_models


def customer_can_activate_trial(customer: djstripe_models.Customer):
    return not customer.subscriptions.filter(trial_end__isnull=False).exists()


def get_product(subscription: djstripe_models.Subscription):
    if subscription.plan:
        product = djstripe_models.Product.objects.get(id=subscription.plan.product)
    else:
        product = djstripe_models.Product.objects.get(id=subscription.price.product)
    return product


def remove_subscriber_from_group(subscriber: settings.AUTH_USER_MODEL, subscription: djstripe_models.Subscription):
    
    product = get_product(subscription)
    
    group = Group.objects.get(name=slugify(product.name))
    subscriber.groups.remove(group)


def add_subscriber_to_group(subscriber: settings.AUTH_USER_MODEL, subscription: djstripe_models.Subscription):
    
    product = get_product(subscription)
    
    group = Group.objects.get(name=slugify(product.name))
    subscriber.groups.add(group)