from ipaddr import _IPAddrBase, IPAddress, IPNetwork

from django.forms import ValidationError as FormValidationError
from django.core.exceptions import ValidationError
from django.forms import fields, widgets
from django.db import models

class IPNetworkWidget(widgets.TextInput):
    def render(self, name, value, attrs=None):
        if isinstance(value, _IPAddrBase):
            value = u'%s' % value
        return super(IPNetworkWidget, self).render(name, value, attrs)


class IPNetworkField(models.Field):
    __metaclass__ = models.SubfieldBase
    description = "IP Network Field with CIDR support"
    empty_strings_allowed = False
            
    def db_type(self, connection):
        return 'varchar(45)'
        
    def to_python(self, value):
        if not value:
            return None

        if isinstance(value, _IPAddrBase):
            return value

        try:
            return IPNetwork(value.encode('latin-1'))
        except Exception, e:
            raise ValidationError(e)

    def get_prep_value(self, value):
        if isinstance(value, _IPAddrBase):
            value = '%s' % value
        return unicode(value)
      
    def formfield(self, **kwargs):
        defaults = {
            'form_class' : fields.CharField,
            'widget': IPNetworkWidget,
        }
        defaults.update(kwargs)
        return super(IPNetworkField, self).formfield(**defaults)

