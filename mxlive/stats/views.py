
from datetime import datetime, timedelta, date
from dateutil.relativedelta import relativedelta
from django.conf import settings
from django.shortcuts import render_to_response
from django.template import RequestContext
from django.views.decorators.cache import cache_page
from django.utils import timezone
from numpy import histogram, average, std
from scheduler.models import Beamline as PublicBeamline
from scheduler.models import Visit, Stat
from lims.models import Beamline, Data, Project, ScanResult
from lims.views import admin_login_required

from collections import OrderedDict


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
@cache_page(3600)
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
def stats_profiles(request):
    return render_to_response('stats/profiles.html', {
        'projects': Project.objects.all().order_by('name'),
        }, context_instance=RequestContext(request))    
    
@admin_login_required
@cache_page(3600)
def stats_calendar(request, month=None):
    mon = month and int(month.split('-')[1]) or timezone.now().month
    yr = month and int(month.split('-')[0]) or timezone.now().year
    today = timezone.make_aware(datetime.combine(datetime(year=yr, month=mon, day=timezone.now().day), datetime.min.time()), timezone.get_current_timezone())
    prev_month = (datetime(yr, mon, 1, 0, 0, 0) + relativedelta(months=-1)).strftime('%Y-%m')
    next_month = (datetime(yr, mon, 1, 0, 0, 0) + relativedelta(months=+1)).strftime('%Y-%m')

    display = {}
    for bl in PublicBeamline.objects.using('public-web'):
        display[bl.name] = Beamline.objects.get(name=bl.name).pk

    dates = []
    i = 0
    first_day = (today - timedelta(days=(today.day-1))) - timedelta(days=(today - timedelta(days=(today.day-1))).weekday())
    data = Data.objects.filter(created__gte=first_day).filter(created__lt=(first_day+timedelta(days=42))).filter(beamline__name__in=display.keys())
    while (first_day+timedelta(days=i*7)).month is today.month or i == 0:
        week = {'dates': [], 'info': {bl:[] for bl in display.keys()}}
        for j in range(7):
            this_day = first_day + timedelta(days=(j + i*7))
            week['dates'].append(this_day)
            for blname, bl in display.items():
                ddata = data.filter(created__gte=this_day).filter(created__lt=(this_day + timedelta(days=1))).filter(beamline=bl)
                users = ddata.values_list('project__user__username',flat=True).distinct()
                uinfo = []
                for user in users:
                    udata = ddata.filter(project__user__username=user).order_by('created')
                    uinfo.append([user, udata.count(), udata[0].created, udata.latest('created').created])
                week['info'][blname].append((this_day,uinfo))
        i += 1
        dates.append(week)

    return render_to_response('stats/calendar.html', {
        'month': [today, prev_month, next_month],
        'current_date': timezone.now().date(),
        'dates': dates,
        }, context_instance=RequestContext(request))
    
@admin_login_required
@cache_page(24*3600)
def stats_params(request, year=None, cumulative=False):   
    all_datasets = Data.objects.all()
    all_scans = ScanResult.objects.all()
    today = date.today()  
    if year:
        today = date.today()    
        start_year = date(int(year), 1, 1)
        end_year = date(int(year), 12, 31)
        if today < end_year:
            end_year = today
        all_datasets = all_datasets.filter(created__gte=start_year).filter(created__lte=end_year)
        all_scans = all_scans.filter(created__gte=start_year).filter(created__lte=end_year)
    else: year = today.year
    beamlines = PublicBeamline.objects.using('public-web')
    exp_data = {}
    stat = {}
    for bl in Beamline.objects.all():
        if bl.name in [b.name for b in beamlines]:
            datasets = all_datasets.filter(beamline__exact=bl).filter(kind__exact=Data.DATA_TYPES.COLLECTION)
            scans = all_scans.filter(beamline__exact=bl)            
            exp_data[bl.name] = {}
            for type in ['exposure_time','wavelength','delta_angle','resolution','scan_attenuation']:
                if type == 'wavelength':
                    stat[type] = [data.energy() for data in datasets]
                elif type == 'scan_attenuation':
                    stat[type] = [scan.attenuation for scan in scans]
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
@cache_page(24*3600)
def stats_year(request, year):

    prov_list = _provinces.keys() + ['Other','No Matching MxLIVE Account']
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
    ostat = Stat.objects.using('public-web').exclude(mode__in=['NormalMode']).filter(start_date__lte=end_year, end_date__gte=start_year)
    mstat = Stat.objects.using('public-web').filter(mode__in=['FacilityRepair']).filter(start_date__lte=end_year, end_date__gte=start_year)
    datasets = Data.objects.filter(created__year=year)

    prod_dates = {}
    prod_stats = {}
    nlist = []
    olist = []
    xlist = [nlist, olist]
    unused = {}
    for x, xstat in enumerate([nstat, ostat]):
        for n in xstat: # Start making a list of all the normal shifts in the given time frame
            if n.start_date == n.end_date:
                for i in range(3):
                    if i >= n.first_shift and i <= n.last_shift: 
                        xlist[x].append([n.start_date,i,[None, None]])
            else:
                for i in range(3):
                    if i >= n.first_shift and n.start_date <= end_year: 
                        xlist[x].append([n.start_date,i,[None, None]])
                nextd = n.start_date + one_day
                while nextd < n.end_date and nextd <= end_year:
                    for i in range(3): 
                        xlist[x].append([nextd,i,[None, None]])
                    nextd += one_day
                for i in range(3):
                    if i <= n.last_shift and n.end_date <= end_year: 
                        xlist[x].append([n.end_date,i,[None, None]])
                 
    mshifts = []
    for m in mstat:
        if m.start_date == m.end_date:
            mshifts.extend([[m.start_date,i,[None, None]] if i >= m.first_shift and i <= m.last_shift else None for i in range(3)])
        else:
            mshifts.extend([[m.start_date,i,[None, None]] if i >= m.first_shift and m.start_date <= end_year else None for i in range(3)])
            nextd = m.start_date + one_day
            while nextd < m.end_date and nextd <= end_year:
                mshifts.extend([[nextd,i,[None, None]] for i in range(3)])
                nextd += one_day
            mshifts.extend([[m.end_date,i,[None, None]] if i <= m.last_shift and m.end_date <= end_year else None for i in range(3)])
        mshifts = [x for x in mshifts if x != None]
    
    num_shifts = [len(nlist)]
    
    for m in mshifts:
        if m in nlist: nlist.pop(nlist.index(m))

    num_shifts.append(len(nlist))
            
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
        'num_shifts': num_shifts,
        }, context_instance=RequestContext(request))
