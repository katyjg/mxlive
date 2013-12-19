from mxlive.settings import VERSION

from django import template  
register = template.Library()  
 
@register.filter("get_version")  
def get_version(val=None):
    return VERSION
    

