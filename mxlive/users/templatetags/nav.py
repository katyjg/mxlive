from django.template import Library
import re

register = Library()

@register.simple_tag
def active(request_path, pattern):
    """
    Used to mark links as active in a navigation list if the ``request.path``
    matches the given regular expression. Returns ``"active"`` or ``""``.
    
    Usage::
    
        {% active request.path [regexp] %}
    
    Example::
    
        {% active request.path "^/users/experiment/" %}
    """
    if re.search(pattern, request_path):
        return 'active'
    return ''

@register.simple_tag
def active_exact(request_path, path):
    """
    Used to mark links as active in a navigation list if the ``request.path``
    matches the given path. Returns ``"active"`` or ``""``.
    
    Usage::
    
        {% active_exact request.path [regexp] %}
    
    Example::
    
        {% active_exact request.path "^/users/experiment/" %}
    """
    if request_path == path:
        return 'active'
    return ''

