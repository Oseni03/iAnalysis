from django.urls import path, include

from .. import views

app_name = "finances"

stripe_urls = [
    path("", include("djstripe.urls", namespace="djstripe")),
]

urlpatterns = [
    path("stripe/", include(stripe_urls)),
    path("pricing/", views.PricingView.as_view(), name="pricing"),
    path("pricing/<price_id>/payment/", views.PricingPayment.as_view(), name="pricing_payment"),
    path("subscription/", views.SubscriptionPage.as_view(), name="profile_subscription"),
    path("subscription/cancel", views.CancelSubscription.as_view(), name="cancel_subscription"),
]
