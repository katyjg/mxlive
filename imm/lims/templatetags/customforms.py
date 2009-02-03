from django.template import Library

register = Library()

@register.inclusion_tag('forms/form.html')
def show_form(form, info):
    return {
        'form': form, 
        'action': info.get('action',''), 
        'target': info.get('target',''),
        'add_another': info.get('add_another', False)
        }

@register.inclusion_tag('forms/plain_form.html')
def show_plain_form(form):
    return {
        'form': form, 
        }

