from django import template
from django.template import Library
from datetime import datetime, timedelta
from dateutil.relativedelta import relativedelta

from lims.models import Data, Project, Result, ScanResult

register = Library()

import logging

@register.filter("format_data")
def format_data(data, beamline):
    projects = []
    for i in range(len(data)):
        print data[i].project.name
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

@register.filter("bl_name")
def bl_name(name):
    return name.replace('08','')

@register.filter("by_kind")
def by_kind(data, kind):
    return data.filter(kind__exact=kind).count()

@register.filter("user_project")
def user_project(data):
    return Project.objects.filter(pk__in=data.values('project'))

@register.filter("by_project")
def by_project(data, project):
    return data.filter(project__exact=project)

@register.filter("by_bl")
def by_bl(data, beamline):
    return data.filter(beamline__name__exact=beamline)

@register.filter("num_shifts")
def num_shifts(data, month):
    one_shift = timedelta(hours=8)
    start_time = datetime(month[2], month[0], 1)
    next_month = start_time + relativedelta(months=+1)
    num_shifts = 0
    while start_time < next_month:
        if data.filter(created__gt=start_time).filter(created__lt=start_time+one_shift).exists():
            num_shifts += 1
        start_time += one_shift
    return num_shifts

@register.filter("report_filter")
def report_filter(month, project):
    start_time = datetime(month[2], month[0], 1)
    next_month = start_time + relativedelta(months=+1)
    return Result.objects.filter(project__exact=project).filter(created__gt=start_time).filter(created__lt=next_month).count()

@register.filter("scan_filter")
def scan_filter(month, project):
    start_time = datetime(month[2], month[0], 1)
    next_month = start_time + relativedelta(months=+1)
    return ScanResult.objects.filter(project__exact=project).filter(created__gt=start_time).filter(created__lt=next_month).count()


