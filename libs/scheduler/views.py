from django.shortcuts import render_to_response
from django.template import RequestContext
from django.core.urlresolvers import reverse
from django.contrib.auth.decorators import user_passes_test
from django.contrib.auth import REDIRECT_FIELD_NAME
from django.utils.encoding import smart_str
from django.core.management import call_command
from django.contrib import messages

from datetime import datetime, date, timedelta, time

import string
from django.conf import settings

from scheduler.models import Visit, Stat, OnCall, SupportPerson, Beamline, Proposal

WARNING = "This is a last-minute change. It will take a few moments to send a notification e-mail to the Users Office and to beamline staff."

def staff_login_required(function=None, redirect_field_name=REDIRECT_FIELD_NAME):
    """
    Decorator for views that checks that the user is logged in, redirecting
    to the log-in page if necessary.
    """
    actual_decorator = user_passes_test(
        lambda u: u.is_authenticated() and u.is_staff,
        redirect_field_name=redirect_field_name
    )
    if function:
        return actual_decorator(function)
    return actual_decorator

def staff_calendar(request, day=None, template='scheduler/admin_schedule_week.html'):
    return current_week(request, day, template, staff=True)

@staff_login_required
def admin_scheduler(request, day=None, template='scheduler/admin_schedule_week.html'):
    return current_week(request, day, template, staff=True, admin=True, title="Beamtime Scheduler")

@staff_login_required
def edit_visit(request, pk, model, form, template='wp-root.html'):
    form_info = {'title': 'Edit Beamline Visit',
                 'action':  reverse('bl-edit-visit', args=[pk]),
                 'save_label': 'Save',
                 'enctype' : 'multipart/form-data',
                 }
    today = datetime.now().date()
    this_monday = today - timedelta(days=datetime.now().date().weekday())
    next_monday = this_monday + timedelta(days=7)
    etime = datetime(this_monday.year, this_monday.month, this_monday.day, 13, 30)
    
    visit = Visit.objects.get(pk__exact=pk)
    mod_msg = ''
    if request.method == 'POST':
        if visit.start_date <= next_monday and visit.start_date >= today:
            for field in ['proposal', 'start_date', 'end_date', 'first_shift', 'last_shift', 'beamline']:
                if str(request.POST.get(field, None)) != str(visit.__dict__[((field == 'proposal' or field == 'beamline') and '%s_id' % field) or field]):
                    msg = string.capwords(field.replace('_', ' '))
                    mod_msg = mod_msg and '%s AND %s' % (mod_msg, msg) or msg
        firstdate = visit.start_date
        frm = form(request.POST, instance=visit)
        if frm.is_valid():
            frm.save()
            if mod_msg and visit.modified > etime:
                mod_msg = firstdate != visit.start_date and 'This change affects %s and %s' % (firstdate.strftime('%a, %b %d'), visit.start_date.strftime('%a, %b %d')) or 'Changed %s' % mod_msg
                call_command('notify', visit.pk, 'MODIFIED: ', mod_msg) 
            message =  '%(name)s modified' % {'name': smart_str(model._meta.verbose_name)}
            messages.add_message(request, messages.INFO, message)
            return render_to_response('scheduler/refresh.html', context_instance=RequestContext(request))
        else:
            return render_to_response(template, {
            'info': form_info, 
            'form' : frm, 
            }, context_instance=RequestContext(request))
    else:
        form.warning_message = (visit.start_date <= next_monday and visit.start_date >= today and datetime.now() > etime and  WARNING) or None
        frm = form(instance=visit, initial=dict(request.GET.items())) # casting to a dict pulls out first list item in each value list
        return render_to_response(template, {
        'info': form_info, 
        'form' : frm,
        }, context_instance=RequestContext(request))
    
@staff_login_required
def delete_object(request, pk, model, form, template='wp-root.html'):
    obj = model.objects.get(pk__exact=pk)
    
    form_info = {        
        'title': 'Delete %s?' % obj,
        'sub_title': 'The %s (%s) will be deleted' % ( model._meta.verbose_name, obj),
        'action':  request.path,
        'message': 'Are you sure you want to delete this visit?',
        'save_label': 'Delete'
        }
    if request.method == 'POST':
        frm = form(request.POST, instance=obj)
        if frm.is_valid():
            message =  '%(name)s deleted' % {'name': smart_str(model._meta.verbose_name)}
            obj.delete()
            messages.add_message(request, messages.INFO, message)
            return render_to_response('scheduler/refresh.html', context_instance=RequestContext(request))
        else:
            return render_to_response(template, {
            'info': form_info, 
            'form' : frm, 
            }, context_instance=RequestContext(request))
    else:
        print obj, type(obj), obj.pk,  dict(request.GET.items())
        frm = form(instance=obj, initial=dict(request.GET.items())) # casting to a dict pulls out first list item in each value list
        return render_to_response(template, {
            'info': form_info, 
            'form' : frm,
            }, context_instance=RequestContext(request))
    

