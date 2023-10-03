from django.shortcuts import render


def handler_400(request, exception):
    referer_url = request.META.get("HTTP_REFERER")
    context = {
        "exception": exception,
        "referer_url": referer_url
    }
    return render(request, "handler/400.html", context)


def handler_403(request, exception):
    referer_url = request.META.get("HTTP_REFERER")
    context = {
        "exception": exception,
        "referer_url": referer_url
    }
    return render(request, "handler/403.html", context)


def handler_404(request, exception):
    referer_url = request.META.get("HTTP_REFERER")
    context = {
        "exception": exception,
        "referer_url": referer_url
    }
    return render(request, "handler/404.html", context)


def handler_500(request):
    referer_url = request.META.get("HTTP_REFERER")
    context = {"referer_url": referer_url}
    return render(request, "handler/500.html", context)