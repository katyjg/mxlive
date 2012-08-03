from datetime import datetime, timedelta, date
import datetime as ddatetime
from dateutil.relativedelta import relativedelta
import calendar
import sys, os

from imm.lims.views import admin_login_required
from imm.lims.models import *

from django.shortcuts import render_to_response
from django.template import RequestContext
from django.http import HttpResponse
from django.utils.datastructures import SortedDict

sys.path.append(os.path.join('/var/website/cmcf-website/cmcf'))
from scheduler.models import Visit, Stat, WebStatus, Proposal
from scheduler.models import Beamline as CMCFBeamline

provinces = {'British Columbia': ['BC','British Columbia'],
             'Alberta': ['AB', 'Alberta'],
             'Saskatchewan': ['SK','Saskatchewan','Sask'],
             'Manitoba': ['MB','Manitoba','Man'],
             'Ontario': ['ON','Ontario','Ont'],
             'Quebec': ['QC','Quebec','Que'],
             'New Brunswick': ['NB','New Brunswick'],
             'Nova Scotia': ['NS','Nova Scotia'],
             'Prince Edward Island': ['PEI','Prince Edward Island'],
             'Newfoundland': ['NL','Newfoundland', 'Nfld'],
             }

@admin_login_required
def stats_month(request, year, month):
    display = ['08ID-1', '08B1-1']   
    start_time = datetime(int(year), int(month), 1)
    end_time = start_time + relativedelta(months=+1)
    all_data = Data.objects.filter(beamline__name__in=display).filter(created__gt=start_time).filter(created__lt=end_time)
    return render_to_response('stats/statistics.html', {
        'month': [int(month), int(year)],
        'data': all_data,
        'display': display,
        }, context_instance=RequestContext(request))    
    
@admin_login_required
def stats_calendar(request, month=None):
    mon = month and int(month.split('-')[1]) or datetime.today().month
    today = month and datetime(year=int(month.split('-')[0]), month=mon, day=datetime.today().day) or datetime.today()
    prev_month = (datetime(today.year, mon, 1) + relativedelta(months=-1)).strftime('%Y-%m')
    next_month = (datetime(today.year, mon, 1) + relativedelta(months=+1)).strftime('%Y-%m')

    display = ['08ID-1', '08B1-1']
    current_date = (datetime.today().strftime('%Y-%m-%d') == today.strftime('%Y-%m-%d')) and today.day or 0

    dates = []
    week = []
    i = 0
    first_day = (today - timedelta(days=(today.day-1))) - timedelta(days=(today - timedelta(days=(today.day-1))).weekday())
    while (first_day+timedelta(days=i*7)).month is today.month or i == 0:
        week = []
        for j in range(7):
            this_day = first_day + timedelta(days=(j + i*7))
            filter_today = datetime(this_day.year, this_day.month, this_day.day)
            filter_tomorrow = filter_today + timedelta(days=1)
            data = Data.objects.filter(created__gt=filter_today).filter(created__lt=filter_tomorrow).order_by('created')
            week.append([this_day.day,this_day.month,data])
        i += 1
        dates.append(week)

    return render_to_response('stats/calendar.html', {
        'month': [mon, today.strftime('%B'), today.year, prev_month, next_month],
        'current_date': current_date,
        'display': display,
        'dates': dates,
        }, context_instance=RequestContext(request))
    
    