@staff_login_required
def add_object(request, model, form, template='wp-root.html'):
    """
    A view which displays a Form of type ``form`` using the Template
    ``template`` and when submitted will create a new object of type ``model``.
    """
    form_info = {'title': 'Add New %s' % model.__name__,
                 'action':  request.path,
                 'save_label': 'Submit',
                 'enctype' : 'multipart/form-data',
                 }
    today = datetime.now().date()
    this_monday = today - timedelta(days=datetime.now().date().weekday())
    next_monday = this_monday + timedelta(days=7)
    etime = datetime(this_monday.year, this_monday.month, this_monday.day, 13, 30)

    if request.method == 'POST':
        frm = form(request.POST)
        if frm.is_valid():
            new_obj = frm.save()
            if model in [Visit, Stat]:
                start_date = new_obj.start_date or request.POST.get('start_date')
                first_shift = int(new_obj.first_shift) or int(request.POST.get('first_shift'))
                ns = int(request.POST.get('num_shifts'))
                extra_shifts = ( ns - ( 3 - first_shift ))
                extra_days = extra_shifts/3 + ( bool(extra_shifts%3) and 1 or 0 )
                end_date = datetime.strptime(str(start_date), '%Y-%m-%d') + timedelta(days=extra_days)
                
                new_obj.start_date = start_date
                new_obj.first_shift = first_shift
                new_obj.last_shift = ( first_shift + ns - 1 ) % 3                  
                new_obj.end_date = end_date.date()
                new_obj.save()
                if model == Visit:
                    if new_obj.start_date <= next_monday and new_obj.start_date >= today and new_obj.modified > etime:
                        dates = '%s%s' % (new_obj.start_date.strftime('%A, %b %d'), new_obj.start_date != new_obj.end_date and (' - %s' % new_obj.end_date.strftime('%A, %b %d')) or '')  
                        call_command('notify', new_obj.pk, 'ADDED: ', 'This change affects %s' % dates)
            message =  'New %(name)s added' % {'name': smart_str(model._meta.verbose_name)}
            messages.add_message(request, messages.INFO, message)
            return render_to_response('scheduler/refresh.html', context_instance=RequestContext(request))
        else:
            return render_to_response(template, {
                'info': form_info,
                'form': frm,
                }, context_instance=RequestContext(request))
    else:
        frm = form(initial=request.GET.items())
        if model in [Visit, Stat]:
            start_date = datetime.strptime(str(request.GET.get('start_date')), '%Y-%m-%d').date()
            if model == Visit:
                form.warning_message = (start_date <= next_monday and start_date >= today and datetime.now() > etime and WARNING) or None
        return render_to_response(template, {
            'info': form_info, 
            'form': frm, 
            }, context_instance=RequestContext(request))


def get_one_week(dt=None):
    if dt is None:
        dt = datetime.now().date()
        
    # start on first day of week
    wk_dt = dt - timedelta(days=dt.weekday())
    week = [wk_dt]
    for i in range(6):
        week.append( wk_dt + timedelta(days=i+1) )
    return week
        
def combine_shifts(shifts, ids=False):
    new_shifts = [[],[],[]]
    for shift in shifts:
        for i in range(3):
            if shift[i] is not None:
                if new_shifts[i] and (new_shifts[i] == ['FacilityRepair'] or shift[i] == 'FacilityRepair') : new_shifts[i][0] += ' '+shift[i]
                if not new_shifts[i]: new_shifts[i].append(shift[i])
    if not ids:
        for i in range(3):
            new_shifts[i] = ','.join(new_shifts[i])
    return new_shifts

