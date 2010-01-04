from django.http import Http404, HttpResponseRedirect, HttpResponse
from django.contrib.auth.decorators import login_required
from django.shortcuts import render_to_response
from django.template import RequestContext
from django.views.decorators.cache import cache_page
from django.contrib.contenttypes.models import ContentType
from django.db import models

from imm.objlist.views import ObjectList
from imm.lims.models import *
from imm.lims.forms import ObjectSelectForm, DataForm

from jsonrpc import jsonrpc_method
try:
    import json
except:
    from django.utils import simplejson as json
    
ACTIVITY_LOG_LENGTH  = 10       
        
@login_required
def show_project(request):
    try:
        project = request.user.get_profile()
    except:
        raise Http404
    msglist = ObjectList(request, request.user.inbox)

    statistics = {
        'shipment': {
                'draft': project.shipment_set.filter(status__exact=Shipment.STATES.DRAFT), 
                'outgoing': project.shipment_set.filter(status__exact=Shipment.STATES.SENT),
                'incoming': project.shipment_set.filter(status__exact=Shipment.STATES.RETURNED),
                'received': project.shipment_set.filter(status__exact=Shipment.STATES.ON_SITE),
                'closed': project.shipment_set.filter(status__exact=Shipment.STATES.ARCHIVED),   
                },
        'experiment': {
                'draft': project.experiment_set.filter(status__exact=Experiment.STATES.DRAFT),
                'active': project.experiment_set.filter(status__exact=Experiment.STATES.ACTIVE),
                'processing': project.experiment_set.filter(status__exact=Experiment.STATES.PROCESSING),
                'paused': project.experiment_set.filter(status__exact=Experiment.STATES.PAUSED),
                'closed': project.experiment_set.filter(status__exact=Experiment.STATES.CLOSED),            
                },
                
    }
    return render_to_response('lims/project.html', {
        'project': project,
        'statistics': statistics,
        'inbox': msglist,
        'link':False,
        },
    context_instance=RequestContext(request))
        
@login_required
def shipping_summary(request):
    try:
        project = request.user.get_profile()
    except:
        raise Http404
    log_set = [
        ContentType.objects.get_for_model(Container).pk, 
        ContentType.objects.get_for_model(Dewar).pk,
        ContentType.objects.get_for_model(Shipment).pk,
    ]
    return render_to_response('lims/shipping.html',{
        'logs': project.activitylog_set.filter(content_type__in=log_set)[:ACTIVITY_LOG_LENGTH],
        'project': project,
        },
        context_instance=RequestContext(request))

@login_required
def sample_summary(request):
    try:
        project = request.user.get_profile()
    except:
        raise Http404
    log_set = [
        ContentType.objects.get_for_model(Crystal).pk,
        ContentType.objects.get_for_model(Constituent).pk,
        ContentType.objects.get_for_model(Cocktail).pk,
        ContentType.objects.get_for_model(CrystalForm).pk,
    ]
    return render_to_response('lims/samples.html', {
        'logs': project.activitylog_set.filter(content_type__in=log_set)[:ACTIVITY_LOG_LENGTH],
        'project': project,
        },
        context_instance=RequestContext(request))

@login_required
def experiment_summary(request):
    try:
        project = request.user.get_profile()
    except:
        raise Http404
    log_set = [
        ContentType.objects.get_for_model(Experiment).pk,
        #ContentType.objects.get_for_model(Results).pk,
    ]
    return render_to_response('lims/experiment.html',{
        'logs': project.activitylog_set.filter(content_type__in=log_set)[:ACTIVITY_LOG_LENGTH],
        'project': project,
        },
        context_instance=RequestContext(request))

