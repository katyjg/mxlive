from django import template
from django.template import Library
from django.db import models
from django.core.exceptions import ObjectDoesNotExist
from django.utils import dateformat
from django.utils.html import escape
from django.utils.text import capfirst
from django.utils.translation import get_date_formats
from django.contrib import admin
from django.conf import settings 
from django.utils.safestring import mark_safe
from django.utils.datastructures import MultiValueDict

from imm.lims.models import Container
from imm.lims.models import Experiment
from imm.lims.models import Crystal

register = Library()

@register.inclusion_tag('lims/entries/experiment_table.html', takes_context=True)
def experiment_table(context, object, admin):
    containers = object.project.container_set.filter(dewar__in=object.dewar_set.all())
    experiments = object.project.experiment_set.filter(pk__in=object.project.crystal_set.filter(container__dewar__shipment__exact=object.pk).values('experiment'))
    list_exps = list(experiments.exclude(priority__isnull=True).exclude(priority__exact=0).order_by('priority')) + list(experiments.exclude(priority__gte=1))

    return { 'experiments': list_exps,
              'containers': containers,
              'admin': admin,
              'object': object
            }

@register.filter("in_shipment")  
def in_shipment(crystals, containers):
    return crystals.filter(container__in=containers).count()

@register.filter("arrived_onsite")
def arrived_onsite(crystals, containers):
    return crystals.filter(container__in=containers).filter(status__in=[Crystal.STATES.ON_SITE, Crystal.STATES.LOADED]).count()