def current_week(request, day=None, template='scheduler/schedule_week.html', admin=False, staff=False, title=''):
    today = datetime.now()
    if day is not None:
        dt = datetime.strptime(day, '%Y-%m-%d').date()
    else:
        dt = today.date()
    
    this_wk = get_one_week(dt)
    prev_wk_day = (dt + timedelta(weeks=-1)).strftime('%Y-%m-%d')
    next_wk_day = (dt + timedelta(weeks=1)).strftime('%Y-%m-%d')
    shift = ( today.time() < time(8) and 2 ) or ( today.time() > time(16) and 1 ) or 0 
    if shift == 2: today = today - timedelta(days=1)

    calendar = []    
    bl_keys = []
    bl_week = {}
    beamlines = Beamline.objects.all()
    week_personnel = OnCall.objects.week_occurences(dt)
    modes = Stat.objects.filter(start_date__lte=this_wk[-1],end_date__gte=this_wk[0]).order_by('-pk')

    for bl in beamlines:
        bl_week[bl.name] = bl.visit_set.week_occurences(dt)
        bl_keys.append(bl.name)
    
    for day in this_wk:
        key = day.strftime('%a %b/%d')
        shifts = {}
        date = day.strftime('%Y-%m-%d')
        
        mode_shifts = []
        beammode = []
        for current_mode in modes:
            beammode.append(current_mode.get_shifts(day))
        beammode = [m for m in beammode if m != [None, None, None]]
        mode_shifts.append(combine_shifts(beammode))
        for blkey, blvis in bl_week.items():
            shifts[blkey] = []

            for vis in blvis:
                shifts[blkey].append(vis.get_shifts(day, True))

        day_shifts = []
        for blkey in bl_keys:
            day_shifts.append(combine_shifts(shifts[blkey], True))

        on_call = [o for o in week_personnel if o.date == day]
        mode_day = []

        calendar.append((key, day_shifts, on_call, mode_shifts, mode_day, date))

    return render_to_response(
        template, 
        {
            'beamlines': beamlines,
            'calendar':  calendar,
            'next_week': next_wk_day,
            'prev_week': prev_wk_day,
            'admin':     admin,
            'staff':     staff,
            'today':    [(today).strftime('%a %b/%d'), shift],
            'title':    title,
        },
        context_instance=RequestContext(request),
    )
    
def contact_legend(request):
    support_list = []
    for person in SupportPerson.objects.all():
            support_list.append(person)

    return render_to_response(     
   	'contacts/contact_legend.html', 
        {'contact_list': support_list},
        )

def contact_list(request):
    support_list = []
    categories = []
    for category in SupportPerson.STAFF_CHOICES:
        categories.append(category)
    for person in SupportPerson.objects.all():
            support_list.append(person)

    return render_to_response(     
   	'contacts/contact_list.html', 
        {
            'contact_list': support_list,
            'categories': categories,
        },
        )

def get_shift_breakdown(request, start, end, template=''):
    """ args 'start' and 'end' should be datetime objects """
    start = date(int(start.split('-')[0]),int(start.split('-')[1]),int(start.split('-')[2]))
    end = date(int(end.split('-')[0]),int(end.split('-')[1]),int(end.split('-')[2]))
    bls = Beamline.objects.all()
    info = {}
    for bl in bls:
        visits = Visit.objects.filter(start_date__lte=end).filter(end_date__gte=start).filter(beamline=bl)
        base = []
        info[bl] = []
        for u in visits.values('proposal').distinct():
            types = []
            if visits.filter(proposal=u['proposal']).filter(mail_in=True).exists():
                types.append('Mail-In')
            if visits.filter(proposal=u['proposal']).filter(remote=True).exists():
                types.append('Remote')
            if visits.filter(proposal=u['proposal']).filter(purchased=True).exists():
                types.append('Purchased')
            if visits.filter(proposal=u['proposal']).filter(maintenance=True).exists():
                types.append('Maintenance')
            if visits.filter(proposal=u['proposal']).filter(maintenance=False).filter(mail_in=False).filter(remote=False).filter(purchased=False).exists():
                types.append('Normal')
            base.append((Proposal.objects.get(pk=u['proposal']),[vis.get_visit_shifts() for vis in visits.filter(proposal=u['proposal'])], types))
        for entry in base:
            shifts = []
            for sh in entry[1]:
                for s in sh:
                    if '24:00 - 08:00' in s:
                        d = datetime.strptime(s[:17],'%a, %b %d, %Y') + timedelta(days=1)
                        s = '%s - 00:00 - 08:00' % ( d.strftime('%a, %b %d, %Y'))
                    shifts.append(s)
            info[bl].append((entry[0], shifts, entry[2]))

    return render_to_response('scheduler/shift_breakdown.html',     
            { 'info': info,
              'date': (start, end),
            }, context_instance=RequestContext(request))
