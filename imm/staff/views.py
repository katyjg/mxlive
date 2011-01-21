import logging

from django.http import HttpResponseRedirect
from django.contrib.auth.decorators import login_required

from django.conf import settings

from django.shortcuts import render_to_response
from django.template import RequestContext
from django.db import transaction
from django.contrib.contenttypes.models import ContentType
from django.core.urlresolvers import reverse
from django.http import HttpRequest
from django.utils.datastructures import MultiValueDict
from django.http import Http404
from django.utils.encoding import smart_str

from imm.lims.views import admin_login_required
from imm.lims.views import manager_required
from imm.lims.views import object_list

from imm.staff.admin import runlist_site

from imm.lims.models import FilterManagerWrapper
from imm.lims.models import DistinctManagerWrapper
from imm.lims.models import perform_action
from imm.lims.models import ActivityLog
from imm.lims.models import Crystal
from imm.lims.models import Container
from imm.staff.models import Runlist
from imm.staff.models import AutomounterLayout
from imm.objlist.views import ObjectList
from imm.lims.models import Container, Experiment

from jsonrpc import jsonrpc_method
from jsonrpc.exceptions import InvalidRequestError
from jsonrpc.exceptions import MethodNotFoundError

ACTIVITY_LOG_LENGTH  = 10 

@login_required
def staff_home(request):
    if not request.user.is_superuser:
        return HttpResponseRedirect(reverse('project-home'))
    
    return render_to_response('lims/staff.html', {
        'activity_log': ObjectList(request, ActivityLog.objects),
        'handler': request.path,
        }, context_instance=RequestContext(request))
    
@admin_login_required
@manager_required
def runlist_summary(request, model=ActivityLog):
    log_set = [
        ContentType.objects.get_for_model(Runlist).pk, 
    ]
    return render_to_response('staff/runlist.html',{
        'logs': request.manager.filter(content_type__in=log_set)[:ACTIVITY_LOG_LENGTH],
        'request': request,
        },
        context_instance=RequestContext(request))
    
@admin_login_required
@transaction.commit_on_success
def receive_shipment(request, model, form, template='objforms/form_base.html', action=None):
    """
    """
    save_label = None
    if action:
        save_label = action[0].upper() + action[1:]
        
    form_info = {
        'title': 'Receive Shipment/Dewar',
        'action':  request.path,
        'save_label': save_label,
    }
    if request.method == 'POST':
        frm = form(request.POST)
        if frm.is_valid(): # frm.instance will be populated here
            frm.save()
            obj = frm.instance
            # if an action ('send', 'close') is specified, the perform the action
            if action:
                perform_action(obj, action)
            form_info['message'] = '%s %s successfully received' % ( model.__name__, obj.identity())
            ActivityLog.objects.log_activity(
                obj.project.pk,
                request.user.pk, 
                request.META['REMOTE_ADDR'],
                ContentType.objects.get_for_model(model).id,
                obj.pk, 
                smart_str(obj), 
                ActivityLog.TYPE.MODIFY,
                form_info['message']
                )
            request.user.message_set.create(message = form_info['message'])
            
            
            return render_to_response("lims/message.html", context_instance=RequestContext(request)) 
            #return HttpResponseRedirect(reverse('staff-shipment-list'))
        else:
            return render_to_response(template, {
            'info': form_info, 
            'form' : frm, 
            }, context_instance=RequestContext(request))
    else:
        frm = form(initial=dict(request.GET.items()))
        return render_to_response(template, {
        'info': form_info, 
        'form' : frm, 
        }, context_instance=RequestContext(request))
        