@login_required
def add_existing_object(request, id, parent_model, model, field, form=ObjectSelectForm):
    """
    A generic view which displays a form of type ``form`` which when submitted 
    will set the foreign key field `field` of one/more existing objects of 
    type ``model`` to the related object of type `parent_model` identified by the 
    primary key ``id``.
    """
    id = int(id)
    try:
        project = request.user.get_profile()
        manager = getattr(project, model.__name__.lower()+'_set')
        parent_manager = getattr(project, parent_model.__name__.lower()+'_set')
    except:
        raise Http404
        
    parent = parent_manager.get(pk=id)    
    queryset = manager.filter(models.Q(**{'%s__isnull' % (field): True}) |
                              ~models.Q(**{'%s__exact' % (field): id}))
    object_type = model.__name__
    form_info = {
        'title': 'Add Existing %s' % (object_type),
        'sub_title': 'Select existing %ss to add to %s' % (object_type.lower(), parent),
        'action':  request.path,
        'target': 'entry-scratchpad',
    }
    if request.method == 'POST':
        frm = form(request.POST)
        frm['items'].field.queryset = queryset
        if frm.is_valid():
            changed = False
            for item_id in request.POST.getlist('items'):
                d = manager.get(pk=item_id)
                setattr(d, field, parent)
                d.save()
                changed = True
            
            if changed:
                parent.save()            
            form_info['message'] = '%d %ss have been successfully added' % (len(request.POST.getlist('items')), object_type.lower())         
            ActivityLog.objects.log_activity(
                project.pk,
                request.user.pk, 
                request.META['REMOTE_ADDR'],
                ContentType.objects.get_for_model(parent_model).id,
                parent.pk, 
                str(parent), 
                ActivityLog.TYPE.MODIFY,
                form_info['message']
                )
            request.user.message_set.create(message = form_info['message'])
            return render_to_response('lims/refresh.html')
        else:
            return render_to_response('objforms/form_base.html', {
                'info': form_info,
                'form': frm, 
                })
    else:
        frm = form()
        frm['items'].field.queryset = queryset
        return render_to_response('objforms/form_base.html', {
            'info': form_info, 
            'form': frm, 
            })


@login_required
def object_detail(request, id, model, template):
    """
    A generic view which displays a detailed page for an object of type ``model``
    identified by the primary key ``id`` using the template ``template``. 
    """
    try:
        project = request.user.get_profile()
        queryset = model.objects.all().filter(project__exact=project.pk)
        obj = queryset.get(pk=id)
    except:
        raise Http404
    return render_to_response(template, {
        'object': obj,
        },
        context_instance=RequestContext(request))


@login_required
def create_object(request, model, form, template='lims/forms/new_base.html'):
    """
    A generic view which displays a Form of type ``form`` using the Template
    ``template`` and when submitted will create a new object of type ``model``.
    """
    try:
        project = request.user.get_profile()
    except:
        raise Http404
    object_type = model.__name__
    form_info = {
        'title': 'New %s' % object_type,
        'action':  request.path,
        'add_another': True,
    }
    if request.method == 'POST':
        frm = form(request.POST)
        frm.restrict_by('project', project.pk)
        if frm.is_valid():
            new_obj = frm.save()
            info_msg = 'The %(name)s "%(obj)s" was added successfully.' % {'name': str(model._meta.verbose_name), 'obj': str(new_obj)}
            ActivityLog.objects.log_activity(
                project.pk,
                request.user.pk, 
                request.META['REMOTE_ADDR'],
                ContentType.objects.get_for_model(model).id,
                new_obj.pk, 
                str(new_obj), 
                ActivityLog.TYPE.CREATE,
                info_msg
                )
            request.user.message_set.create(message = info_msg)
            if request.POST.has_key('_addanother'):
                frm = form(initial={'project': project.pk})            
                frm.restrict_by('project', project.pk)
                return render_to_response(template, {
                    'info': form_info, 
                    'form': frm, 
                    }, 
                    context_instance=RequestContext(request))            
            else:
                return HttpResponseRedirect(request.path+'../%s/' % new_obj.pk)
        else:
            return render_to_response(template, {
                'info': form_info,
                'form': frm, 
                }, 
                context_instance=RequestContext(request))
    else:
        frm = form(initial={'project': project.pk})
        frm.restrict_by('project', project.pk)
        if request.GET.has_key('clone'):
            clone_id = request.GET['clone']
            try:
                manager = getattr(project, model.__name__.lower()+'_set')
                clone_obj = manager.get(pk=clone_id)
            except:
                info_msg = 'Could not clone %(name)s!' % {'name': str(model._meta.verbose_name)}
                request.user.message_set.create(message = info_msg)
            else:
                for name, field in frm.fields.items():
                    val = getattr(clone_obj, name)
                    if hasattr(val, 'pk'):
                        val = getattr(val, 'pk')
                    elif hasattr(val, 'all'):
                        val = [o.pk for o in val.all() ]
                    field.initial = val

        return render_to_response(template, {
            'info': form_info, 
            'form': frm, 
            }, 
            context_instance=RequestContext(request))


