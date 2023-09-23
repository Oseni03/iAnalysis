from functools import wraps
from django.contrib import messages
from django.shortcuts import redirect
from django.http import HttpResponse
from django.conf import settings
from django.http import HttpResponseBadRequest

 
def subscription_test(user):
    if user.is_subscribed:
        return True
    return False


def subscribe_required(redirect_url="finances:pricing"):
    def decorator(view):
        @wraps(view)
        def _wrapped_view(request, *args, **kwargs):
            if not subscription_test(request.user):
                messages.info(request, "Active subscription required")
                return redirect(redirect_url)
            return view(request, *args, **kwargs)
        return _wrapped_view
    return decorator


def xhr_request_only(view_func):
    """
    this decorators ensures that the view func accepts only 
    XML HTTP Request i.e request done via fetch or ajax
    """
    @wraps(view_func)
    def wrapper(request, *args, **kwargs):
        if request.headers.get('x-requested-with') == 'XMLHttpRequest':
            return view_func(request, *args, **kwargs)
        print("Can't Process this Request")
        return HttpResponseBadRequest("Can't Process this Request")
    return wrapper