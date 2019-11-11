from django.template import Library

register = Library()


@register.inclusion_tag('users/components/icon-info.html')
def show_icon(label='', icon='', badge=None, color='', tooltip=''):
    return {
        'label': label,
        'icon': icon,
        'badge': badge,
        'color': color,
        'tooltip': tooltip
    }