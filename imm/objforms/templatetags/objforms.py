from django.template import Library

register = Library()

@register.inclusion_tag('objforms/form.html')
def show_form(form, info):
    """
    Render a Custom Form with action and target
    """
    return {
        'form': form, 
        'action': info.get('action',''), 
        'target': info.get('target',''),
        'add_another': info.get('add_another', False)
        }

@register.inclusion_tag('objforms/plain.html')
def show_plain_form(form):
    """ 
    Render a plain Form 
    """
    return {
        'form': form, 
        }

