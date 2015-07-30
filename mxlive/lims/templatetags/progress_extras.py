
from django.template import Library
register = Library()


@register.filter("get_crystal_set")  
def get_crystal_set(shipment):  
    try:
        return shipment.crystal_set.filter(**shipment.project.get_archive_filter()).order_by('-experiment__priority','-priority')
    except AttributeError:
        return shipment.project.crystal_set.filter(container__dewar__shipment__exact=shipment).filter(**shipment.project.get_archive_filter()).order_by('-experiment__priority','-priority')

@register.filter("get_data_set")  
def get_data_set(crystal, kind):  
    return crystal.get_data_set().filter(kind__exact=kind)

@register.filter("get_obj_type")
def get_obj_type(shipment):
    return str(shipment.__class__.__name__)

@register.filter("object_url")
def object_url(handler):
    return handler.split('progress/')[0]

