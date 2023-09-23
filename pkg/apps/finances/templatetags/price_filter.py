from django import template

register = template.Library()

@register.filter(name="dollar")
def dollar(value):
    return int(str(value).replace("00", ""))