@login_required
def add_new_object(request, id, model, form, field):
    """
    A generic view which displays a form of type `form` which when submitted 
    will create a new object of type `model` and set it's foreign key field 
    `field` to the related object identified by the primary key `id`.
    """
    object_type = model.__name__
    try:
        project = request.user.get_profile()
        manager = getattr(project, field+'_set')
        related = manager.get(pk=id)
        related_type = related._meta.verbose_name
    except:
        raise Http404
    form_info = {
        'title': 'New %s' % object_type,
        'sub_title': 'Adding a new %s to %s "%s"' % (object_type, related_type, str(related)),
        'action':  request.path,
        'target': 'entry-scratchpad',
        'add_another': True,
    }
    if request.method == 'POST':
        q = request.POST.copy()
        q.update({field: related.pk})
        frm = form(q)
        frm[field].field.widget.attrs['disabled'] = 'disabled'
        frm.restrict_by('project', project.pk)
        if frm.is_valid():
            new_obj = frm.save()
            info_msg = '%s "%s" added to %s "%s"' % (object_type, str(new_obj), related_type, str(related))
            ActivityLog.objects.log_activity(
                project.pk,
                request.user.pk,
                request.META['REMOTE_ADDR'],
                ContentType.objects.get_for_model(model).id,
                new_obj.pk, 
                str(new_obj), 
                ActivityLog.TYPE.CREATE,
                info_msg
                )
            request.user.message_set.create(message = info_msg)
            if request.POST.has_key('_addanother'):
                frm = form(initial={'project': project.pk, field: related.pk})
                frm.restrict_by('project', project.pk)
                frm[field].field.widget.attrs['disabled'] = 'disabled'
                return render_to_response('objforms/form_base.html', {
                    'info': form_info, 
                    'form': frm, 
                    })
            else:
                return render_to_response('lims/refresh.html')
        else:
            return render_to_response('objforms/form_base.html', {
                'info': form_info,
                'form': frm, 
                })
    else:
        frm = form(initial={'project': project.pk, field: related.pk})
        frm.restrict_by('project', project.pk)
        frm[field].field.widget.attrs['disabled'] = 'disabled'
        return render_to_response('objforms/form_base.html', {
            'info': form_info, 
            'form': frm, 
            })


@login_required
def project_object_list(request, model, template='objlist/object_list.html', link=True, can_add=True):
    """
    A generic view which displays a list of objects of type ``model`` owned by
    the current users project. The list is displayed using the template
    `template`. 
    
    Keyworded options:
        - ``link`` (boolean) specifies whether or not to link each item to it's detailed page.
        - ``can_add`` (boolean) specifies whether or not new entries can be added on the list page.    
    """
    try:
        project = request.user.get_profile()
    except:
        raise Http404
    manager = getattr(project, model.__name__.lower()+'_set')
    ol = ObjectList(request, manager)
    return render_to_response(template, {'ol': ol, 'link': link, 'can_add': can_add},
        context_instance=RequestContext(request)
    )

@login_required
def user_object_list(request, model, template='lims/lists/list_base.html', link=True, can_add=True):
    """
    A generic view which displays a list of objects of type ``model`` owned by
    the current user. The list is displayed using the template
    ``template``. 
    
    Keyworded options
    -----------------
        - ``link`` (boolean) specifies whether or not to link each item to it's
           detailed page.
        - ``can_add`` (boolean) specifies whether or not new entries can be added
           on the list page.    
    """
    manager = getattr(request.user, model.__name__.lower()+'_set')
    ol = ObjectList(request, manager)
    return render_to_response(template, {'ol': ol,'link': link, 'can_add': can_add },
        context_instance=RequestContext(request)
    )


@login_required
def edit_object_inline(request, id, model, form, template='objforms/form_base.html'):
    """
    A generic view which displays a form of type ``form`` using the template 
    ``template``, for editing an object of type ``model``, identified by primary 
    key ``id``, which when submitted will update the entry asynchronously through
    AJAX.
    """
    try:
        project = request.user.get_profile()
        manager = getattr(project, model.__name__.lower()+'_set')
    except:
        raise Http404
    obj = manager.get(pk=id)
    form_info = {
        'title': 'Edit %s' % model.__name__,
        'sub_title': obj.identity(),
        'action':  request.path,
        'target': 'entry-scratchpad'
    }
    if request.method == 'POST':
        frm = form(request.POST, instance=obj)
        frm.restrict_by('project', project.pk)
        if frm.is_valid():
            frm.save()
            form_info['message'] = '%s %s successfully modified' % ( model.__name__, obj.identity())
            ActivityLog.objects.log_activity(
                project.pk,
                request.user.pk, 
                request.META['REMOTE_ADDR'],
                ContentType.objects.get_for_model(model).id,
                obj.pk, 
                str(obj), 
                ActivityLog.TYPE.MODIFY,
                form_info['message']
                )
            request.user.message_set.create(message = form_info['message'])
            return render_to_response('lims/refresh.html')
        else:
            return render_to_response(template, {
            'info': form_info, 
            'form' : frm, 
            })
    else:
        frm = form(instance=obj)
        frm.restrict_by('project', project.pk)
        return render_to_response(template, {
        'info': form_info, 
        'form' : frm, 
        })
       