@login_required
@manager_required
def runlist_object_list(request, model, form, parent_model=None, link_field=None, template='objlist/object_list.html', 
                        link=True, can_add=False, can_upload=False, can_receive=False, can_prioritize=False, redirect=None,
                        instructions=None):
    """
    """
    model_str = model.__name__.lower() # ie. 'experiment' or 'container'
    parent_model_str = None
    if parent_model:
        parent_model_str = parent_model.__name__.lower() # ie. 'experiment' or 'container'
    
    if request.method == 'POST':
        data = MultiValueDict()
        data.update(request.GET)
        data.update(request.POST)
        frm = form(data)
        if frm.is_valid():
            objects = [(model_str, o.pk) for o in frm.cleaned_data[model_str]]
            if parent_model:
                objects += [(parent_model_str, o.pk) for o in frm.cleaned_data[parent_model_str]]
            return HttpResponseRedirect(reverse(redirect) + '?' + '&'.join(['%s=%d' % (o[0], o[1]) for o in objects]))
    else:
        if model_str in request.GET or parent_model_str in request.GET:
            frm = form(request.GET)
        else:
            frm = form()
        frm.fields[model_str].required = False

    manager = request.manager
    if parent_model:
        # use the forms.ModelForm interface to do the querying for us
        parents = frm.fields[parent_model_str].widget.value_from_datadict(frm.data, frm.files, frm.add_prefix(parent_model_str))
        parents = frm.fields[parent_model_str].clean(parents)
        # now fetch the children
        links = [l for p in parents for l in getattr(p, link_field + 's').all()]
        manager = FilterManagerWrapper(model.objects, **{link_field + '__in': links})
        manager = DistinctManagerWrapper(manager)
        request.GET = {} 
        
    ol = ObjectList(request, manager, admin_site=runlist_site)
        
    return render_to_response(template, {'ol': ol, 
                                         'link': link, 
                                         'form': frm,
                                         'can_add': can_add, 
                                         'can_upload': can_upload, 
                                         'can_receive': can_receive, 
                                         'can_prioritize': can_prioritize,
                                         'instructions': instructions,
                                         'handler' : request.path
                                         },
        context_instance=RequestContext(request)
    )
    
@login_required
def runlist_create_object(request, model, form, template='lims/forms/new_base.html'):
    """
    A generic view which displays a Form of type ``form`` using the Template
    ``template`` and when submitted will create a new object of type ``model``.
    """
    object_type = model.__name__
    form_info = {
        'title': 'New %s' % object_type,
        'action':  request.path,
        'add_another': True,
    }
    
    if request.method == 'POST':
        frm = form(request.POST)
        if frm.is_valid():
            auto = AutomounterLayout()
            auto.save()
            runlist = Runlist(automounter=auto, name=frm.cleaned_data['name'], comments=frm.cleaned_data['comments'])
            runlist.save()
            request.user.message_set.create(message = 'New Runlist created.')
            return render_to_response('lims/message.html', context_instance=RequestContext(request))
            #return HttpResponseRedirect(request.path+'../../%s/' % new_obj.pk)
        
    else:
        # pull args like foo=1&foo=2  (singular) and insert them into the form filed 'foos' (plural)
        data = MultiValueDict()
        for field in form().fields:
            if field.endswith('s') and field[:-1] in request.GET:
                data.setlist(field, request.GET.getlist(field[:-1]))
        frm = form(initial=data)
        
    return render_to_response(template, {
        'info': form_info, 
        'form': frm, 
        }, 
        context_instance=RequestContext(request))
    
@login_required
@transaction.commit_on_success
def add_existing_object(request, dest_id, obj_id, destination, object, src_id=None, loc_id=None, source=None, replace=False, reverse=False):
    """
    New add method. Meant for AJAX, so only intended to be POST'd to. This will add an object of type 'object'
    and id 'obj_id' to the object of type 'destination' with the id of 'dest_id'.
    Replace means if the field already has an item in it, replace it, else fail
    Reverse means, due to model layout, you are actually adding destination to object
    """
    object_type = destination.__name__
    form_info = {
        'title': 'Add Existing %s' % (object_type),
        'sub_title': 'Select existing %ss to add to %s' % (object_type.lower(), object),
        'action':  request.path,
        'target': 'entry-scratchpad',
    }
    if request.method != 'POST':
        raise Http404

    model = destination;
    manager = model.objects
    request.project = None
    if not request.user.is_superuser:
        try:
            project = request.user.get_profile()
            request.project = project
            manager = FilterManagerWrapper(manager, project__exact=project)
        except Project.DoesNotExist:
            raise Http404    

    model = object;
    obj_manager = model.objects
    request.project = None
    if not request.user.is_superuser:
        try:
            project = request.user.get_profile()
            request.project = project
            obj_manager = FilterManagerWrapper(obj_manager, project__exact=project)
        except Project.DoesNotExist:
            raise Http404    

