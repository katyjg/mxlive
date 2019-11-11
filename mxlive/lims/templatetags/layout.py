from django import template

register = template.Library()

@register.simple_tag
def container_col(container):
    height = container.kind.layout.get('height', 1.0)
    envelope = container.kind.envelope
    if envelope == 'circle' or height >= 0.75:
        return 'col-3'
    else:
        return 'col-6'