from datetime import datetime, timedelta, date
from dateutil.relativedelta import relativedelta
import calendar
import logging
import subprocess
import tempfile
import os
import shutil
import sys
import xlrd
from shutil import copyfile

from django.http import Http404, HttpResponseRedirect, HttpResponse
from django.contrib.auth.decorators import login_required

from django.conf import settings

from django.shortcuts import render_to_response, get_object_or_404
from django.template import RequestContext
from django.template import loader
from django.db import transaction
from django.db.models import Q
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

from imm.lims.models import *
from imm.staff.models import Runlist
from imm.objlist.views import ObjectList
from imm.lims.models import Container, Experiment, Shipment, Crystal
from imm.download.models import SecurePath
from imm.download.maketarball import create_tar

#sys.path.append(os.path.join('/var/website/cmcf-website/cmcf'))
#from scheduler.models import Visit, Stat, WebStatus
#from scheduler.models import Beamline as CMCFBeamline

ACTIVITY_LOG_LENGTH  = 10 

@login_required
def staff_home(request):
    if not request.user.is_superuser:
        return HttpResponseRedirect(reverse('project-home'))
    
    recent_start = datetime.now() - timedelta(days=7)
    last_login = ActivityLog.objects.last_login(request)
    if last_login is not None:
        if last_login.created < recent_start:
            recent_start = last_login.created       

    statistics = {
        'shipments': {
                'outgoing': Shipment.objects.filter(status__exact=Shipment.STATES.SENT).count(),
                'incoming': Shipment.objects.filter(status__exact=Shipment.STATES.RETURNED).count(),
                'on_site': Shipment.objects.filter(status__exact=Shipment.STATES.ON_SITE).count(),
                },
        'dewars': {
                'outgoing': Dewar.objects.filter(status__exact=Dewar.STATES.SENT).count(),
                'incoming': Dewar.objects.filter(status__exact=Dewar.STATES.RETURNED).count(),
                'on_site': Dewar.objects.filter(status__exact=Dewar.STATES.ON_SITE).count(),
                },
        'experiments': {
                'active': Experiment.objects.filter(status__exact=Experiment.STATES.ACTIVE).filter(pk__in=Crystal.objects.filter(status__in=[Crystal.STATES.ON_SITE, Crystal.STATES.LOADED]).values('experiment')).count(),
                'processing': Experiment.objects.filter(status__exact=Experiment.STATES.PROCESSING).filter(pk__in=Crystal.objects.filter(status__exact=Crystal.STATES.ON_SITE).values('experiment')).count(),
                },
        'crystals': {
                'on_site': Crystal.objects.filter(status__in=[Crystal.STATES.ON_SITE, Crystal.STATES.LOADED]).count(),
                'outgoing': Crystal.objects.filter(status__exact=Crystal.STATES.SENT).count(),
                'incoming': Crystal.objects.filter(status__exact=Crystal.STATES.RETURNED).count(),
                },
        'runlists':{
                'loaded': Runlist.objects.filter(status__exact=Runlist.STATES.LOADED).count(),
                'completed': Runlist.objects.filter(status__exact=Runlist.STATES.COMPLETED, modified__gte=recent_start).count(),
                'start_date': recent_start,
        },                
    }
    

    return render_to_response('lims/staff.html', {
        'activity_log': ObjectList(request, ActivityLog.objects),
        'feedback': Feedback.objects.all()[:5],
        'statistics': statistics,
        'handler': request.path,
        }, context_instance=RequestContext(request))
    
