from django import template
from django.template import Library
from django.shortcuts import render_to_response
from django.db.models import *

from lims.models import Container, Experiment, Crystal

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
    if object_list[0].container.get_kind_display() == 'Cassette':
        return object_list.order_by('priority','container','container_location')
    return object_list.annotate(port=Sum('container_location')).order_by('priority','container','port')
    

