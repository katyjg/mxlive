from datetime import datetime, timedelta, date
from dateutil.relativedelta import relativedelta
import sys, os
from numpy import histogram, average, std

from imm.lims.views import admin_login_required
from imm.lims.models import Beamline, Data, Project

from django.shortcuts import render_to_response
from django.template import RequestContext
from django.views.decorators.cache import cache_page
from django.conf import settings

PUBLIC_PATH = getattr(settings, 'PUBLIC_PATH', '/tmp')
sys.path.append(os.path.join(PUBLIC_PATH))
from scheduler.models import Visit, Stat, WebStatus
from scheduler.models import Beamline as PublicBeamline

_provinces = {'British Columbia': ['BC','British Columbia'],
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
@cache_page(60*3600)
def stats_month(request, year, month):
    display = [bl.name for bl in PublicBeamline.objects.using('public-web')]   
    start_time = datetime(int(year), int(month), 1)
    end_time = start_time + relativedelta(months=+1)
    all_data = Data.objects.filter(beamline__name__in=display).filter(created__gt=start_time).filter(created__lt=end_time)
    all_stats = {}
    for d in all_data:
        if not all_stats.has_key(d.project.name):
            all_stats[d.project.name] =  {}
            for bl in PublicBeamline.objects.using('public-web'):
                shifts = []
                bl_data = all_data.filter(project=d.project).filter(beamline__name=bl.name)
                for data in bl_data:
                    if '%s-%s' % (data.created.strftime('%a, %b %d, %Y'), data.created.hour/8) not in shifts:
                        shifts.append('%s-%s' % (data.created.strftime('%a, %b %d, %Y'), data.created.hour/8))
                all_stats[d.project.name][bl.name] = {
                      'shifts': len(shifts),
                      'Screening': bl_data.filter(kind=Data.DATA_TYPES.SCREENING).count(),
                      'Collection': bl_data.filter(kind=Data.DATA_TYPES.COLLECTION).count()
                      }
                
    return render_to_response('stats/statistics.html', {
        'month': [int(month), int(year)],
        'stats': all_stats,
        'display': display,
        }, context_instance=RequestContext(request))    
    
@admin_login_required
@cache_page(60*3600)
def stats_calendar(request, month=None):
    mon = month and int(month.split('-')[1]) or datetime.today().month
    today = month and datetime(year=int(month.split('-')[0]), month=mon, day=datetime.today().day) or datetime.today()
    prev_month = (datetime(today.year, mon, 1) + relativedelta(months=-1)).strftime('%Y-%m')
    next_month = (datetime(today.year, mon, 1) + relativedelta(months=+1)).strftime('%Y-%m')

    display = {}
    for bl in PublicBeamline.objects.using('public-web'):
        display[bl.name] = bl.pk
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
            data = Data.objects.filter(created__gt=filter_today).filter(created__lt=filter_tomorrow).order_by('created').filter(beamline__name__in=display.keys())
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
@cache_page(60*3600)
def stats_params(request, year=None, cumulative=False):   
    all_datasets = Data.objects.all()
    today = date.today()  
    if year:
        today = date.today()    
        start_year = date(int(year), 1, 1)
        end_year = date(int(year), 12, 31)
        if today < end_year:
            end_year = today
        all_datasets = all_datasets.filter(created__gte=start_year).filter(created__lte=end_year)
    else: year = today.year
    beamlines = PublicBeamline.objects.using('public-web')
    exp_data = {}
    stat = {}
    for bl in Beamline.objects.all():
        if bl.name in [b.name for b in beamlines]:
            datasets = all_datasets.filter(beamline__exact=bl).filter(kind__exact=Data.DATA_TYPES.COLLECTION)
            exp_data[bl.name] = {}
            for type in ['exposure_time','wavelength','delta_angle','resolution']:
                if type == 'wavelength':
                    stat[type] = [data.energy() for data in datasets]
                else:
                    stat[type] = [data.__dict__[type] for data in datasets]
                num_bins = 20
                stat[type] = [x for x in stat[type] if x < ( average(stat[type]) + 3 * std(stat[type])) ]
                if stat[type]:
                    exp_data[bl.name][type] = histogram(stat[type], bins=num_bins, range=(min(stat[type]), max(stat[type])))
                    exp_data[bl.name][type] = [[exp_data[bl.name][type][1][i], exp_data[bl.name][type][0][i]] for i in range(num_bins) ]

    return render_to_response('stats/param_stats.html', {
        'years': [int(today.year), int(year) +1, int(year) -1, int(year)],
        'exp_data': exp_data,
        'cumulative': cumulative,
        }, context_instance=RequestContext(request))

@admin_login_required
@cache_page(60*3600)
def stats_year(request, year):

    prov_list = ['Saskatchewan','British Columbia','Alberta','Manitoba','Ontario','Quebec','New Brunswick','Nova Scotia','Prince Edward Island','Newfoundland','Other','No Matching MxLIVE Account']
    labels = ['Normal','Remote','Mail-In','Purchased Access','Maintenance','Unallocated']
    colors = ['#7DCF7D','#A2DDDD','#CCE3B5','#FFCB94','#bbbbbb','#dddddd']
    month_labels = ('Jan','Feb','Mar','Apr','May','Jun','Jul','Aug','Sep','Oct','Nov','Dec')
    
    today = date.today()
    start_year = date(int(year), 1, 1)
    end_year = date(int(year), 12, 31)
    if today < end_year:
        end_year = today
    one_day = timedelta(days=1)
    year = end_year.year
    
    shift_usage_labels = [[k, month_labels[k]] for k in range(len(month_labels)) if k < int(end_year.month)]
    
    shift_stats = {}
    shift_usages = {}
    extra_visit = {}
    
    all_visits = Visit.objects.using('public-web').filter(start_date__lte=end_year).filter(end_date__gte=start_year)
    visits = all_visits.exclude(proposal=None)
    beamlines = PublicBeamline.objects.using('public-web')
    nstat = Stat.objects.using('public-web').filter(mode__in=['NormalMode']).filter(start_date__lte=end_year, end_date__gte=start_year)
    nwebstat = WebStatus.objects.using('public-web').filter(date__endswith=str(year))
    datasets = Data.objects.filter(created__year=year)

    prod_dates = {}
    prod_stats = {}
    nlist = []
    unused = {}
    for n in nstat: # Start making a list of all the normal shifts in the given time frame
        if n.start_date == n.end_date:
            for i in range(3):
                if i >= n.first_shift and i <= n.last_shift: 
                    nlist.append([n.start_date,i,[None, None]])
        else:
            for i in range(3):
                if i >= n.first_shift: 
                    nlist.append([n.start_date,i,[None, None]])
            next = n.start_date + one_day
            while next < n.end_date:
                for i in range(3): 
                    nlist.append([next,i,[None, None]])
                next += one_day
            for i in range(3):
                if i <= n.last_shift: 
                    nlist.append([n.end_date,i,[None, None]])
    
    next_day = start_year
    while next_day <= end_year: # Add more shifts to the list of normal shifts, from the WebStatus model
        for shift in range(3):
            if [next_day, shift, [None, None]] not in nlist and nwebstat.filter(date__exact=next_day.strftime('%b/%d/%Y')).exists():
                ws = nwebstat.get(date__exact=next_day.strftime('%b/%d/%Y'))
                wslist = [ws.status1, ws.status2, ws.status3]
                if wslist[shift] and wslist[shift][0] == 'N' and (len(wslist[shift]) == 1 or not wslist[shift][1] == 'S'):
                    nlist.append([next_day, shift,[None, None]])
        next_day += one_day
    
    for i, bl in enumerate(beamlines):
        extra_visit[bl.name] = [all_visits.filter(beamline=bl).count(),visits.filter(beamline=bl).count(),all_visits.filter(beamline=bl).filter(proposal=None)] # Visits that don't have a proposal attached
        shift_stats[bl.name] = {} # How much time users had who visited this year
        shift_usages[bl.name] = {} # How N shifts were used
        prod_dates[bl.name] = {} # Productivity stats
        prod_stats[bl.name] = {} # Productivity stats
        unused[bl.name] = {'nights': 0, 'days': 0}
        for prov in prov_list: shift_stats[bl.name][prov] = {}
        for j, lab in enumerate(labels): 
            shift_usages[bl.name][lab] = [[[m,0] for m in range(0,end_year.month)], colors[j]]
            if lab in ['Mail-In','Remote','Purchased Access','Normal']: 
                prod_stats[bl.name][lab] = [0,0,0,0,0,0]
                prod_dates[bl.name][lab] = []
        for n in nlist:
            for v in all_visits.filter(beamline=bl).filter(start_date__lte=n[0]).filter(end_date__gte=n[0]):
                if v.get_shifts(n[0])[n[1]] is not None:
                    n[2][i] = v.get_shifts(n[0], ids=True)[n[1]][1]
            if n[2][i] is not None:
                if n[2][i].maintenance: mode = 'Maintenance'
                elif n[2][i].remote: mode = 'Remote'
                elif n[2][i].mail_in: mode = 'Mail-In'
                elif n[2][i].purchased: mode = 'Purchased Access'
                else: mode = 'Normal'
                if n[2][i].proposal:
                    country = None
                    if Project.objects.filter(name__exact=n[2][i].proposal_account()).exists(): # proposal exists AND there's an MxLIVE project
                        group_name = Project.objects.get(name__exact=n[2][i].proposal_account()).name 
                        province = Project.objects.get(name__exact=n[2][i].proposal_account()).province
                        for prov, vals in _provinces.items(): 
                            if province in vals: 
                                province = prov
                        province = ( province in prov_list and province ) or 'Other'
                        if province == 'Other': country = Project.objects.get(name__exact=n[2][i].proposal_account()).country
                    else: # proposal exists, but no MxLIVE account
                        group_name = n[2][i].proposal_display()
                        province = 'No Matching MxLIVE Account' 
                    if not shift_stats[bl.name][province].has_key(group_name): # First appearance of this group
                        shifts_used = 0
                        for a in n[2][i].proposal.account_list():
                            shifts_used += Project.objects.filter(name__exact=a).exists() and Project.objects.get(name__exact=a).shifts_used_by_year(today.year, bl.name) or 0
                        shift_stats[bl.name][province][group_name] = [[n[2][i]], 0, shifts_used]
                    elif n[2][i] not in shift_stats[bl.name][province][group_name][0]: # Not first appearance, but new visit
                        shift_stats[bl.name][province][group_name][0].append(n[2][i])
                    if not n[2][i].maintenance: shift_stats[bl.name][province][group_name][1] += 1 # Add a scheduled shift
                    if country and country not in shift_stats[bl.name][province][group_name]: shift_stats[bl.name][province][group_name].append(country)
            else: 
                mode = 'Unallocated'
                if n[1] == 2 or n[0].weekday() in [5,6]: unused[bl.name]['nights'] += 1
                else: unused[bl.name]['days'] += 1
            shift_usages[bl.name][mode][0][n[0].month-1][1] += 1
            if mode in ['Mail-In','Remote','Purchased Access','Normal']:
                prod_dates[bl.name][mode].append([n[0],n[1]])
        for prov in prov_list: 
            for key, val in shift_stats[bl.name][prov].items():
                shift_stats[bl.name][prov][key][0] = len(val[0])
    
    # Want [#datasets(full), avg_datasets(full), shutter_time_open, avg_shutter_time, number_shifts_scheduled]
    for bl, modes in prod_dates.items():
        for mode, dates in modes.items():
            for d in dates:
                prod_stats[bl][mode][4] += 1
                s = (d[1] < 2 and d[1]+1) or 0 
                data_date = (s is not 0 and d[0]) or d[0] + one_day
                for data in datasets.filter(created__month=data_date.month).filter(created__day=data_date.day):
                    if data.created.hour in range(s*8, s*8+8):
                        if data.kind == Data.DATA_TYPES.COLLECTION:
                            prod_stats[bl][mode][0] += 1
                        prod_stats[bl][mode][2] += data.exposure_time * data.num_frames()
            if prod_stats[bl][mode][4]:
                prod_stats[bl][mode][1] = prod_stats[bl][mode][0]/float(prod_stats[bl][mode][4]*8)
                prod_stats[bl][mode][3] = prod_stats[bl][mode][2]/float(prod_stats[bl][mode][4]*8)
        
    return render_to_response('stats/beamline_stats.html', {
        'years': [int(today.year), int(year) +1, int(year) -1, int(year)],
        'unused': unused,
        'users': shift_stats,
        'visits': extra_visit,
        'shift_usage': shift_usages,
        'prod_stats': prod_stats,
        'shift_usage_labels': shift_usage_labels,
        'type_labels': labels,
        'modes': ['Purchased Access','Normal','Remote','Mail-In'],
        }, context_instance=RequestContext(request))
