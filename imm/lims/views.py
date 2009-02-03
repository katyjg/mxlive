from django.template.loader import get_template
from django.http import HttpResponse, Http404, HttpResponseRedirect
from django.contrib.auth.decorators import login_required
from django.shortcuts import get_object_or_404, render_to_response
from django.template import RequestContext
from django.contrib.contenttypes.models import ContentType


from objectlister import ObjectLister
from django import forms
from lims.models import *
from lims.forms import *
import messaging.models


ACTIVITY_LOG_LENGTH  = 10       
        
@login_required
def show_home(request):
    user_groups = [str(grp) for grp in request.user.groups.all()]
    if 'General User' in user_groups:
        project = request.user.get_profile()   
        msgs = request.user.inbox.all()[:10]
        msglist = ObjectLister(request, request.user.inbox)

        statistics = {
            'shipment': {
                    'draft': project.shipment_set.filter(status__exact=Shipment.STATES.DRAFT),
                    'outgoing': project.shipment_set.filter(status__exact=Shipment.STATES.OUTGOING),
                    'incoming': project.shipment_set.filter(status__exact=Shipment.STATES.INCOMING),
                    'received': project.shipment_set.filter(status__exact=Shipment.STATES.RECEIVED),
                    'closed': project.shipment_set.filter(status__exact=Shipment.STATES.CLOSED),                
                    },
            'experiment': {
                    'draft': project.experiment_set.filter(status__exact=Experiment.STATES.DRAFT),
                    'active': project.experiment_set.filter(status__exact=Experiment.STATES.ACTIVE),
                    'processing': project.experiment_set.filter(status__exact=Experiment.STATES.PROCESSING),
                    'paused': project.experiment_set.filter(status__exact=Experiment.STATES.PAUSED),
                    'closed': project.experiment_set.filter(status__exact=Experiment.STATES.CLOSED),                
                    },
                    
        }
        return render_to_response('project.html', {
            'project': project,
            'statistics': statistics,
            'inbox': msglist,
            'link':False,
            },
        context_instance=RequestContext(request))
    else:
        raise Http404
        
