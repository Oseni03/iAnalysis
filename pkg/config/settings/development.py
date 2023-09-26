from .base import *


if DEVELOPMENT_MODE is True:
    DATABASES = {
        'default': {
            'ENGINE': 'django.db.backends.sqlite3',
            'NAME': BASE_DIR / 'db.sqlite3',
        }
    }
    
    EMAIL_BACKEND = "django.core.mail.backends.console.EmailBackend"
    
    STATIC_URL = 'static/'
    # STATIC_ROOT = BASE_DIR / "static"
    MEDIA_URL = "media/"
    MEDIA_ROOT = BASE_DIR / "media"
    STATICFILES_DIRS = [
        BASE_DIR / "static",
        BASE_DIR / "media",
    ]
    
    
    CHANNEL_LAYERS = {
        "default": {"BACKEND": "channels.layers.InMemoryChannelLayer"},
    }
    
    # INTERNAL_IPS = ("127.0.0.1",)
    # MIDDLEWARE += ("debug_toolbar.middleware.DebugToolbarMiddleware",)

    # INSTALLED_APPS += ("debug_toolbar",)

    # DEBUG_TOOLBAR_PANELS = [
    #     "debug_toolbar.panels.versions.VersionsPanel",
    #     "debug_toolbar.panels.timer.TimerPanel",
    #     "debug_toolbar.panels.settings.SettingsPanel",
    #     "debug_toolbar.panels.headers.HeadersPanel",
    #     "debug_toolbar.panels.request.RequestPanel",
    #     "debug_toolbar.panels.sql.SQLPanel",
    #     "debug_toolbar.panels.staticfiles.StaticFilesPanel",
    #     "debug_toolbar.panels.templates.TemplatesPanel",
    #     "debug_toolbar.panels.cache.CachePanel",
    #     "debug_toolbar.panels.signals.SignalsPanel",
    #     "debug_toolbar.panels.logging.LoggingPanel",
    #     "debug_toolbar.panels.redirects.RedirectsPanel",
    # ]

    # DEBUG_TOOLBAR_CONFIG = {
    #     "INTERCEPT_REDIRECTS": False,
    # }
else:
    if len(sys.argv) > 0 and sys.argv[1] != "collectstatic":
        if env("DATABASE_URL", default="") is None:
            raise Exception("DATABASE_URL environment not defined")
        DATABASES = {
            "default": dj_database_url.parse(env("DATABASE_URL"))
        }
    
    EMAIL_BACKEND = "django_ses.SESBackend"
    
    AWS_S3_ACCESS_KEY_ID = env("AWS_S3_ACCESS_KEY_ID")
    AWS_S3_SECRET_ACCESS_KEY = env("AWS_S3_SECRET_ACCESS_KEY")
    AWS_STORAGE_BUCKET_NAME = env("AWS_STORAGE_BUCKET_NAME")
    AWS_S3_REGION_NAME = env("AWS_S3_REGION_NAME")
    AWS_S3_ENDPOINT_URL = f"https://${AWS_S3_REGION_NAME}.digitaloceanspaces.com"
    AWS_S3_OBJECT_PARAMETERS = {
        "CacheControl": "max-age=86400",
    }
    AWS_DEFAULT_ACL = "public-read"
    AWS_LOCATION = "static"
    AWS_MEDIA_LOCATION = "media"
    AWS_S3_CUSTOM_DOMAIN = env("AWS_S3_CUSTOM_DOMAIN", default=None)
    STORAGES = {
        "default": {"BACKEND": "custom_storages.CustomS3Boto3Storage"},
        "staticfiles": {"BACKEND": "storages.backends.s3boto3.S3StaticStorage"},
    }
    
    AWS_QUERYSTRING_EXPIRE = env("AWS_QUERYSTRING_EXPIRE", default=60 * 60 * 24)
    AWS_CLOUDFRONT_KEY = os.environ.get('AWS_CLOUDFRONT_KEY', '').encode('ascii')
    AWS_CLOUDFRONT_KEY_ID = os.environ.get('AWS_CLOUDFRONT_KEY_ID', None)
    
    
    # REDIS setup
    
    CHANNEL_LAYERS = {
        "default": {
            "BACKEND": "channels_redis.core.RedisChannelLayer",
            "CONFIG": {
                "hosts": [REDIS_URL],
            },
        },
    }

