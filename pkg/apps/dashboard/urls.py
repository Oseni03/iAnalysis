from django.urls import path

from . import views

app_name = "dashboard"

urlpatterns = [
    path("", views.DashboardView.as_view(), name="dashboard"),
    path("new/<slug:data_type>/", views.AddDataView.as_view(), name="data_add"),
    path("<str:pk>/", views.chat, name="data_chat"),
]