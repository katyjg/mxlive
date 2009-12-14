"""
Here is a Django template tag that allows you to create complex variables specified in JSON format within a template.

It enables you to do stuff like:

{% var as person %}
{
     "firstName": "John",
     "lastName": "Smith",
      "address": {
          "streetAddress": "21 2nd Street",
          "city": "New York",
          "state": "NY",
          "postalCode": 10021
      },
      "phoneNumbers": [
          "212 555-1234",
          "646 555-4567"
      ]
  }
 {% endvar %}

 <p>{{person.firstName}}, </br>
    {{person.address.postalCode}}, </br>
    {{person.phoneNumbers.1}}
 </p>
"""

from django import template
from django.utils import simplejson
import re

register = template.Library()

class VariablesNode(template.Node):
    def __init__(self, nodelist, var_name):
        self.nodelist = nodelist
        self.var_name = var_name
        
    def render(self, context):
        source = self.nodelist.render(context)
        context[self.var_name] = simplejson.loads(source)
        return ''

@register.tag(name='var')
def do_variables(parser, token):
    try:
        tag_name, arg = token.contents.split(None, 1)
    except ValueError:
        msg = '"%s" tag requires arguments' % token.contents.split()[0]
        raise template.TemplateSyntaxError(msg)
    m = re.search(r'as (\w+)', arg)
    if m:
        var_name, = m.groups()
    else:
        msg = '"%s" tag had invalid arguments' % tag_name
        raise template.TemplateSyntaxError(msg)
           
    nodelist = parser.parse(('endvar',))
    parser.delete_first_token()
    return VariablesNode(nodelist, var_name)


