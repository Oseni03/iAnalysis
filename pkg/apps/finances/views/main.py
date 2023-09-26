from django.conf import settings
from django.urls import reverse
from django.shortcuts import render, redirect, get_object_or_404
from django.http import JsonResponse
from django.contrib.auth.decorators import login_required
from django.contrib.auth.mixins import LoginRequiredMixin
from django.views.generic import View
from django.views.generic import TemplateView
from django.utils.decorators import method_decorator
from djstripe import models as djstripe_models

from ..services import customers, subscriptions 
from .. import models, forms
from ..decorators import subscribe_required, xhr_request_only

class PricingView(TemplateView):
    template_name = "finances/pricing.html"
    
    def get_context_data(self, *args, **kwargs):
        context = super().get_context_data(*args, **kwargs)
        prices = models.Price.objects.prefetch_related("product").all()
        context["monthly"] = prices.filter(recurring__interval="month").distinct()
        context["yearly"] = prices.filter(recurring__interval="year")
        return context 


@method_decorator(xhr_request_only, name="dispatch")
class PricingPayment(LoginRequiredMixin, View):
    
    def get(self, request, price_id, *args, **kwargs):
        price = get_object_or_404(djstripe_models.Price, id=price_id)
        intent = customers.setup_intent(request.user)
        
        context = {
            "price": price,
            "clientSecret": intent.client_secret
        }
        context["STRIPE_PUBLISHABLE_KEY"] = settings.STRIPE_PUBLISHABLE_KEY
        context["redirect_url"] = reverse("finances:profile_subscription")
        return render(request, "finances/subscription_payment.html", context)
    
    def post(self, request, price_id=None, *args, **kwargs):
        data = json.loads(request.data)
        payment_method_id = data.get("payment_method_id")
        (customer, _) = djstripe_models.Customer.get_or_create(request.user)
        customers.set_default_payment_method(request.user, payment_method_id)
        
        if subscriptions.has_paid_subscription(request.user):
            print("Subscription upgrade")
        
        try:
            sub = djstripe_models.Subscription._api_create(
                price=price_id,
                payment_behavior='default_incomplete',
                payment_settings={'save_default_payment_method': 'on_subscription'},
                expand=['latest_invoice.payment_intent', 'pending_setup_intent'],
            )
            subscription = djstripe_models.Subscription.sync_from_stripe_data(sub)
            
            subscriptions.create_schedule(subscription=subscription, customer=customer)
            
            if subscription.pending_setup_intent is not None:
                return JsonResponse({
                    "type": 'setup', 
                    "clientSecret": subscription.pending_setup_intent.client_secret
                })
            else:
                return JsonResponse({
                    "type": 'payment', 
                    "clientSecret": subscription.latest_invoice.payment_intent.client_secret
                })
        except Exception as e:
            return JsonResponse({"error": {'message': e.user_message}}, status=400)


# @method_decorator(subscribe_required, name="dispatch")
class SubscriptionPage(LoginRequiredMixin, TemplateView):
    template_name = "finances/profile_subscription.html"


@method_decorator(subscribe_required, name="dispatch")
class CancelSubscription(LoginRequiredMixin, View):
    def get(self, request, *args, **kwargs):
        subscriptions.cancel_active_subscription(request.user)
        return redirect("users:profile")