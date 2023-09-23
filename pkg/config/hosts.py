from django_hosts import patterns, host
from django.conf import settings

host_patterns = patterns(
    "",
    host(r"admin", "config.urls.admin", name="admin"),
    host(r"", settings.ROOT_URLCONF, name="main"),
)
