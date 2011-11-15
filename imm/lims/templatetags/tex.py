from django.template.defaultfilters import stringfilter
from django import template
import sys

register = template.Library()

@register.filter
@stringfilter
def texsafe(value):
    """ Returns a string with LaTeX special characters stripped/escaped out """
    special = [
    [ "\\xc5", 'A'],       #'\\AA'
    [ "\\xf6", 'o']        #'\\"{o}'
    ]
    for char in ['\\', '^', '~', '%']: # these mess up things
        value = value.replace(char, '')
    for char in ['$','_', '{', '}']: # these can be escaped properly
        value = value.replace(char, '\\' + char)
    for char, new_char in special:
        value = eval(repr(value).replace(char, new_char))
    return value