@login_required
def remove_object(request, id, model, field):
    """
    A generic view which displays a confirmation form and if confirmed, will
    set the foreign key field ``field`` of the object of type ``model`` identified
    by primary key ``id`` to null. The model must have specified ``null=True`` as an
    option of the field.
    """
    try:
        project = request.user.get_profile()
        manager = getattr(project, model.__name__.lower()+'_set')
        obj = manager.get(pk=id)
    except:
        raise Http404
    object_type = model.__name__
    related = getattr(obj, field)
    related_type = related._meta.verbose_name
    
    form_info = {
        'title': 'Remove %s?' % object_type.lower(),
        'sub_title': 'The %s will become unassigned.' % object_type.lower(),
        'action':  request.path,
        'target': 'entry-scratchpad',
        'message': 'Are you sure you want to remove %s "%s" from %s "%s"?' % (
            object_type.lower(), 
            str(obj), 
            related_type.lower(), 
            str(related)
            )
    }
    if request.method == 'POST':
        if request.POST.has_key('_confirmed'):
            setattr(obj,field,None)
            obj.save()
            form_info['message'] = '%s "%s" removed from %s  "%s".' % (
                object_type, 
                str(obj), 
                related_type.lower(), 
                str(related)
                )
            ActivityLog.objects.log_activity(
                project.pk,
                request.user.pk, 
                request.META['REMOTE_ADDR'],
                ContentType.objects.get_for_model(model).id,
                obj.pk, 
                str(obj), 
                ActivityLog.TYPE.MODIFY,
                form_info['message']
                )
            request.user.message_set.create(message = form_info['message'])            
            return render_to_response('lims/refresh.html')
        else:
            return render_to_response('lims/refresh.html')
    else:
        return render_to_response('lims/forms/confirm_action.html', {
            'info': form_info, 
            'id': obj.pk,
            'confirm_action': 'Remove %s' % object_type, 
            }, 
            context_instance=RequestContext(request))


@jsonrpc_method('lims.add_data', authenticated=True)
def add_data(request, data_info):
    info = {}
    # convert unicode to str
    for k,v in data_info.items():
        info[str(k)] = v
    info.update({'project_id':1, 
                 'experiment_id':1, 
                 'crystal_id': 1})    
    try:
        new_obj = Data(**info)
        new_obj.save()
        return {'data_id': new_obj.pk}
    except Exception, e:
        raise e
        return {'error': str(e)}

@jsonrpc_method('lims.add_result', authenticated=True)
def add_result(request, res_info):
    info = {}
    # convert unicode to str
    for k,v in res_info.items():
        info[str(k)] = v
    info.update({'project_id':1, 
                 'experiment_id':1, 
                 'crystal_id': 1})  
    new_obj = Result(**info)
    new_obj.save()
    return {'result_id': new_obj.pk}

@jsonrpc_method('lims.add_strategy', authenticated=True)
def add_strategy(request, stg_info):
    info = {}
    # convert unicode to str
    for k,v in stg_info.items():
        info[str(k)] = v
    info.update({'project_id':1})  
    new_obj = Strategy(**info)
    new_obj.save()
    return {'strategy_id': new_obj.pk}

