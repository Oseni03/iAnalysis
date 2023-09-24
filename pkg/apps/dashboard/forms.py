from django import forms 
from django.core import exceptions
from django.utils.translation import gettext as _

from .models import Database 
# from .utils import get_schema, generate_identifier
# from .services import secrets


class CredentialsForm(forms.Form):
    username = forms.CharField(required=True)
    password = forms.CharField(required=True, widget=forms.PasswordInput())


class DatabaseForm(forms.ModelForm, CredentialsForm):
    # protocol = models.CharField(widget=forms.HiddenInput())
    
    class Meta:
        model = Database 
        fields = (
            "protocol", "host", "port", 
            "db_name", "tables", "snowflake_account", 
            "snowflake_schema", "snowflake_warehouse"
        )
        
    def save(self, user, commit=True):
        data = Database.objects.create(**self.cleaned_data)
        data.user = user
        try:
            conn_str = data.conn_str(
                self.cleaned_data["username"], 
                self.cleaned_data["password"]
            )
            schema = get_schema(conn_str)
        except exception as e:
            raise exceptions.ValidationError({"credential": _(e)})
        data.schema = schema 
            
        identifier = generate_identifier(user, data)
        secrets.create_secret(
            identifier, 
            self.cleaned_data.get("username"), 
            self.cleaned_data.get("password")
        )
        
        if commit:
            data.save()
        return data


class ChatForm(forms.Form):
    model = forms.ChoiceField(widget=forms.RadioSelect, choices=[("gpt-3", _("GPT3")), ("gpt-4", _("GPT4"))])
    message = forms.CharField()