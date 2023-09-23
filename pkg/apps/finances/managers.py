from django.db import models
from djstripe.settings import djstripe_settings
from djstripe import enums as djstripe_enums


class ProductManager(models.Manager):

    def create(self, idempotency_key=None, stripe_account=None, **kwargs):
        metadata = {}

        stripe_product = self.model._api_create(
            **kwargs,
            idempotency_key=idempotency_key,
            metadata=metadata,
            stripe_account=stripe_account,
        )

        return self.model.sync_from_stripe_data(stripe_product)
