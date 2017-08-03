
from django.template import Library
register = Library()


@register.filter("get_sample_set")
def get_sample_set(shipment):
    try:
        return shipment.sample_set.filter(**shipment.project.get_archive_filter()).order_by('-experiment__priority','-priority')
    except AttributeError:
        return shipment.project.sample_set.filter(container__dewar__shipment__exact=shipment).filter(**shipment.project.get_archive_filter()).order_by('-experiment__priority','-priority')

@register.filter("get_data_set")  
def get_data_set(crystal, kind):  
    return crystal.get_data_set().filter(kind__exact=kind)

@register.filter("get_obj_type")
def get_obj_type(shipment):
    return str(shipment.__class__.__name__)

@register.filter("object_url")
def object_url(handler):
    return handler.split('progress/')[0]


