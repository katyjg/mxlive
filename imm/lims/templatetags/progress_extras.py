from django import template
from django.template import Library
from django.shortcuts import render_to_response

from lims.models import Shipment, Crystal

register = Library()

import logging

@register.filter("get_crystal_set")  
def get_crystal_set(shipment):  
    try:
        return shipment.crystal_set.all().order_by('-experiment__priority','-priority')
    except AttributeError:
        return shipment.project.crystal_set.filter(container__dewar__shipment__exact=shipment).order_by('-experiment__priority','-priority')

@register.filter("get_data_set")  
def get_data_set(crystal, kind):  
    return crystal.data_set.filter(kind__exact=kind)

@register.filter("get_obj_type")
def get_obj_type(shipment):
    return str(shipment.__class__.__name__)

@register.filter("object_url")
def object_url(handler):
    return handler.split('progress/')[0]