@login_required
@cache_page(60*3600)
def plot_shell_stats(request, id):
    from matplotlib.backends.backend_agg import FigureCanvasAgg as FigureCanvas
    from matplotlib.ticker import FormatStrFormatter, MultipleLocator, MaxNLocator
    from matplotlib.figure import Figure
    from matplotlib import rcParams
    
    # Adjust Legend parameters
    rcParams['legend.loc'] = 'best'
    rcParams['legend.fontsize'] = 10
    rcParams['legend.isaxes'] = False
    
    try:
        project = request.user.get_profile()
        result = project.result_set.get(pk=id)
    except:
        raise Http404
    # extract shell statistics to plot
    data = result.details['shell_statistics']
    fig = Figure(figsize=(5.6,5), dpi=72)
    ax1 = fig.add_subplot(211)
    ax1.plot(data['shell'], data['completeness'], 'r-+')
    ax1.set_ylabel('completeness (%)', color='r')
    ax11 = ax1.twinx()
    ax11.plot(data['shell'], data['r_meas'], 'g-', label='R-meas')
    ax11.plot(data['shell'], data['r_mrgdf'], 'g:+', label='R-mrgd-F')
    ax11.legend(loc='best')
    ax1.grid(True)
    ax11.set_ylabel('R-factors (%)', color='g')
    for tl in ax11.get_yticklabels():
        tl.set_color('g')
    for tl in ax1.get_yticklabels():
        tl.set_color('r')
    ax1.yaxis.set_major_formatter(FormatStrFormatter('%0.0f'))
    ax11.yaxis.set_major_formatter(FormatStrFormatter('%0.0f'))
    ax1.set_ylim((0, 105))
    ax11.set_ylim((0, 105))

    ax2 = fig.add_subplot(212, sharex=ax1)
    ax2.plot(data['shell'], data['i_sigma'], 'm-x')
    ax2.set_xlabel('Resolution Shell')
    ax2.set_ylabel('I/SigmaI', color='m')
    ax21 = ax2.twinx()
    ax21.plot(data['shell'], data['sig_ano'], 'b-+')
    ax2.grid(True)
    ax21.set_ylabel('SigAno', color='b')
    for tl in ax21.get_yticklabels():
        tl.set_color('b')
    for tl in ax2.get_yticklabels():
        tl.set_color('m')
    ax2.yaxis.set_major_formatter(FormatStrFormatter('%0.0f'))
    ax21.yaxis.set_major_formatter(FormatStrFormatter('%0.1f'))
    ax2.set_ylim((-5, max(data['i_sigma'])+5))
    ax21.set_ylim((0, max(data['sig_ano'])+1))


    canvas = FigureCanvas(fig)
    response = HttpResponse(content_type='image/png')
    canvas.print_png(response)
    return response
    

@login_required
@cache_page(60*3600)
def plot_diff_stats(request, id):
    from matplotlib.backends.backend_agg import FigureCanvasAgg as FigureCanvas
    from matplotlib.ticker import FormatStrFormatter, MultipleLocator, MaxNLocator
    from matplotlib.figure import Figure
    from matplotlib import rcParams
    
    # Adjust Legend parameters
    rcParams['legend.loc'] = 'best'
    rcParams['legend.fontsize'] = 10
    rcParams['legend.isaxes'] = False
    
    try:
        project = request.user.get_profile()
        result = project.result_set.get(pk=id)
    except:
        raise Http404
    # extract shell statistics to plot
    data = result.details['diff_statistics']
    fig = Figure(figsize=(5.6,5), dpi=72)
    ax1 = fig.add_subplot(311)
    ax1.plot(data['frame_diff'], data['rd'], 'r-')
    ax1.set_ylabel('R-d', color='r')
    ax11 = ax1.twinx()
    ax11.plot(data['frame_diff'], data['n_refl'], 'g-')
    ax1.grid(True)
    ax11.set_ylabel('# Reflections', color='g')
    for tl in ax11.get_yticklabels():
        tl.set_color('g')
    for tl in ax1.get_yticklabels():
        tl.set_color('r')
    ax1.yaxis.set_major_formatter(FormatStrFormatter('%0.2f'))
    ax11.yaxis.set_major_formatter(FormatStrFormatter('%0.0f'))
    #ax1.set_ylim((0, 105))
    #ax11.set_ylim((0, max(data['n_refl'])+5))

    ax2 = fig.add_subplot(312, sharex=ax1)
    ax2.plot(data['frame_diff'], data['rd_friedel'], 'm-')
    ax2.set_ylabel('R-d Friedel', color='m')
    ax21 = ax2.twinx()
    ax21.plot(data['frame_diff'], data['n_friedel'], 'b-')
    ax2.grid(True)
    ax21.set_ylabel('# Reflections', color='b')
    for tl in ax21.get_yticklabels():
        tl.set_color('b')
    for tl in ax2.get_yticklabels():
        tl.set_color('m')
    ax2.yaxis.set_major_formatter(FormatStrFormatter('%0.2f'))
    ax21.yaxis.set_major_formatter(FormatStrFormatter('%0.0f'))

    ax3 = fig.add_subplot(313, sharex=ax1)
    ax3.plot(data['frame_diff'], data['rd_non_friedel'], 'k-')
    ax3.set_xlabel('Frame Difference')
    ax3.set_ylabel('R-d Non-friedel', color='k')
    ax31 = ax3.twinx()
    ax31.plot(data['frame_diff'], data['n_non_friedel'], 'c-')
    ax3.grid(True)
    ax31.set_ylabel('# Reflections', color='c')
    for tl in ax31.get_yticklabels():
        tl.set_color('c')
    for tl in ax3.get_yticklabels():
        tl.set_color('k')
    ax3.yaxis.set_major_formatter(FormatStrFormatter('%0.2f'))
    ax31.yaxis.set_major_formatter(FormatStrFormatter('%0.0f'))

    canvas = FigureCanvas(fig)
    response = HttpResponse(content_type='image/png')
    canvas.print_png(response)
    return response

