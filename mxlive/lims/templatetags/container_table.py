from django.template import Library

register = Library()

@register.inclusion_tag('users/entries/container_table.html', takes_context=True)
def container_table(context, obj, admin):
    return { 'object': obj,
            'admin': admin
            }
