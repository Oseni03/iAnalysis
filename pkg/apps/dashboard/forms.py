from django import forms 
from django.core import exceptions
from django.utils.translation import gettext as _

from .models import Data 
# from .utils import get_schema, generate_identifier
# from .services import secrets


class CredentialsForm(forms.Form):
    username = forms.CharField(required=True)
    password = forms.CharField(required=True, widget=forms.PasswordInput())


class DatabaseForm(forms.ModelForm, CredentialsForm):
    protocol = forms.ChoiceField(label=_("Choose database type"), choices= Data.ProtocolType.choices)
    db_name = forms.CharField(label=_("Database name"))
    tables = forms.CharField(label=_("Tables (optional)"), help_text=_("Coma (,) seperated names"))
    
    class Meta:
        model = Data 
        fields = ("title",
            "protocol", "host", "port", 
            "db_name", "tables", "snowflake_account", 
            "snowflake_schema", "snowflake_warehouse"
        )
        
    def save(self, user, commit=True):
        data = Data.objects.create(**self.cleaned_data)
        data.user = user
        data.is_db = True
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


class APIForm(forms.ModelForm):
    spec_url = forms.URLField(label="Spec url")
    
    class Meta:
        model = Data 
        fields = ("title", "spec_url", "header")
        
    def save(self, user, commit=True):
        data = Data.objects.create(**self.cleaned_data)
        data.user = user
        data.is_api = True
        
        # Might have to save the header dict into aws secret manager 
        
        if commit:
            data.save()
        return data


class ChatForm(forms.Form):
    model = forms.ChoiceField(
        widget=forms.RadioSelect(attrs={
            "class": "btn-check",
            "autocomplete": "off"
        }), 
        choices=[("gpt-3", _("GPT3")), ("gpt-4", _("GPT4"))],
        initial="gpt-3"
    )
    message = forms.CharField(help_text=_("Natural language query"))