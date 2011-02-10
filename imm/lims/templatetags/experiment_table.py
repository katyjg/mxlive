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

register = Library()

@register.inclusion_tag('lims/entries/experiment_table.html', takes_context=True)
def experiment_table(context, object, admin):
    experiment_list = list()
    experiments = list()
    dewar_list = object.dewar_set.all()
    conts = list()
    for dewar in dewar_list:
        cont_list = dewar.container_set.all()
        for cont in cont_list:
            if cont not in conts:
                conts.append(cont)

    if conts:
        for container in conts:
            cont_experiment_list = container.get_experiment_list()
            for experiment in cont_experiment_list:
                if experiment not in experiment_list:
                    experiment_list.append(experiment)
    
    for exp in Experiment.objects.all().order_by('priority').reverse():
        if exp in experiment_list:
            experiments.append(exp)

    
    return { 'experiments': experiments,
              'containers': conts,
              'admin': admin,
              'object': object
            }

@register.filter("in_shipment")  
def in_shipment(crystals, containers):  
    crystal_set = list()    
    if containers:
        for container in containers:
            for crystal in crystals.all():
                if crystal.container == container:
                    crystal_set.append(crystal)
        
    return len(crystal_set)
