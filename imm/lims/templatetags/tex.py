from django.template.defaultfilters import stringfilter
from django import template

register = template.Library()

@register.filter
@stringfilter
def texsafe(value):
    """ Returns a string with LaTeX special characters stripped/escaped out """
    for char in ['\\', '^', '~']: # these mess up things
        value = value.replace(char, '')
    for char in ['$','_', '{', '}']: # these can be escaped properly
        value = value.replace(char, '\\' + char)
    return value
    
