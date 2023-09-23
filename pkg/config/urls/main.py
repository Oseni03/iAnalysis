from django.contrib import admin
from django.urls import path, include
from django.conf import settings

import debug_toolbar

urlpatterns = [
    path('finances/', include('apps.finances.urls.main', namespace="finances")),
    path('users/', include('apps.users.urls', namespace="users")),
    path('notifications/', include('apps.notifications.urls', namespace="notifications")),
    path('accounts/', include('allauth.urls')),
]

if settings.DEVELOPMENT_MODE is True:
    urlpatterns.append(
        path("__debug__", include(debug_toolbar.urls))
    )