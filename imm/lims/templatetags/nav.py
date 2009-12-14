from django.template import Library

register = Library()

@register.simple_tag
def active(request, pattern):
    """
    Used to mark links as active in a navigation list if the ``request.path``
    matches the given regular expression. Returns ``"active"`` or ``""``.
    
    Usage::
    
        {% active request [regexp] %}
    
    Example::
    
        {% active request "^/project/experiment/" %}
    """
    import re
    if re.search(pattern, request.path):
        return 'active'
    return ''

