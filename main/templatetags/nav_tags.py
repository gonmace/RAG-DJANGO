from django import template
from django.urls import resolve

register = template.Library()

@register.simple_tag(takes_context=True)
def is_active(context, url_name):
    request = context['request']
    current_url = resolve(request.path_info).url_name
    return 'menu-active' if current_url == url_name else '' 