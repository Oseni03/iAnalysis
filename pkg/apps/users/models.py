import hashid_field
from django.contrib.auth.models import AbstractBaseUser, PermissionsMixin
from django.contrib.auth.models import BaseUserManager
from django.contrib.auth.models import Group
from django.db import models

from datetime import date

from common.acl.helpers import CommonGroups
from common.models import ImageWithThumbnailMixin
from common.storages import UniqueFilePathGenerator, PublicS3Boto3StorageWithCDN

# from . import notifications

from djstripe import models as djstripe_models


class UserManager(BaseUserManager):
    def get_queryset(self):
        return super().get_queryset().prefetch_related("notifications").all()
    
    def create_user(self, email, password=None):
        if not email:
            raise ValueError("Users must have an email address")

        user = self.model(
            email=self.normalize_email(email).lower(),
        )
        user.set_password(password)
        group_user, _ = Group.objects.get_or_create(name=CommonGroups.User)
        user.save(using=self._db)
        user.groups.add(group_user)
        UserProfile.objects.create(user=user)

        return user

    def create_superuser(self, email, password):
        user = self.create_user(
            email,
            password=password,
        )
        group_admin, _ = Group.objects.get_or_create(name=CommonGroups.Admin)
        user.is_superuser = True
        user.groups.add(group_admin)
        user.save(using=self._db)
        return user

    def filter_admins(self):
        return self.filter(groups__name=CommonGroups.Admin)


class User(AbstractBaseUser, PermissionsMixin):
    id = hashid_field.HashidAutoField(primary_key=True)
    created = models.DateTimeField(editable=False, auto_now_add=True)
    email = models.EmailField(
        verbose_name="email address",
        max_length=255,
        unique=True,
    )
    is_active = models.BooleanField(default=False)
    is_superuser = models.BooleanField(default=False)
    
    paid_until = models.DateField(null=True)
    
    otp_enabled = models.BooleanField(default=False)
    otp_verified = models.BooleanField(default=False)
    otp_base32 = models.CharField(max_length=255, blank=True, default='')
    otp_auth_url = models.CharField(max_length=255, blank=True, default='')

    objects = UserManager()

    USERNAME_FIELD = "email"

    def __str__(self) -> str:
        return self.email

    @property
    def is_staff(self):
        return self.is_superuser

    def has_group(self, name):
        return self.groups.filter(name=name).exists()
    
    @property
    def get_roles(self):
        from .services.users import get_role_names
        return get_role_names(self)
    
    @property
    def has_unread_notifications(self):
        from apps.notifications.services import NotificationService
        return NotificationService.user_has_unread_notifications(self)
    
    def set_paid_until(self, date_or_timestamp):
        if isinstance(date_or_timestamp, int):
            paid_until = date.fromtimestamp(date_or_timestamp)
        elif isinstance(date_or_timestamp, str):
            paid_until = date.fromtimestamp(int(date_or_timestamp))
        else:
            paid_until = date_or_timestamp
        
        self.paid_until = paid_until
        self.save()
    
    @property
    def customer(self):
        customer = djstripe_models.Customer.objects.filter(subscriber=self)
        if customer.exists():
            return customer.first()
        # customer.active_subscriptions
        # customer.subscriptions
        # customer.has_any_active_subscription()
        # customer.valid_subscriptions
        # customer.is_subscribed_to(product)
        return None
    
    @property
    def is_subscribed(self):
        return self.customer.has_any_active_subscription()


class UserAvatar(ImageWithThumbnailMixin, models.Model):
    original = models.ImageField(
        storage=PublicS3Boto3StorageWithCDN, upload_to=UniqueFilePathGenerator("avatars"), null=True
    )
    thumbnail = models.ImageField(
        storage=PublicS3Boto3StorageWithCDN, upload_to=UniqueFilePathGenerator("avatars/thumbnails"), null=True
    )

    THUMBNAIL_SIZE = (128, 128)
    ERROR_FIELD_NAME = "avatar"

    def __str__(self) -> str:
        return str(self.id)


class UserProfile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name="profile")
    first_name = models.CharField(max_length=40, blank=True, default='')
    last_name = models.CharField(max_length=40, blank=True, default='')
    avatar = models.OneToOneField(
        UserAvatar, 
        on_delete=models.SET_NULL, 
        null=True, blank=True, 
        related_name="user_profile"
    )

    def __str__(self) -> str:
        return f"{self.first_name} {self.last_name}"
    
    @property
    def email(self):
        """Get the profile user email
        
        This is needed by dj-stripe
        """
        return self.user.email