@admin_login_required
def stats_year(request, year):

    prov_list = ['Saskatchewan','British Columbia','Alberta','Manitoba','Ontario','Quebec','New Brunswick','Nova Scotia','Prince Edward Island','Newfoundland','Other','No Matching MxLIVE Account']
    labels = ['Normal','Remote','Mail-In','Purchased Access','Maintenance','Unallocated']
    colors = ['#7DCF7D','#A2DDDD','#CCE3B5','#FFCB94','#dddddd','#bbbbbb']
    month_labels = ('Jan','Feb','Mar','Apr','May','Jun','Jul','Aug','Sep','Oct','Nov','Dec')
    
    today = ddatetime.date.today()
    start_year = ddatetime.date(int(year), 1, 1)
    end_year = ddatetime.date(int(year), 12, 31)
    if today < end_year:
        end_year = today
    one_day = timedelta(days=1)
    one_shift = timedelta(hours=8)
    
    shift_usage_labels = [[k, month_labels[k]] for k in range(len(month_labels)) if k < int(end_year.month)]
    
    shift_stats = {}
    shift_stats['users'] = {}
    
    all_datasets = Data.objects.filter(created__gte=start_year).filter(created__lte=end_year)
    beamlines = CMCFBeamline.objects.using('cmcf-web').exclude(name__exact='SIM-1')
    visits = Visit.objects.using('cmcf-web').filter(start_date__lte=end_year).filter(end_date__gte=start_year)
    props = Proposal.objects.using('cmcf-web').filter(pk__in=visits.values('proposal').distinct())
    nstat = Stat.objects.using('cmcf-web').filter(mode__in=['NormalMode']).filter(start_date__lte=end_year, end_date__gte=start_year)
    nwebstat = WebStatus.objects.using('cmcf-web').filter(date__endswith=str(year))
    
    vlist = {}
    for bl in beamlines: vlist[bl.name] = {}
    for v in visits: # Get a list of all visits, sorted by the type of visit
        # Choose which dictionary key to use
        if v.remote: dkey = 'Remote'
        elif v.mail_in: dkey = 'Mail-In'
        elif v.purchased: dkey = 'Purchased Access'
        elif v.maintenance: dkey = 'Maintenance'
        else: dkey = 'Normal'
        if not vlist[v.beamline.name].has_key(dkey): vlist[v.beamline.name][dkey] = []
        # Add entries to vlist for each shift
        if v.start_date == v.end_date:
            for i in range(3):
                if i >= v.first_shift and i <= v.last_shift: vlist[v.beamline.name][dkey].append([v.start_date, i])
        else:
            for i in range(3):
                if i >= v.first_shift: vlist[v.beamline.name][dkey].append([v.start_date, i])
            next = v.start_date + one_day
            while next < v.end_date:
                for i in range(3): vlist[v.beamline.name][dkey].append([next, i])
                next += one_day
            for i in range(3): 
                if i <= v.last_shift: vlist[v.beamline.name][dkey].append([v.end_date, i])
    
    nlist = []
    for n in nstat: # Start making a list of all the  normal shifts in the given time frame
        if n.start_date == n.end_date:
            for i in range(3):
                if i >= n.first_shift and i <= n.last_shift: nlist.append([n.start_date,i])
        else:
            for i in range(3):
                if i >= n.first_shift: nlist.append([n.start_date,i])
            next = n.start_date + one_day
            while next < n.end_date:
                for i in range(3): nlist.append([next,i])
                next += one_day
            for i in range(3):
                if i <= n.last_shift: nlist.append([n.end_date,i]) 
    
    next_day = start_year
    while next_day <= end_year: # Add more shifts to the list of normal shifts, from the WebStatus model
        for shift in range(3):
            if [next_day, shift] not in nlist and nwebstat.filter(date__exact=next_day.strftime('%b/%d/%Y')).exists():
                ws = nwebstat.get(date__exact=next_day.strftime('%b/%d/%Y'))
                wslist = [ws.status1, ws.status2, ws.status3]
                if wslist[shift] and wslist[shift][0] == 'N' and (len(wslist[shift]) == 1 or not wslist[shift][1] == 'S'):
                    nlist.append([next_day, shift])
        next_day += one_day

    months, shift_usage, extra_visits = {}, {}, {}
    
    for bl in beamlines:
        stats = {}
        _projs_checked = []
        bl_visits = visits.filter(beamline__exact=bl).filter(maintenance=False)
        extra_visits[bl.name] = [bl_visits.count(), bl_visits.exclude(proposal=None).count(), bl_visits.filter(proposal=None)]
        for x in props:
            num_shifts, num_visits, num_used = 0, 0, 0
            projs = []
            pi, prov = None, None
            account_list = x.account and [a for a in x.account.replace(' ','').split(',')] or []
            if Project.objects.filter(name__in=account_list).exists():
                projs = Project.objects.filter(name__in=account_list)
                pi = Project.objects.filter(name__exact=account_list[0]).exists() and Project.objects.get(name__exact=account_list[0]) or None
            elif Project.objects.filter(user__last_name__exact=str(x.last_name)).filter(user__first_name__startswith=str(x.first_name)[0]).exists():
                projs = Project.objects.filter(user__last_name__exact=str(x.last_name)).filter(user__first_name__startswith=str(x.first_name)[0])
                pi = projs[0]
            if pi:
                for k, v in provinces.items():
                    prov = prov == None and str(pi.province) in v and k or prov
                prov = prov and prov or 'Other'
            group = pi and pi or x
            prov = prov and prov or 'No Matching MxLIVE Account'
            if not stats.has_key(prov): stats[prov] = {}
            for v in bl_visits.filter(proposal__exact=x):
                num_visits += 1
                if v.start_date == v.end_date:
                    for i in range(3):
                        if i >= v.first_shift and i <= v.last_shift: num_shifts += 1
                else:
                    for i in range(3):
                        if i >= v.first_shift: num_shifts += 1
                    next = v.start_date + one_day
                    while next < v.end_date:
                        for i in range(3): num_shifts += 1
                        next += one_day
                    for i in range(3): 
                        if i <= v.last_shift: num_shifts += 1
            if num_visits or num_shifts:
                if stats[prov].has_key(group):
                    stats[prov][group][0] += num_visits
                    stats[prov][group][1] += num_shifts
                else: stats[prov][group] = [num_visits, num_shifts, num_used]
            for p in account_list:
                num_used = 0
                data = all_datasets.filter(beamline__exact=Beamline.objects.get(name__exact=bl.name)).filter(project__name=p).values('created')
                if data and p not in _projs_checked:
                    _projs_checked.append(p)
                    _shifts_checked = []
                    for d in data:
                        first_shift = datetime(d['created'].year, d['created'].month, d['created'].day)
                        if first_shift not in _shifts_checked:
                            _shifts_checked.append(first_shift)
                            for i in range(3):
                                if data.filter(created__gte=first_shift+(one_shift*i)).filter(created__lte=first_shift+(one_shift*(i+1))).exists():
                                    num_used += 1
                if num_used:
                    if stats[prov].has_key(group):
                        stats[prov][group][2] += num_used
                    else: stats[prov][group] = [num_visits, num_shifts, num_used]
            
        shift_stats['users'][bl.name] = SortedDict([(k, stats[k]) for k in prov_list if stats.has_key(k)])
        months[bl.name] = [0]*6
        for i, type in enumerate(labels):
            months[bl.name][i] = [0]*end_year.month
        for ns in nlist:
            sh = [k for k, v in vlist[bl.name].iteritems() if ns in v]
            if len(sh) == 1:
                months[bl.name][labels.index(sh[0])][ns[0].month-1] +=1
            elif len(sh) == 0:
                months[bl.name][labels.index('Unallocated')][ns[0].month-1] +=1
        shift_usage[bl.name] = {}
        for i, type in enumerate(labels):
            shift_usage[bl.name][type] = [[], colors[i]]
            for j, val in enumerate(months[bl.name][i]):
                shift_usage[bl.name][type][0].append([j, months[bl.name][i][j]])

    
    return render_to_response('stats/beamline_stats.html', {
        'years': [int(today.year), int(year) +1, int(year) -1, int(year)],
        'users': shift_stats['users'],
        'visits': extra_visits,
        'shift_usage': shift_usage,
        'shift_usage_labels': shift_usage_labels,
        'type_labels': labels,
        }, context_instance=RequestContext(request))
