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

PLOT_WIDTH = 6
PLOT_HEIGHT = 4 
PLOT_DPI = 75
IMG_WIDTH = int(round(PLOT_WIDTH * PLOT_DPI))    

import matplotlib
import numpy
from matplotlib.figure import Figure
from matplotlib.backends.backend_agg import FigureCanvasAgg as FigureCanvas

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
    
    today = ddatetime.date.today()
    start_year = ddatetime.date(int(year), 1, 1)
    end_year = ddatetime.date(int(year), 12, 31)
    if today < end_year:
        end_year = today
    one_day = timedelta(days=1)
    one_shift = timedelta(hours=8)
    
    '''
    one_shift = timedelta(hours=8)
    start_time = datetime(month[1], month[0], 1)
    next_month = start_time + relativedelta(months=+1)
    num_shifts = 0
    while start_time < next_month:
        if data.filter(created__gt=start_time).filter(created__lt=start_time+one_shift).exists():
            num_shifts += 1
        start_time += one_shift
    return num_shifts
    '''
    
    
    
    shift_stats = {}
    shift_stats['users'] = {}
    all_datasets = Data.objects.filter(created__gte=start_year).filter(created__lte=end_year)
    visits = Visit.objects.using('cmcf-web').filter(start_date__lte=end_year).filter(end_date__gte=start_year)
    
    num_total_visits = visits.count()
    num_registered_visits = visits.exclude(proposal=None).count()
    
    beamlines = CMCFBeamline.objects.using('cmcf-web').exclude(name__exact='SIM-1')
    totals = {}
    for bl in beamlines:
        stats = {}
        _projs_checked = []
        props = Proposal.objects.using('cmcf-web').filter(pk__in=visits.values('proposal').distinct())
        bl_visits = visits.filter(beamline__exact=bl)
        for x in props:
            num_shifts = 0
            num_visits = 0
            group = '%s, %s' %(x.last_name, x.first_name.upper()[0])
            try:
                p = Project.objects.filter(user__last_name__exact=str(x.last_name)).filter(user__first_name__startswith=str(x.first_name)[0])[0]
                for k, v in provinces.items():
                    if str(p.province) in v:
                        country = p.city
                        prov = k
                        break
                    else: 
                        if p.country: country = '%s, %s' % ( p.city, p.country)
                        else: country = ''
                        prov = 'Other'
            except:
                p = None
                country = "-"
                prov = 'No Matching MxLIVE Account'
            if not stats.has_key(prov): stats[prov] = []
            for v in bl_visits.filter(proposal__exact=x):
                num_visits += 1
                # Add entries to vlist for each shift
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
            data = all_datasets.filter(project__exact=p).values('created').distinct()
            if data:
                num_used = 0
                '''
                _shifts_checked = []
                for d in data:
                    first_shift = datetime(d['created'].year, d['created'].month, d['created'].day)
                    if first_shift not in _shifts_checked and p not in _projs_checked:
                        _projs_checked.append(p)
                        _shifts_checked.append(first_shift)
                        for i in range(3):
                            if data.filter(created__gte=first_shift+(one_shift*(i-1))).filter(created__lte=first_shift+(one_shift*i)):
                                num_used += 1
                '''    
            if num_visits or num_used:
                stats[prov].append([group, x.proposal_id, prov, country, num_visits, num_shifts, num_used])
        shift_stats['users'][bl.name] = SortedDict([(k, stats[k]) for k in prov_list if stats.has_key(k)])
        totals[bl.name] = {}
        for p in prov_list:
            if shift_stats['users'][bl.name].has_key(p): 
                totals[bl.name][p] = [sum(k[5] for k in shift_stats['users'][bl.name][p]),sum(k[4] for k in shift_stats['users'][bl.name][p]) ]
    
    return render_to_response('stats/beamline_stats.html', {
        'year': int(year),
        'years': [int(today.year), int(year) +1, int(year) -1],
        'users': shift_stats['users'],
        'totals': totals,
        'visits': [num_total_visits, num_registered_visits],
        }, context_instance=RequestContext(request))
    


    
