from django import forms

from . import models


class UpdateNotificationForm(forms.ModelForm):
    
    def update(self, instance: models.Notification):
        is_read = cleaned_data["is_read"]
        if is_read != instance.is_read:
            instance.is_read = is_read
            instance.save(update_fields=["read_at"])
        return instance

    class Meta:
        model = models.Notification
        fields = ("id", "is_read")