@admin_login_required
@transaction.commit_on_success
def receive_shipment(request, id, model, form, template='objforms/form_base.html', action=None):
    """
    """
    save_label = None
    if action:
        save_label = action[0].upper() + action[1:]
        
    form_info = {
        'title': 'Receive Dewar',
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
                if action == 'receive':
                    obj.receive(request)
            form_info['message'] = '%s %s successfully received' % ( model.__name__, obj.identity())
            request.user.message_set.create(message = form_info['message'])           
            return render_to_response("lims/redirect.html", context_instance=RequestContext(request)) 
        else:
            return render_to_response(template, {
            'info': form_info, 
            'form' : frm, 
            }, context_instance=RequestContext(request))
    else:
        try:
            obj = model.objects.get(pk=id)
            init_dict = {'barcode': 'CLS%04i-%04i' % (obj.pk, obj.shipment.pk)}
            if not obj.storage_location:
                init_dict['storage_location'] = 'CMCF 1608.7'
        except:
            obj = None
            init_dict = dict(request.GET.items())
        frm = form(instance=obj, initial=init_dict)
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
        if destination.__name__ == 'Runlist':
            if object.__name__ == 'Experiment':
                container_list = Container.objects.filter(status__exact=Container.STATES.ON_SITE).filter(pk__in=Experiment.objects.get(pk=obj_id).crystal_set.values('container')).exclude(pk__in=dest.containers.all()).exclude(kind__exact=Container.TYPE.CANE)
                for container in container_list:
                    dest.add_container(container)
                    try:
                        current = getattr(dest, 'containers')
                        current.add(container)
                    except AttributeError:
                        message = '%s has not been added. No Field (tried %s and %s)' % (display_name, lookup_name, '%ss' % lookup_name)
                        request.user.message_set.create(message = message)
                        return render_to_response('lims/refresh.html', context_instance=RequestContext(request))
                
        if loc_id:
            added = dest.container_to_location(to_add, loc_id)
            dest.container_to_location(to_add, loc_id)
            if added:
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
def experiment_basic_object_list(request, runlist_id, model, template='objlist/basic_object_list.html'):
    """
    Should display name and id for entity, but filter
    to only display experiments with containers with unprocessed crystals available to add to a runlist.
    """
    basic_list = list()
    ol = ObjectList(request, request.manager)
    try: 
        runlist = Runlist.objects.get(pk=runlist_id)
    except:
        runlist = None

    if runlist:
        ol.object_list = Experiment.objects.filter(status__in=[Experiment.STATES.ACTIVE, Experiment.STATES.PROCESSING]).filter(pk__in=Crystal.objects.filter(container__pk__in=Container.objects.filter(status__exact=Container.STATES.ON_SITE).exclude(pk__in=runlist.containers.all()).exclude(kind__exact=Container.TYPE.CANE)).values('experiment'))
    
    return render_to_response(template, {'ol': ol, 'type': ol.model.__name__.lower() }, context_instance=RequestContext(request))


@login_required
@manager_required
def container_basic_object_list(request, runlist_id, exp_id, model, template='objlist/basic_object_list.html'):
    """
    Slightly more complex than above. Should display name and id for entity, but filter
    to only display containers with a crystal in the specified experiment.
    """
    active_containers = None
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

    if runlist and experiment:
        ol.object_list = Container.objects.filter(status__exact=Container.STATES.ON_SITE).filter(pk__in=(experiment.crystal_set.all().values('container'))).exclude(pk__in=runlist.containers.all()).exclude(kind__exact=Container.TYPE.CANE)
    elif runlist:
        ol.object_list = Container.objects.filter(status__exact=Container.STATES.ON_SITE).exclude(pk__in=runlist.containers.all()).exclude(kind__exact=Container.TYPE.CANE)
    return render_to_response(template, {'ol': ol, 'type': ol.model.__name__.lower() }, context_instance=RequestContext(request))

CACHE_DIR = getattr(settings, 'DOWNLOAD_CACHE_DIR', '/tmp')

import threading

@login_required
def object_status(request, model):
    pks = map(int, request.POST.getlist('id_list[]'))
    action = int(request.POST.get('action'))
    if model is Crystal:
        experiment = Crystal.objects.get(pk=pks[0]).experiment
        for crystal in Crystal.objects.filter(pk__in=pks):
            if action == 1:
                crystal.change_screen_status(Crystal.EXP_STATES.PENDING) 
            elif action == 2:
                crystal.change_collect_status(Crystal.EXP_STATES.PENDING) 
            elif action == 3:
                crystal.change_screen_status(Crystal.EXP_STATES.IGNORE) 
                crystal.change_collect_status(Crystal.EXP_STATES.IGNORE) 
            elif action == 4:
                crystal.change_screen_status(Crystal.EXP_STATES.COMPLETED)
            elif action == 5: 
                crystal.change_collect_status(Crystal.EXP_STATES.COMPLETED) 
                
        if experiment.is_complete():
            experiment.change_status(Experiment.STATES.COMPLETE)
        else:
            if experiment.status == Experiment.STATES.COMPLETE:
                if experiment.result_set.exists() or experiment.data_set.exists():
                    experiment.change_status(Experiment.STATES.PROCESSING)
                else:
                    experiment.change_status(Experiment.STATES.ACTIVE)

    if model is Data:
        threads = {}
        for data in Data.objects.filter(pk__in=pks):
            if action == 1:
                path_obj = get_object_or_404(SecurePath, key=data.url)
                tar_file = os.path.join(CACHE_DIR, path_obj.key, '%s.tar.gz' % (data.name))
                if not os.path.exists(tar_file):
                    try:
                        threads[data.name] = threading.Thread(target=create_tar, 
                                                              args=[path_obj.path, tar_file],
                                                              kwargs={'data_dir':True})
                        threads[data.name].start()
                        msg = "A tar file is being created for dataset %s.  Depending on the number of images, it may be awhile before it is available to download." % data.name
                        request.user.message_set.create(message = msg)
                    except OSError:
                        raise Http404 
                data.toggle_download(True)
            if action == 2:
                msg = "The tar file has been deleted for dataset %s." % data.name
                obj = get_object_or_404(SecurePath, key=data.url)
                file = os.path.join(CACHE_DIR, obj.key, '%s.tar.gz' % data.name)
                if os.path.exists(file):
                    os.remove(file)
                elif os.path.exists('%s-tmp' % file):
                    os.remove('%s-tmp' % file)
                else:
                    msg = "The tar file for dataset %s could not be removed because it does not exist." % data.name
                request.user.message_set.create(message = msg)
                data.toggle_download(False)
            
    return render_to_response('lims/refresh.html')

@admin_login_required
@transaction.commit_on_success
def staff_action_object(request, id, model, form, template='objforms/form_base.html', action=None):
    try:
        obj = model.objects.get(pk=id)
    except:
        raise Http404

    save_label = None
    save_labeled = None
    if action:
        save_label = action[0].upper() + action[1:]
        if save_label[-1:] == 'e': save_labeled = '%sd' % save_label
        else: 
            save_labeled = '%sed' % save_label      
            if action == 'send': save_labeled = 'sent'
    form_info = {
        'title': '%s %s "%s"?' % (save_label, model.__name__, model.objects.get(pk=id).name),
        'sub_title': 'The %s will be marked as %s' % ( model._meta.verbose_name, save_labeled),
        'action':  request.path,
        'save_label': save_label }

    if action:
        if action == 'review':
            form_info['message'] = 'Are you sure no further tests of %s "%s" are necessary?' % (
            model.__name__.lower(), model.objects.get(pk=id).name)
            if not obj.is_complete():
                form.warning_message = "There are crystals in this experiment that have not been processed according to the experiment plan."
            else:
                form.warning_message = None
        if action == 'load':
            form_info['message'] = 'Verify that this runlist has been loaded into the automounter.'
        if action == 'unload':
            form_info['message'] = 'Verify that the runlist has been unloaded from the automounter.'

    if request.method == 'POST':
        frm = form(request.POST, instance=obj)
        if request.POST.has_key('_save'):
            if action:
                if action == 'review': obj.review(request=request)
                if action == 'load': obj.load(request=request)
                if action == 'unload': 
                    obj.unload(request=request)
                    request.user.message_set.create(message = 'Runlist (%s) unloaded from %s automounter' % (obj.name, obj.beamline))
                    url_name = "staff-%s-list" % (model.__name__.lower()) 
                    return render_to_response("lims/redirect.json", {'redirect_to': reverse(url_name),}, context_instance=RequestContext(request), mimetype="application/json")   
            return render_to_response('lims/refresh.html')
        else:
            return render_to_response(template, {
            'info': form_info, 
            'form' : frm, 
            }, context_instance=RequestContext(request))
    else:   
        form._meta.model = Experiment
        frm = form(initial=dict(request.GET.items()))
        return render_to_response(template, {
        'info': form_info, 
        'form' : frm, 
        }, context_instance=RequestContext(request))



# -------------------------- JSONRPC Methods ----------------------------------------#
from jsonrpc import jsonrpc_method
from jsonrpc.exceptions import InvalidRequestError
from jsonrpc.exceptions import MethodNotFoundError
from imm.apikey.views import apikey_required
from django.db import models

@jsonrpc_method('lims.get_onsite_samples')
@apikey_required
def get_onsite_samples(request, info):
    try:
        project = Project.objects.get(name__exact=info.get('project_name'))
    except Project.DoesNotExist:
        raise InvalidRequestError("Project does not exist.")
    
    cnt_list = project.container_set.filter(
        models.Q(status__exact=Container.STATES.ON_SITE) | 
        models.Q(status__exact=Container.STATES.LOADED))
    xtl_list = project.crystal_set.filter(
        models.Q(status__exact=Crystal.STATES.ON_SITE) | 
        models.Q(status__exact=Crystal.STATES.LOADED)).order_by('priority')
    exp_list = project.experiment_set.filter(
        models.Q(status__exact=Experiment.STATES.ACTIVE) | 
        models.Q(status__exact=Experiment.STATES.PROCESSING) |
        models.Q(status__exact=Experiment.STATES.COMPLETE)) 
    containers = {}
    crystals = {}
    experiments = {}
    rl_dict = {}
    
    if info.get('beamline_name') is not None:
        try:
            beamline = Beamline.objects.get(name__exact=info['beamline_name'])
            active_runlist = beamline.runlist_set.get(status=Runlist.STATES.LOADED)
            rl_dict = active_runlist.json_dict()
        except Beamline.DoesNotExist:
            raise InvalidRequestError("Beamline does not exist.")
        except Runlist.DoesNotExist:
            pass
        except Runlist.MultipleObjectsReturned:
            raise ServerError("Expected only one object. Found many.")

    for cnt_obj in cnt_list:
        if cnt_obj.pk in rl_dict.get('containers', {}):
            containers[str(cnt_obj.pk)] = rl_dict['containers'][cnt_obj.pk]
        else:
            containers[str(cnt_obj.pk)] = cnt_obj.json_dict()
    for xtl_obj in xtl_list:
        crystals[str(xtl_obj.pk)] = xtl_obj.json_dict()
    for exp_obj in exp_list:
        experiments[str(exp_obj.pk)] = exp_obj.json_dict()

           
    return {'containers': containers, 'crystals': crystals, 'experiments': experiments}

@jsonrpc_method('lims.get_active_runlist')
@apikey_required
def get_active_runlist(request, info):
    if info.get('beamline_name') is not None:
        try:
        # should only be one runlist per beamline
            beamline = Beamline.objects.get(name__exact=info['beamline_name'])
            active_runlist = beamline.runlist_set.get(status=Runlist.STATES.LOADED)
            return active_runlist.json_dict()
        except Beamline.DoesNotExist:
            raise InvalidRequestError("Beamline does not exist.")
        except Runlist.DoesNotExist:
            pass
        except Runlist.MultipleObjectsReturned:
            raise ServerError("Expected only one runlist. Found many.")
    else:
          raise InvalidRequestError("A valid beamline name must be provided.")  


