
from django import template
from django.utils.safestring import mark_safe
import yaml
from pygments import highlight
from pygments.lexers import YamlLexer, PythonLexer
from pygments.formatters import HtmlFormatter

register = template.Library()


@register.filter
def entry_html(entry):
    data = {
        'Type': entry.get_kind_display(),
        'Data Source': f"{entry.source}",
        'Attributes': entry.attrs
    }
    if entry.kind == entry.Types.TEXT:
        flow_style = False
        style = None
    else:
        flow_style = None
        style = None

    yaml_data = yaml.dump(data, default_style=style, default_flow_style=flow_style, sort_keys=False)
    formatter = HtmlFormatter(nobackground=True)
    highlighted_data = highlight(yaml_data, YamlLexer(), formatter)
    return mark_safe(highlighted_data)


@register.filter
def yaml_html(data):
    yaml_data = yaml.dump(data, default_flow_style=None, sort_keys=False)
    formatter = HtmlFormatter(nobackground=True)
    highlighted_data = highlight(yaml_data, YamlLexer(), formatter)
    return mark_safe(highlighted_data)


@register.filter
def expression_html(text):
    formatter = HtmlFormatter(nobackground=True)
    highlighted_data = highlight(text, PythonLexer(), formatter)
    return mark_safe(highlighted_data)


@register.filter
def boolean_check(value):
    text = '<i class="bi-check-circle-fill text-primary"></i>' if value else ''
    return mark_safe(text)


@register.simple_tag(takes_context=False)
def pigments_css(style='friendly'):
    formatter = HtmlFormatter(style=style, nobackground=True)
    return mark_safe(formatter.get_style_defs('.highlight'))


@register.inclusion_tag('reporter/tool-icon.html')
def tool_icon(**kwargs):
    return kwargs
