# Time_Manager/templatetags/custom_filters.py

from django import template

register = template.Library()

@register.filter(name='replace_spaces')
def replace_spaces(value):
    return value.lower().replace(' ', '-')
