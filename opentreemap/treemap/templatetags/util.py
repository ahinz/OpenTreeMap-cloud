from django import template
from django.core.files.storage import default_storage


register = template.Library()


register.filter('get', lambda a, b: a[b])
