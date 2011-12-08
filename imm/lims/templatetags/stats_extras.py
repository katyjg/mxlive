from django import template
from django.template import Library
from datetime import datetime

from lims.models import Data

register = Library()

import logging

@register.filter("format_data")
def format_data(data, beamline):
    projects = []
    for i in range(len(data)):
        print data[i].beamline.name
        if data[i].beamline.name == beamline:
            k = None
            for j in range(len(projects)):
                if projects[j][0] == data[i].project.name:
                    k = j
            if k is not None:
                projects[k][1] += 1
                projects[k][3] = data[i].created.strftime("%H:%M")
            else:
                projects.append([data[i].project.name, 
                                 1, 
                                 data[i].created.strftime("%H:%M"), 
                                 data[i].created.strftime("%H:%M")])      
    return projects or ''
