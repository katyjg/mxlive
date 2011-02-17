from django import template
from django.template import Library
from django.shortcuts import render_to_response


from lims.models import Container

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
    experiment_list = list()
    if object.containers:
        for container in object.containers.all():
            cont_experiment_list = container.get_experiment_list()
            for experiment in cont_experiment_list:
                if experiment not in experiment_list:
                    experiment_list.append(experiment)
    
    return { 'experiments': experiment_list,
              'admin': admin,
              'object': object
            }

@register.filter("in_runlist")  
def in_runlist(crystals, containers):  
    crystal_set = list()    
    if containers:
        for container in containers.all():
            for crystal in crystals.all():
                if crystal.container == container:
                    crystal_set.append(crystal)
        
    return len(crystal_set)

@register.filter("runlist_position")
def runlist_position(runlist, container):
    return runlist.get_position(container)

@register.filter("prioritize")
def prioritize(object_list):
    return object_list.order_by('priority').reverse()
    
    

