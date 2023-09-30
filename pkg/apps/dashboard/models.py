from django.db import models
from django.conf import settings
from django.urls import reverse
from django.utils.translation import gettext_lazy as _

import hashid_field

# Create your models here.
class DataQuerySet(models.QuerySet):
    def database(self):
        return self.filter(is_db=True)
    
    def api(self):
        return self.filter(is_api=True)


class DataManager(models.Manager):
    def get_queryset(self):
        return DataQuerySet(self.model, using=self._db)
    
    def database(self):
        return self.get_queryset().database()
    
    def api(self):
        return self.get_queryset().api()


class Data(models.Model):
    class ProtocolType(models.TextChoices):
        POSTGRESQL = "postgresql+psycopg2", _("PostgreSQL") # redshift/aurora postgresql
        MYSQL = "mysql+pymysql", _("MySQL") # or mysql+auroradataapi
        # MYSQL = "mysql+mysqlconnector", _("MySQL")
        ORACLE = "oracle+cx_oracle", _("Oracle")
        MS_SERVER= "mssql+pyodbc", _("Microsoft SQL Server")
        REDSHIFT = "redshift+redshift_connector", _("Redshift")
        ELASTIC_SEARCH= "https", _("Elastic search")
        SNOWFLAKE= "snowflake", _("Amazon Snowflake")
        
    id = hashid_field.HashidAutoField(primary_key=True)
    user = models.ForeignKey(settings.AUTH_USER_MODEL, related_name="databases", on_delete=models.CASCADE)
    title = models.CharField(max_length=255)
    protocol = models.CharField(max_length=255, choices=ProtocolType.choices, null=True)
    host = models.CharField(max_length=255, null=True)
    port = models.CharField(max_length=255, null=True) 
    db_name = models.CharField(max_length=255, null=True) 
    tables = models.CharField(max_length=255, null=True)
    snowflake_account = models.CharField(max_length=255, null=True, help_text=_("Snowflake database account"))
    snowflake_schema = models.CharField(max_length=255, null=True, help_text=_("Snowflake database schema"))
    snowflake_warehouse = models.CharField(max_length=255, null=True, help_text=_("Snowflake database warehouse"))
    schema = models.TextField(null=True)
    spec_url = models.URLField(null=True, help_text=_("Openapi spec url"))
    header = models.JSONField(null=True, help_text=_("A dict of API request header"))
    created_at = models.DateTimeField(auto_now=True)
    updated_at = models.DateTimeField(auto_now_add=True)
    
    is_db = models.BooleanField(default=False)
    is_api = models.BooleanField(default=False)
    
    objects = DataManager()
    
    def __str__(self):
        return str(self.db_name)
    
    def get_absolute_url(self):
        return reverse("dashboard:data_chat", args=(self.id,))
    
    @property
    def tbls(self):
        tables = self.tables.split(",")
        tables = [tbl.strip() for tbl in tables]
        return tables
    
    def conn_str(self, username, password):
        if self.protocol == self.ProtocolType.SNOWFLAKE:
            return f"snowflake://{username}:{password}@{self.snowflake_account}/{self.db_name}/{self.snowflake_schema}?warehouse={self.snowflake_warehouse}"
        elif self.protocol == self.ProtocolType.ELASTIC_SEARCH:
            return f"{self.protocol}://{username}:{password}@{self.host}:{self.port}"
        return f"{self.protocol}://{username}:{password}@{self.host}:{self.port}/{self.db_name}"
        
    @property
    def jdbc_uri(self):
        return f"jdbc:{self.protocol}://{self.host}:{self.port}/{self.db_name}"


class Message(models.Model):
    id = hashid_field.HashidAutoField(primary_key=True)
    source = models.ForeignKey(Data, related_name="messages", on_delete=models.CASCADE)
    text = models.CharField(max_length=255)
    is_ai = models.BooleanField(default=False)
    sql_query = models.CharField(null=True, max_length=255)