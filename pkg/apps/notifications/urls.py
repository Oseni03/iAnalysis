from django.urls import path

from . import views

app_name = "notifications"

urlpatterns = [
    path("", views.NotificationView.as_view(), name="all"),
    path("read-all/", views.MarkAllRead.as_view(), name="read_all"),
]