import functools
from django.shortcuts import redirect


def require_HTMX(view_func, redirect_url="dashboard:dashboard"):
    """
        this decorator ensures that the request is made by htmx,
        if not, the user will get redirected to 
        the url whose view name was passed to the redirect_url parameter
    """
    @functools.wraps(view_func)
    def wrapper(request, *args, **kwargs):
        if request.htmx:
            return view_func(request,*args, **kwargs)
        return redirect(redirect_url)
    return wrapper

