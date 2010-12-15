from django import template
from django.template import Library

from imm.lims.models import Data

register = Library()

import logging

@register.simple_tag
def get_location(automounter, container):
    ret_val = automounter.get_position(container)
    return ret_val