#    #project = request.project
#    try:
#        # get all items of the type we want to add to
#        manager = getattr(project, destination.__name__.lower()+'_set')
#        obj_manager = getattr(project, object.__name__.lower()+'_set')
#        
#    except: 
#        raise Http404
#    
    #get just the items we want
    try:
        dest = manager.get(pk=dest_id)
        to_add = obj_manager.get(pk=obj_id)
    except:
        raise Http404

    # get the display name
    display_name = to_add.name
    if reverse:
        display_name = dest.name
        
    lookup_name = object.__name__.lower()
    
    if dest.is_editable():
        if loc_id:
            dest.automounter.container_to_location(to_add, loc_id)
            if dest.automounter.container_to_location(to_add, loc_id):
                try:
                    current = getattr(dest, '%ss' % lookup_name)
                    # want destination.objects.add(to_add)
                    current.add(to_add)
                    #setattr(dest, '%ss' % object.__name__.lower(), current_values)
                except AttributeError:
                    message = '%s has not been added. No Field (tried %s and %s)' % (display_name, lookup_name, '%ss' % lookup_name)
                    request.user.message_set.create(message = message)
                    return render_to_response('lims/refresh.html', context_instance=RequestContext(request))
            else:
                message = '%s has not been added. Location %s is unavailable.' % (display_name, loc_id)
                request.user.message_set.create(message = message)
                return render_to_response('lims/refresh.html', {
                    'context': RequestContext(request), 
                    'info': form_info,
                    })
                


        message = '%s has been successfully added' % display_name
        dest._activity_log = {
            'message': message,
            'ip_number': request.META['REMOTE_ADDR'],
            'action_type': ActivityLog.TYPE.MODIFY,}
        dest.save()
    else:
        message = '%s has not been added, as %s is not editable' % (display_name, dest.name)

    request.user.message_set.create(message = message)
    return render_to_response('lims/refresh.html', {
        'context': RequestContext(request), 
        'info': form_info,
        })


@login_required
@manager_required
def container_basic_object_list(request, runlist_id, exp_id, model, template='objlist/basic_object_list.html'):
    """
    Slightly more complex than above. Should display name and id for entity, but filter
    to only display containers with a crystal in the specified experiments.
    """
    active_containers = None
    experiment_list = None
    
    ol = ObjectList(request, request.manager)
    try: 
        runlist = Runlist.objects.get(pk=runlist_id)
    except:
        runlist = None

    try:
        experiment = Experiment.objects.get(pk=exp_id)
    except:
        experiment = None
        ol.object_list = None

    if runlist != None:
        container_list = []
        for container in Container.objects.all():
            exp_list = container.get_experiment_list()
            for exp in exp_list:
                if experiment == exp:
                    container_list.append(container)
        # currently selected containers
        active_containers = runlist.containers
    
    """ only want containers that pass experiment check. """
    if container_list != None:
        if active_containers.count != 0:
            #ol.object_list = Container.objects.filter(crystal__experiment=experiment).distinct().exclude(id__in=active_containers.all())#.remove(active_containers) 
            ol.object_list = container_list
        else:
            ol.object_list = Container.objects.filter(crystal__experiment=experiment).distinct()
            ol.object_list = container_list
    return render_to_response(template, {'ol': ol, 'type': ol.model.__name__.lower() }, context_instance=RequestContext(request))

@jsonrpc_method('lims.detailed_runlist', authenticated=getattr(settings, 'AUTH_REQ', True))
def detailed_runlist(request, runlist_id):
    try:
        runlist = Runlist.objects.get(pk=runlist_id)
    except Runlist.DoesNotExist:
        raise MethodNotFoundError("Runlist does not exist.")
 #   if runlist.status != Runlist.STATES.LOADED:
 #       raise InvalidRequestError("Runlist is not loaded.")
    
    return runlist.json_dict()

@jsonrpc_method('lims.get_active_runlist',  authenticated=getattr(settings, 'AUTH_REQ', True), safe=True)
def get_active_runlist(request):
    try:
        # should only be one runlist loaded at a time
        runlist = Runlist.objects.get(status=Runlist.STATES.LOADED)
    except Runlist.DoesNotExist:
        # can't just except, need to return no runlist found.
        return 'None'
    except Runlist.MultipleObjectsReturned:
        # too many runlists are considered loaded
        return 'Too many'
    
    return runlist.json_dict()
        
