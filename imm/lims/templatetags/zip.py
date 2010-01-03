"""
Here is a Django template tag that allows you to create perform python zip of lists and tuples a template.

For example, say you have the following dictionary:

info = {'Names': ['John','Mary','Susan',Joe'], 'Ages':[25,45, 11, 20]}

Within the template you could then do

{% zip info.Names, info.Ages as pairs %}
<table>
    <thead>
    <tr>
        <th>Name</th>
        <th>Age</th>
    </tr>
    </thead>
    <tbody>
    {% for pair in pairs %}
        <tr>
        {% for name, age in pair %}
            <td>{{name}}</td><td>{{age}}</td>
        {% endfor %}
        </tr>
    {% endfor}
    </tbody>
</table>
"""

from django import template
import re


register = template.Library()


class ZipNode(template.Node):
    def __init__(self, vals, var_name):
        self.vals = vals
        self.var_name = var_name
    
    def render(self, context):
        _vals = [v.resolve(context) for v in self.vals]
        context[self.var_name] = zip(*_vals)
        return ''
    
    
@register.tag(name='zip')
def do_zip(parser, token):

    try:
        args = token.split_contents()
    except ValueError:
        msg = '"zip" tag requires at least 4 arguments'
        raise template.TemplateSyntaxError(msg)
    if len(args) < 5:
        msg = '"zip" tag requires at least 4 arguments'
        raise template.TemplateSyntaxError(msg)
    if args[-2] != 'as':
        msg = 'Last but one argument of "zip" tag must be "as"'
        raise template.TemplateSyntaxError(msg)
    var_name = args[-1]

    vals = map(template.Variable, args[1:-2])
    
    return ZipNode(vals, var_name)


