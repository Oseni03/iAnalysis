from django.contrib.auth import get_user_model
from django.contrib.auth.models import Group 
from django.db.models.signals import post_save
from django.dispatch import receiver
from django.conf import settings
from django.utils.text import slugify

from djstripe import models as djstripe_models

from .services import subscriptions

User = get_user_model()


@receiver(post_save, sender=User)
def create_free_plan_subscription(sender, instance, created, **kwargs):
    if created:
        if settings.SUBSCRIPTION_ENABLE:
            subscriptions.initialize_user(user=instance)


@receiver(post_save, sender=djstripe_models.Product)
def create_product_group(sender, instance, created, **kwargs):
    if created:
        Group.objects.create(name=slugify(instance.name))
        # group.permissions.set([permission_list])
        # group.permissions.add(permission, permission, ...)