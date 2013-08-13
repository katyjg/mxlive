from django.template import Library
from datetime import datetime, timedelta
from dateutil.relativedelta import relativedelta

from django.contrib.auth.models import User

from lims.models import Project

from django.conf import settings
import sys, os
PUBLIC_PATH = getattr(settings, 'PUBLIC_PATH', '/tmp')
sys.path.append(os.path.join(PUBLIC_PATH))
from scheduler.models import Visit, Proposal

register = Library()

@register.filter("format_data")
def format_data(data, beamline):
    projects = []
    for i in range(len(data)):
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

@register.filter("by_kind")
def by_kind(data, kind):
    return data.filter(kind__exact=kind).count()

@register.filter("user_project")
def user_project(data):
    return Project.objects.filter(pk__in=data.values('project')).order_by('name')

@register.filter("by_project")
def by_project(data, project):
    try:
        return data.filter(project__name__exact=project)
    except ValueError:
        return data

@register.filter("by_bl")
def by_bl(data, beamline):
    return data.filter(beamline__name__exact=beamline)

@register.filter("num_shifts")
def num_shifts(data, month):
    one_shift = timedelta(hours=8)
    start_time = datetime(month[1], month[0], 1)
    next_month = start_time + relativedelta(months=+1)
    num_shifts = 0
    while start_time < next_month:
        if data.filter(created__gt=start_time).filter(created__lt=start_time+one_shift).exists():
            num_shifts += 1
        start_time += one_shift
    return num_shifts

@register.filter("sum_shifts")
def sum_shifts(lst):
    num = 0
    for v in lst:
        num += v.get_num_shifts()
    return num

@register.filter("sum_dict")
def sum_dict(dct, i):
    total = 0
    for v in dct.values():
        total = total + v[i]
    return total

@register.filter("sum_index")
def sum_index(lst, i):
    total = 0
    for v in lst:
        total += v[i]
    return total

@register.filter("dict_key")
def dict_key(dct, key):
    return dct[key]

@register.filter("stripspace")
def stripspace(txt):
    return txt.replace(' ','')

@register.filter("is_remote")
def is_remote(user, year):
    if User.objects.filter(username=user).exists() and Proposal.objects.using('public-web').filter(last_name=User.objects.get(username=user).last_name).exists():
        visits = Visit.objects.using('public-web').filter(proposal__in=Proposal.objects.using('public-web').filter(last_name=User.objects.get(username=user).last_name))
        if visits.filter(mail_in=True).exists() or visits.filter(remote=True):
            return '*'
    return ''

@register.filter("is_pi")
def is_pi(user, year):
    props = Proposal.objects.using('public-web').filter(expiration__gte=datetime(year,1,1))
    if User.objects.filter(username=user).exists() and not props.filter(last_name=User.objects.get(username=user).last_name).exists():
        return props.filter(account__icontains=user).values('last_name','proposal_id')
    return []