@login_required
def get_message(request, id):
    message = request.user.inbox.get(pk=id)
    message.status = messaging.models.Message.STATE.READ
    message.save()
    return render_to_response('message.html', {
        'message': message,
        })

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
    return render_to_response('shipping.html',{
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
    return render_to_response('samples.html', {
        'logs': project.activitylog_set.filter(content_type__in=log_set)[:ACTIVITY_LOG_LENGTH],
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
    return render_to_response('experiment.html',{
        'logs': project.activitylog_set.filter(content_type__in=log_set)[:ACTIVITY_LOG_LENGTH],
        },
        context_instance=RequestContext(request))

@login_required
def shipment_add_dewar(request, id):
    id = int(id)
    try:
        project = request.user.get_profile()
        shipment = project.shipment_set.get(pk=id)
    except:
        raise Http404
    dewars = project.dewar_set.filter( models.Q(shipment__isnull=True) | ~models.Q(shipment__exact=id) )
    form_info = {
        'title': 'Add Existing Dewar',
        'sub_title': 'Select existing dewars to add to shipment %s' % shipment.identity(),
        'action':  request.path,
        'target': 'entry-scratchpad',
    }
    if request.method == 'POST':
        form = DewarSelectForm(request.POST)
        form['dewars'].field.queryset = dewars
        if form.is_valid():
            changed = False
            for dewar_id in request.POST.getlist('dewars'):
                d = project.dewar_set.get(pk=dewar_id)
                d.shipment = shipment
                d.save()
                changed = True
            
            if changed:
                shipment.save()            
            form_info['message'] = '%d dewars have been successfully added' % len(request.POST.getlist('dewars'))           
            ActivityLog.objects.log_activity(
                project.pk,
                request.user.pk, 
                request.META['REMOTE_ADDR'],
                ContentType.objects.get_for_model(Shipment).id,
                shipment.pk, 
                str(shipment), 
                ActivityLog.TYPE.MODIFY,
                form_info['message']
                )
            request.user.message_set.create(message = form_info['message'])
            return render_to_response('refresh.html')
        else:
            return render_to_response('forms/form_base.html', {
                'info': form_info,
                'form': form, 
                })
    else:
        form = DewarSelectForm()
        form['dewars'].field.queryset = dewars
        return render_to_response('forms/form_base.html', {
            'info': form_info, 
            'form': form, 
            })


@login_required
def dewar_add_container(request, id):
    id = int(id)
    try:
        project = request.user.get_profile()
        dewar = project.dewar_set.get(pk=id)
    except:
        raise Http404
    containers = project.container_set.filter( models.Q(dewar__isnull=True) | ~models.Q(dewar__exact=id) )
    form_info = {
        'title': 'Add Existing Container',
        'sub_title': 'Select existing containers to add to dewar %s' % dewar.identity(),
        'action':  request.path,
        'target': 'entry-scratchpad',
    }
    if request.method == 'POST':
        form = ContainerSelectForm(request.POST)
        form['containers'].field.queryset = containers
        if form.is_valid():
            changed = False
            for container_id in request.POST.getlist('containers'):
                d = project.container_set.get(pk=container_id)
                d.dewar = dewar
                d.save()
                changed = True
            
            if changed:
                dewar.save()            
            form_info['message'] = '%d containers have been successfully added' % len(request.POST.getlist('containers'))           
            ActivityLog.objects.log_activity(
                project.pk,
                request.user.pk, 
                request.META['REMOTE_ADDR'],
                ContentType.objects.get_for_model(Dewar).id,
                dewar.pk, 
                str(dewar), 
                ActivityLog.TYPE.MODIFY,
                form_info['message']
                )
            request.user.message_set.create(message = form_info['message'])
            return render_to_response('refresh.html')
        else:
            return render_to_response('forms/form_base.html', {
                'info': form_info,
                'form': form, 
                })
    else:
        form = ContainerSelectForm()
        form['container'].field.queryset = containers
        return render_to_response('forms/form_base.html', {
            'info': form_info, 
            'form': form, 
            })


@login_required
def object_detail(request, id, model, template):
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
def create_object(request, model, form, template='forms/new_base.html'):
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
        restrict_to_project(frm, project)
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
                restrict_to_project(frm, project)
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
        restrict_to_project(frm, project)
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
        restrict_to_project(frm, project)
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
                restrict_to_project(frm, project)
                frm[field].field.widget.attrs['disabled'] = 'disabled'
                return render_to_response('forms/form_base.html', {
                    'info': form_info, 
                    'form': frm, 
                    })
            else:
                return render_to_response('refresh.html')
        else:
            return render_to_response('forms/form_base.html', {
                'info': form_info,
                'form': frm, 
                })
    else:
        frm = form(initial={'project': project.pk, field: related.pk})
        restrict_to_project(frm, project)
        frm[field].field.widget.attrs['disabled'] = 'disabled'
        return render_to_response('forms/form_base.html', {
            'info': form_info, 
            'form': frm, 
            })


@login_required
def project_object_list(request, model, template='lists/list_base.html', link=True, can_add=True):
    try:
        project = request.user.get_profile()
    except:
        raise Http404
    manager = getattr(project, model.__name__.lower()+'_set')
    ol = ObjectLister(request, manager)
    return render_to_response(template, {'ol': ol, 'link': link, 'can_add': can_add},
        context_instance=RequestContext(request)
    )

@login_required
def user_object_list(request, model, template='lists/list_base.html', link=True, can_add=True):
    manager = getattr(request.user, model.__name__.lower()+'_set')
    ol = ObjectLister(request, manager)
    return render_to_response(template, {'ol': ol,'link': link, 'can_add': can_add },
        context_instance=RequestContext(request)
    )


@login_required
def edit_object_inline(request, id, model, form, template='/forms/form_base.html'):
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
        restrict_to_project(frm, project)
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
            return render_to_response('refresh.html')
        else:
            return render_to_response(template, {
            'info': form_info, 
            'form' : frm, 
            })
    else:
        frm = form(instance=obj)
        restrict_to_project(frm, project)
        return render_to_response(template, {
        'info': form_info, 
        'form' : frm, 
        })
       
@login_required
def remove_object(request, id, model, field):
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
        if request.has_key('_confirmed'):
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
            return render_to_response('refresh.html')
        else:
            return render_to_response('refresh.html')
    else:
        return render_to_response('forms/confirm_action.html', {
            'info': form_info, 
            'id': obj.pk,
            'confirm_action': 'Remove %s' % object_type, 
            }, 
            context_instance=RequestContext(request))