@login_required
@cache_page(60*3600)
def plot_frame_stats(request, id):
    from matplotlib.backends.backend_agg import FigureCanvasAgg as FigureCanvas
    from matplotlib.ticker import FormatStrFormatter, MultipleLocator, MaxNLocator
    from matplotlib.figure import Figure
    from matplotlib import rcParams
    
    # Adjust Legend parameters
    rcParams['legend.loc'] = 'best'
    rcParams['legend.fontsize'] = 10
    rcParams['legend.isaxes'] = False
    
    try:
        project = request.user.get_profile()
        result = project.result_set.get(pk=id)
    except:
        raise Http404
    # extract shell statistics to plot
    data = result.details['frame_statistics']
    fig = Figure(figsize=(5.6,5), dpi=72)
    ax1 = fig.add_subplot(311)
    ax1.plot(data['frame'], data['scale'], 'r-')
    ax1.set_ylabel('Scale Factor', color='r')
    ax11 = ax1.twinx()
    ax11.plot(data['frame'], data['mosaicity'], 'g-')
    ax1.grid(True)
    ax11.set_ylabel('Mosaicity', color='g')
    for tl in ax11.get_yticklabels():
        tl.set_color('g')
    for tl in ax1.get_yticklabels():
        tl.set_color('r')
    ax1.yaxis.set_major_formatter(FormatStrFormatter('%0.1f'))
    ax11.yaxis.set_major_formatter(FormatStrFormatter('%0.2f'))
    ax1.set_ylim((min(data['scale'])-0.2, max(data['scale'])+0.2))
    ax11.set_ylim((min(data['mosaicity'])-0.01, max(data['mosaicity'])+0.01))

    ax2 = fig.add_subplot(312, sharex=ax1)
    ax2.plot(data['frame'], data['divergence'], 'm-')
    ax2.set_ylabel('Divergence', color='m')
    ax21 = ax2.twinx()
    ax21.plot(data['frame'], data['i_sigma'], 'b-')
    ax2.grid(True)
    ax21.set_ylabel('I/Sigma(I)', color='b')
    for tl in ax21.get_yticklabels():
        tl.set_color('b')
    for tl in ax2.get_yticklabels():
        tl.set_color('m')
    ax2.yaxis.set_major_formatter(FormatStrFormatter('%0.3f'))
    ax21.yaxis.set_major_formatter(FormatStrFormatter('%0.1f'))
    ax2.set_ylim((min(data['divergence'])-0.02, max(data['divergence'])+0.02))

    ax3 = fig.add_subplot(313, sharex=ax1)
    ax3.plot(data['frame'], data['r_meas'], 'k-')
    ax3.set_xlabel('Frame Number')
    ax3.set_ylabel('R-meas', color='k')
    ax31 = ax3.twinx()
    ax31.plot(data['frame'], data['unique'], 'c-')
    ax3.grid(True)
    ax31.set_ylabel('Unique Reflections', color='c')
    for tl in ax31.get_yticklabels():
        tl.set_color('c')
    for tl in ax3.get_yticklabels():
        tl.set_color('k')
    ax3.yaxis.set_major_formatter(FormatStrFormatter('%0.3f'))
    ax31.yaxis.set_major_formatter(FormatStrFormatter('%0.0f'))

    canvas = FigureCanvas(fig)
    response = HttpResponse(content_type='image/png')
    canvas.print_png(response)
    return response
