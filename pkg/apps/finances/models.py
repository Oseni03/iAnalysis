from djstripe import models as djstripe_models
from django.urls import reverse

from . import managers


class Product(djstripe_models.Product):
    class Meta:
        proxy = True

    objects = managers.ProductManager()
    
    @property
    def features(self):
        return self.metadata.features


class Price(djstripe_models.Price):
    class Meta:
        proxy = True
    
    def get_absolute_url(self):
        return reverse("finances:pricing_payment", kwargs={"price_id": self.id,})