@admin_login_required
def stats_usage(request, year):

    start_year = ddatetime.date(int(year), 1, 1)
    end_year = ddatetime.date(int(year), 12, 31)
    today = ddatetime.date.today()
    if today < end_year:
        end_year = today
    one_day = timedelta(days=1)

    labels = ['Normal', 'Remote','Mail-In','Purchased Access','Maintenance','Unallocated']
    ldict = {'Normal': 0,
             'Remote': 1,
             'Mail-In': 2,
             'Purchased Access': 3,
             'Maintenance': 4,
             'Unallocated': 5}

    visits = Visit.objects.using('cmcf-web').filter(start_date__lte=end_year).filter(end_date__gte=start_year)
    vlist = {}
    total = {}
    months = {}
    bls = CMCFBeamline.objects.using('cmcf-web').exclude(name__exact='SIM-1')
    for bl in bls:
        vlist[bl.name] = {}
        total[bl.name] = [0]*6
        months[bl.name] = [0]*6
        for i, type in enumerate(labels):
            vlist[bl.name][type] = []
            months[bl.name][i] = [0]*end_year.month
                
    for v in visits:
        # Choose which dictionary key to use
        if v.remote: dkey = 'Remote'
        elif v.mail_in: dkey = 'Mail-In'
        elif v.purchased: dkey = 'Purchased Access'
        elif v.maintenance: dkey = 'Maintenance'
        else: dkey = 'Normal'
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
    nstat = Stat.objects.using('cmcf-web').filter(mode__in=['NormalMode']).filter(start_date__lte=end_year, end_date__gte=start_year)
    nmanstat = {}
    for n in nstat:
        nmanstat[n.start_date] = ['','','']
        if n.start_date == n.end_date:
            for i in range(3):
                if i >= n.first_shift and i <= n.last_shift: nmanstat[n.start_date][i] = 'N'
        else:
            for i in range(3):
                if i >= n.first_shift: nmanstat[n.start_date][i] = 'N'
            next = n.start_date + one_day
            while next < n.end_date:
                nmanstat[next] = ['N','N','N']
                next += one_day
            nmanstat[n.end_date] = ['','','']
            for i in range(3):
                if i <= n.last_shift: 
                    nmanstat[n.end_date][i] = 'N'

    nwebstat = WebStatus.objects.using('cmcf-web').filter(date__endswith=str(year))
    
    next_day = start_year
    while next_day <= end_year:
        for shift in range(3):
            if nmanstat.has_key(next_day):
                if nmanstat[next_day][shift] == 'N': nlist.append([next_day, shift])
            if [next_day, shift] not in nlist and nwebstat.filter(date__exact=next_day.strftime('%b/%d/%Y')).exists():
                ws = nwebstat.get(date__exact=next_day.strftime('%b/%d/%Y'))
                try:
                    if (shift == 0 and ws.status1[0] == 'N') or (shift == 1 and ws.status2[0] == 'N') or (shift==2 and ws.status3[0] == 'N'):
                        try:
                            if (shift == 0 and not ws.status1[1] == 'S') or (shift == 1 and not ws.status2[1] == 'S') or (shift == 2 and not ws.status3[1] == 'S'):
                                nlist.append([next_day, shift])
                        except:
                            nlist.append([next_day, shift])
                except:
                    pass
        next_day += one_day
    
    for bl in bls:
        for ns in nlist:
            sh = [k for k, v in vlist[bl.name].iteritems() if ns in v]
            if len(sh) == 1:
                total[bl.name][ldict[sh[0]]] += 1
                months[bl.name][ldict[sh[0]]][ns[0].month-1] +=1
            elif len(sh) == 0:
                total[bl.name][ldict['Unallocated']] += 1
                months[bl.name][ldict['Unallocated']][ns[0].month-1] +=1
    
    colors = ['#7DCF7D','#A2DDDD','#CCE3B5','#FFFF99','0.9','0.75']
    cols = {}
    plab = {}
    for bl in bls:
        cols[bl.name] = []  
        plab[bl.name] = []
        ind = [i for i, x in enumerate(total[bl.name]) if x == 0]
        total[bl.name][:] = [x for x in total[bl.name] if x != 0]
        for i in range(6):
            if i not in ind: 
                plab[bl.name].append(labels[i])
                cols[bl.name].append(colors[i])

    explode = [0.0, 0.15, 0.0, 0.0, 0.0, 0.0]
    def my_autopct(pct):
        tot=sum(total[bls[0].name])
        val=int(pct*tot/100.0)
        return '{p:.2f}% ({v:d})'.format(p=pct,v=val)
    
    matplotlib.rcParams['font.size'] = 15.0
    matplotlib.rcParams['font.weight'] = 600
    matplotlib.rcParams['text.color'] = '#555555'
    text_colors = ['0.2','0.5']
    fig = Figure(figsize=(PLOT_WIDTH*2, PLOT_WIDTH*2), dpi=PLOT_DPI)
    pip1 = fig.add_subplot(221)
    pip2 = fig.add_subplot(222)
    for i, pip in enumerate([pip1, pip2]):
        matplotlib.rcParams['text.color'] = text_colors[i]
        pip.set_title('%s - %s' % (str(year), bls[i].name))
        pip.pie(total[bls[i].name], explode=explode[:len(plab[bls[i].name])], 
             labels=plab[bls[i].name], colors=cols[bls[i].name], 
             autopct=my_autopct, pctdistance=0.6, labeldistance=1.1)
    matplotlib.rcParams['text.color'] = '#555555'   
    
    colLabels = ('Jan','Feb','Mar','Apr','May','Jun','Jul','Aug','Sep','Oct','Nov','Dec')
    rowLabels = ['Norm','Remo','MailIn','$PA','Maint','Open']
    rowLabels.reverse()
    hist1 = fig.add_subplot(223)    
    hist2 = fig.add_subplot(224)

    for i, hist in enumerate([hist1, hist2]):
        data = months[bls[i].name]
        rows = len(data)   
        ind = numpy.arange(end_year.month) + 0.25  # the x locations for the groups
        cellText = []
        width=0.5
        yoff = numpy.array([0.0] * end_year.month) # the bottom values for stacked bar chart
        #data.reverse()
        for row in xrange(rows):
            hist.bar(ind, data[row], width, bottom=yoff, color=colors[row])
            yoff = yoff + data[row]
            cellText.append(['%d' % x for x in data[row]])
        hist.set_title('%s - Beam Usage by Month (%s)' % (bls[i].name, str(year)))
        hist.set_ylabel('Shifts')
        hist.set_xticks([])
        colors.reverse()
        cellText.reverse()
        hist.table(cellText=cellText, rowLabels=rowLabels, rowLoc='right', rowColours=colors, colLabels=colLabels[:end_year.month], loc='bottom')
        colors.reverse()
    
    # make and return png image
    canvas = FigureCanvas(fig)
    response = HttpResponse(content_type='image/png')
    canvas.print_png(response)
    return response