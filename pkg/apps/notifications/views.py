from django.shortcuts import redirect
from django.contrib.auth.mixins import LoginRequiredMixin
from django.views.generic import ListView, View

from . import models, services

class NotificationView(LoginRequiredMixin, ListView):
    template_name = 'notifications/notification.html'
    context_object_name = "notifications"
    model = models.Notification
    paginate_by = 15
    
    def get_queryset(self):
        return models.Notification.objects.filter(user=self.request.user)


class MarkAllRead(View):
    def get(self, request, *args, **kwargs):
        services.NotificationService.mark_read_all_user_notifications(request.user)
        return redirect(request.META.get("HTTP_REFERER"))