from django import template

register = template.Library()  
  
@register.filter("split_char")
def split_char(value, ch):
    return value.split(ch)[-1]