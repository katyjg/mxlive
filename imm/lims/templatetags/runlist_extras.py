from django import template
from django.template import Library
from django.shortcuts import render_to_response
from django.db.models import *

from lims.models import Container, Experiment, Crystal
from staff.models import Runlist

register = Library()

import logging

@register.inclusion_tag('staff/entries/auto_list.html', takes_context=True)
def auto_location(context, object, side):
    if side == 'left' and type(object.left).__name__=='int':
        cassette = Container.objects.get(pk=object.left)
    elif side == 'middle' and type(object.middle).__name__=='int':
        cassette = Container.objects.get(pk=object.middle)
    elif side == 'right' and type(object.right).__name__=='int':
        cassette = Container.objects.get(pk=object.right)
    else:
        cassette = None
    return { 'object': object,
              'side': side,
              'cassette': cassette
            }

@register.inclusion_tag('staff/entries/auto_position.html', takes_context=True)
def automounter_position(context, object, side, spot, letter):
    if side == "left":
        try: 
            cont = Container.objects.get(pk=object.left[spot])
        except:
            cont = None
        position = "L" + letter
    if side == "middle":
        try: 
            cont = Container.objects.get(pk=object.middle[spot])
        except:
            cont = None
        position = "M" + letter
    if side == "right":
        try: 
            cont = Container.objects.get(pk=object.right[spot])
        except:
            cont = None
        position = "R" + letter
    return { 'container': cont,
              'object': object,
              'letter': position }

@register.inclusion_tag('staff/entries/experiment_table.html', takes_context=True)
def experiment_table(context, object, admin):
    experiments = Experiment.objects.filter(pk__in=Crystal.objects.filter(container__pk__in=object.containers.all()).values('experiment')).order_by('priority')
    return { 'experiments': experiments,
              'admin': admin,
              'object': object
            }

@register.filter("pos_full")
def pos_full(runlist, side):
    return runlist.position_full(side[0].upper())

@register.filter("in_runlist")  
def in_runlist(crystals, containers):  
    return len(crystals.all().filter(container__pk__in=containers.all()))

@register.filter("runlist_position")
def runlist_position(runlist, container):
    return runlist.get_position(container)

@register.filter("prioritize")
def prioritize(object_list):
    return object_list.order_by('priority')
  
@register.filter('prioritize_and_sort')
def prioritize_and_sort(object_list):
    if len(object_list) and object_list[0].container.get_kind_display() == 'Cassette':
        obj_list = list(object_list.filter(priority__gte=1).order_by('priority','container','container_location')) + \
                   list(object_list.exclude(priority__gte=1).order_by('priority','container','container_location'))
    else:
        obj_list = list(object_list.filter(priority__gte=1).annotate(port=Sum('container_location')).order_by('priority','container','port')) + \
                   list(object_list.exclude(priority__gte=1).annotate(port=Sum('container_location')).order_by('priority','container','port'))
    return obj_list
    
@register.filter('num_containers')
def num_containers(project, pk):
    runlist = Runlist.objects.get(pk=pk)
    return Container.objects.filter(project__exact=project).filter(status__exact=Container.STATES.ON_SITE).exclude(pk__in=runlist.containers.all()).exclude(kind__exact=Container.TYPE.CANE).count()

@register.filter('get_container_type')
def get_container_type(pk):
    try:
        c = Container.objects.get(pk=int(float(pk)))
        return c.get_kind_display()
    except:
        return ''

@register.filter('get_container_project')
def get_container_project(pk):
    try:
        c = Container.objects.get(pk=int(float(pk)))
        return c.project
    except: 
        return ''
