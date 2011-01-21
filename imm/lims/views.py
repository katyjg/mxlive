import datetime
import subprocess
import tempfile
import os
import shutil
import sys
import xlrd

from django.conf import settings

from django.http import Http404, HttpResponseRedirect, HttpResponse
from django.contrib.auth.decorators import login_required, user_passes_test
from django.contrib.auth.models import User
from django.shortcuts import render_to_response
from django.template import RequestContext
from django.views.decorators.cache import cache_page
from django.contrib.contenttypes.models import ContentType
from django.db import models
from django.db.models import Max
from django.core.urlresolvers import reverse
from django.db import transaction
from django.db import IntegrityError
from django.template import loader
from django.contrib.auth import REDIRECT_FIELD_NAME
from django.utils.datastructures import MultiValueDict
from django.utils.encoding import smart_str

import logging

from imm.objlist.views import ObjectList
from imm.lims.models import *
from imm.staff.models import Runlist
from imm.lims.forms import ObjectSelectForm, DataForm
from imm.lims.excel import LimsWorkbook, LimsWorkbookExport
from imm.download.views import create_download_key 
from imm.remote.user_api import UserApi
  
#from imm.remote.user_api import UserApi

import jsonrpc
from jsonrpc import jsonrpc_method
try:
    import json
except:
    from django.utils import simplejson as json


 
ACTIVITY_LOG_LENGTH  = 6       


def get_ldap_user_info(username):
    """
    Get the ldap record for user identified by 'username'.
    """
    
    import ldap
    l = ldap.initialize(settings.LDAP_SERVER_URI)
    flt = settings.LDAP_SEARCH_FILTER % username
    result = l.search_s(settings.LDAP_SEARCHDN,
                ldap.SCOPE_SUBTREE, flt)
    if len(result) != 1:
        raise ValueError("More than one entry found for 'username'")
    return result[0]

def admin_login_required(function=None, redirect_field_name=REDIRECT_FIELD_NAME):
    """
    Decorator for views that checks that the user is logged in, redirecting
    to the log-in page if necessary.
    """
    actual_decorator = user_passes_test(
        lambda u: u.is_authenticated() and u.is_superuser,
        redirect_field_name=redirect_field_name
    )
    if function:
        return actual_decorator(function)
    return actual_decorator

def create_project(user=None, username=None, fetcher=None):
    if user is None:
        # find out if we have a user by the same username in LDAP and create a new one.
        if username is None:
            raise ValueError('"username" must be provided if "user" is not given.')
        userinfo = get_ldap_user_info(username)[1]
        user = User(username=username, password=userinfo['userPassword'][0])
        user.last_name = userinfo['cn'][0].split()[0]
        user.first_name  =  userinfo['cn'][0].split()[-1]
        user.save()
                   
    try:
        project = user.get_profile()
        
    except Project.DoesNotExist:
        project = Project(user=user, name=user.username)
        project.save()
    
    return project
    


def project_required(function):
    """ Decorator that enforces the existence of a imm.lims.models.Project """
    def project_required_wrapper(request, *args, **kwargs):
        try:
            project = request.user.get_profile()
            request.project = project
            return function(request, *args, **kwargs)
        except Project.DoesNotExist:
            raise Http404
    return project_required_wrapper

MANAGER_FILTERS = {
    (Shipment, True) : {'status__in': [Shipment.STATES.SENT, Shipment.STATES.ON_SITE, Shipment.STATES.RETURNED]},
    (Shipment, False) : {'status__in': [Shipment.STATES.DRAFT, Shipment.STATES.SENT, Shipment.STATES.ON_SITE, Shipment.STATES.RETURNED]},
    (Dewar, True) : {'status__in': [Dewar.STATES.SENT, Dewar.STATES.ON_SITE, Dewar.STATES.RETURNED]},
    (Dewar, False) : {'status__in': [Dewar.STATES.DRAFT, Dewar.STATES.SENT, Dewar.STATES.ON_SITE, Dewar.STATES.RETURNED]},
    (Container, True) : {'status__in': [Container.STATES.SENT, Container.STATES.ON_SITE, Container.STATES.LOADED, Container.STATES.RETURNED]},
    (Container, False) : {'status__in': [Container.STATES.DRAFT, Container.STATES.SENT, Container.STATES.ON_SITE, Container.STATES.LOADED, Container.STATES.RETURNED]},
    (Crystal, True) : {'status__in': [Crystal.STATES.SENT, Crystal.STATES.ON_SITE, Crystal.STATES.LOADED, Crystal.STATES.RETURNED]},
    (Crystal, False) : {'status__in': [Crystal.STATES.DRAFT, Crystal.STATES.SENT, Crystal.STATES.ON_SITE, Crystal.STATES.LOADED, Crystal.STATES.RETURNED]},
    (Experiment, True) : {'status__in': [Experiment.STATES.ACTIVE, Experiment.STATES.PROCESSING, Experiment.STATES.PAUSED]},
    (Experiment, False) : {'status__in': [Experiment.STATES.DRAFT, Experiment.STATES.ACTIVE, Experiment.STATES.PROCESSING, Experiment.STATES.PAUSED, Experiment.STATES.CLOSED]},
}

# models.Manager ordering is overridden by admin.ModelAdmin.ordering in the ObjectList
# framework (when specified). Ensure that admin.py does not conflict with these settings.
MANAGER_ORDER_BYS = {}

def manager_required(function):
    """ Decorator that enforces the existence of a model.Manager """
    def manager_required_wrapper(request, *args, **kwargs):
        tmp = []
        for arg in args:
            try:
                if issubclass(arg, models.Model):
                    tmp.append(arg)
            except TypeError:
                pass
        if tmp:
            model = tmp[0]
        else:
            model = kwargs['model']
        manager = model.objects
        request.project = None
        if not request.user.is_superuser:
            try:
                project = request.user.get_profile()
                request.project = project
                if model != Project:
                    manager = FilterManagerWrapper(manager, project__exact=project)
                else:
                    manager = FilterManagerWrapper(manager, pk__exact=project.pk)
            except Project.DoesNotExist:
                raise Http404
        if MANAGER_FILTERS.has_key((model, request.user.is_superuser)):
            manager = FilterManagerWrapper(manager,**MANAGER_FILTERS[(model, request.user.is_superuser)])
        if MANAGER_ORDER_BYS.has_key((model, request.user.is_superuser)):
            manager = OrderByManagerWrapper(manager,*MANAGER_ORDER_BYS[(model, request.user.is_superuser)])
        request.manager = manager
        assert isinstance(request.manager, models.Manager)
        return function(request, *args, **kwargs)
    return manager_required_wrapper

def project_assurance(function):
    """ Decorator that creates a default imm.lims.models.Project if there isn't one """
    def project_assurance_wrapper(request, fetcher=None):
        try:
            request.user.get_profile() # test for existence of the project 
        except Project.DoesNotExist:
            request.project = create_project(request.user, fetcher=fetcher)
        return function(request)
    return project_assurance_wrapper

@login_required
def home(request):
    """ The /home/ page selects and redirects the user to either
      1. /lims/ - for users
      2. /staff/ - for staff
    """
    if request.user.is_superuser:
        return HttpResponseRedirect(reverse('staff-home'))
    else:
        return HttpResponseRedirect(reverse('project-home'))
        
@login_required
@project_assurance
@project_required
def show_project(request):
    project = request.project

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
        'activity_log': ObjectList(request, project.activitylog_set),
        'handler' : request.path,
        },
    context_instance=RequestContext(request))
 
@login_required
@project_required
@transaction.commit_on_success
def upload_shipment(request, model, form, template='lims/forms/new_base.html'):
    """A generic view which displays a Form of type ``form`` using the Template
    ``template`` and when submitted will create new data using the LimsWorkbook
    class
    """
    project = request.project
    object_type = model.__name__
    form_info = {
        'title': 'Upload %s' % object_type,
        'action':  request.path,
        'add_another': False,
        'save_label': 'Upload',
        'enctype' : 'multipart/form-data',
    }
    if request.method == 'POST':
        frm = form(request.POST, request.FILES)
        if frm.is_valid():
            
            # saving valid data to the database can fail if duplicates are found. in this case
            # we need to manually rollback the transaction and return a normal rendered form error
            # to the user, rather than a 500 page
            try:
                frm.save(request)
                request.user.message_set.create(message = "The data was uploaded correctly.")
                return render_to_response("lims/message.html", context_instance=RequestContext(request))

            except IntegrityError:
                transaction.rollback()
                frm.add_excel_error('This data has been uploaded already')
                return render_to_response(template, {'form': frm, 'info': form_info}, context_instance=RequestContext(request))
        else:
            return render_to_response(template, {'form': frm, 'info': form_info}, context_instance=RequestContext(request))
    else:
        frm = form(initial={'project': project.pk})
        return render_to_response(template, {'form': frm, 'info': form_info}, context_instance=RequestContext(request))

@login_required
@manager_required
def shipping_summary(request, model=ActivityLog):
    log_set = [
        ContentType.objects.get_for_model(Container).pk, 
        ContentType.objects.get_for_model(Dewar).pk,
        ContentType.objects.get_for_model(Shipment).pk,
    ]
    return render_to_response('lims/shipping.html',{
        'logs': request.manager.filter(content_type__in=log_set)[:ACTIVITY_LOG_LENGTH],
        'project': request.project,
        'request': request,
        },
        context_instance=RequestContext(request))

@login_required
@manager_required
def sample_summary(request, model=ActivityLog):
    log_set = [
        ContentType.objects.get_for_model(Crystal).pk,
        ContentType.objects.get_for_model(Constituent).pk,
        ContentType.objects.get_for_model(Cocktail).pk,
        ContentType.objects.get_for_model(CrystalForm).pk,
    ]
    return render_to_response('lims/samples.html', {
        'logs': request.manager.filter(content_type__in=log_set)[:ACTIVITY_LOG_LENGTH],
        'project': request.project,
        'request': request,
        },
        context_instance=RequestContext(request))

@login_required
@manager_required
def experiment_summary(request, model=ActivityLog):
    log_set = [
        ContentType.objects.get_for_model(Experiment).pk,
    ]
    return render_to_response('lims/experiment.html',{
        'logs': request.manager.filter(content_type__in=log_set)[:ACTIVITY_LOG_LENGTH],
        'project': request.project,
        'request': request,
        },
        context_instance=RequestContext(request))
    
@login_required
@manager_required
def container_summary(request, model=ActivityLog):
    log_set = [
        ContentType.objects.get_for_model(Container).pk,
        ContentType.objects.get_for_model(Crystal).pk,
    ]
    return render_to_response('lims/container.html',{
        'logs': request.manager.filter(content_type__in=log_set)[:ACTIVITY_LOG_LENGTH],
        'project': request.project,
        'request': request,
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

    if reverse:
        # swap obj and destination
        obj_id, dest_id = dest_id, obj_id
        object, destination = destination, object

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
    if lookup_name == 'crystalform':
        lookup_name = 'crystal_form'
    
    if dest.is_editable():
        #if replace == True or dest.(object.__name__.lower()) == None
        try:
            getattr(dest, lookup_name)
            setattr(dest, lookup_name, to_add)
        except AttributeError:
            # attrib didn't exist, append 's' for many field
            try:
                current = getattr(dest, '%ss' % lookup_name)
                # want destination.objects.add(to_add)
                current.add(to_add)
                #setattr(dest, '%ss' % object.__name__.lower(), current_values)
            except AttributeError:
                message = '%s has not been added. No Field (tried %s and %s)' % (display_name, lookup_name, '%ss' % lookup_name)
                request.user.message_set.create(message = message)
                return render_to_response('lims/refresh.html', context_instance=RequestContext(request))
                
        if loc_id:
            setattr(dest, 'container_location', loc_id)

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
@project_required
@transaction.commit_on_success
def add_existing_object_old(request, src_id, dest_id, obj_id, parent_model, model, field, additional_fields=None, form=ObjectSelectForm):
    """
    A generic view which displays a form of type ``form`` which when submitted 
    will set the foreign key field `field` of one/more existing objects of 
    type ``model`` to the related object of type `parent_model` identified by the 
    primary key ``id``.
    """
    
    id = int(obj_id)
    project = request.project
    try:
        manager = getattr(project, model.__name__.lower()+'_set')
        parent_manager = getattr(project, parent_model.__name__.lower()+'_set')
        parent = parent_manager.get(pk=id)
    except:
        raise Http404
        
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
            if parent.is_editable():
                item_id = obj_id
                d = manager.get(pk=item_id)
                setattr(d, field, parent)
                for additional_field in additional_fields or []:
                    setattr(d, additional_field, frm.cleaned_data[additional_field])
                d.save()
                changed = True
                
            if changed:
                parent.save()            
                form_info['message'] = '%ss has been successfully added' % object_type.lower()
            else:
                form_info['message'] = '%ss has not been added, as the destination is not editable' %  object_type.lower()        
            ActivityLog.objects.log_activity(
                project.pk,
                request.user.pk, 
                request.META['REMOTE_ADDR'],
                parent, 
                ActivityLog.TYPE.MODIFY,
                form_info['message']
                )
            request.user.message_set.create(message = form_info['message'])
            return render_to_response('lims/refresh.html', context_instance=RequestContext(request))
        else:
            return render_to_response('objforms/form_base.html', {
                'info': form_info,
                'form': frm, 
                })
    else:
        if form.base_fields.has_key('parent'):
            frm = form(initial={'parent': id})
        else:
            frm = form()
        frm['items'].field.queryset = queryset
        return render_to_response('objforms/form_base.html', {
            'info': form_info, 
            'form': frm, 
            })
        
@login_required
@manager_required
def object_detail(request, id, model, template):
    """
    A generic view which displays a detailed page for an object of type ``model``
    identified by the primary key ``id`` using the template ``template``. 
    """
    try:
        obj = request.manager.get(pk=id)
    except:
        raise Http404
    return render_to_response(template, {
        'object': obj,
        'handler' : request.path
        },
        context_instance=RequestContext(request))

@login_required
@manager_required
def dewar_object_detail(request, id, model, template, admin=False):
    """
    Experiment needs a unique detail since it needs to pass the relevant information
    from results and datasets into it's detail.
    """
    try:
        obj = request.manager.get(pk=id)
    except:
        raise Http404
    
    containers = Container.objects.filter(dewar__exact=obj)
    
    return render_to_response(template, {
        'object': obj,
        'handler': request.path,
        'containers': containers,
        'admin': admin
        }, 
        context_instance=RequestContext(request))

@login_required
@manager_required
def crystal_object_detail(request, id, model, template, admin=False):
    """
    Experiment needs a unique detail since it needs to pass the relevant information
    from results and datasets into it's detail.
    """
    try:
        obj = request.manager.get(pk=id)
    except:
        raise Http404
    
    datasets = Data.objects.filter(crystal__exact=obj)
    results = Result.objects.filter(crystal__exact=obj)
    
    return render_to_response(template, {
        'object': obj,
        'handler': request.path,
        'datasets': datasets,
        'results': results,
        'admin': admin
        }, 
        context_instance=RequestContext(request))
    
@login_required
@manager_required
def experiment_object_detail(request, id, model, template, admin=False):
    """
    Experiment needs a unique detail since it needs to pass the relevant information
    from results and datasets into it's detail.
    """
    try:
        obj = request.manager.get(pk=id)
    except:
        raise Http404

    crystals = obj.crystal_set.annotate(best_score=Max('result__score')).order_by('-best_score')
    datasets = Data.objects.filter(experiment__exact=obj)
    results = Result.objects.filter(experiment__exact=obj)
    
    return render_to_response(template, {
        'object': obj,
        'crystals': crystals,
        'handler': request.path,
        'datasets': datasets,
        'results': results,
        'admin': admin
        }, 
        context_instance=RequestContext(request))

@login_required
@project_required
@transaction.commit_on_success
def create_object(request, model, form, template='lims/forms/new_base.html', action=None, redirect=None):
    """
    A generic view which displays a Form of type ``form`` using the Template
    ``template`` and when submitted will create a new object of type ``model``.
    """
    project = request.project
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
            if action:
                perform_action(new_obj, action, data=frm.cleaned_data)
            info_msg = 'The %(name)s "%(obj)s" was added successfully.' % {'name': smart_str(model._meta.verbose_name), 'obj': smart_str(new_obj)}
            ActivityLog.objects.log_activity(
                project.pk,
                request.user.pk, 
                request.META['REMOTE_ADDR'],
                new_obj, 
                ActivityLog.TYPE.CREATE,
                info_msg
                )
            request.user.message_set.create(message = info_msg)

            # messages are simply passed down to the template via the request context
            return render_to_response("lims/message.html", context_instance=RequestContext(request))
        else:
            return render_to_response(template, {
                'info': form_info,
                'form': frm, 
                }, 
                context_instance=RequestContext(request))
    else:
        initial = {'project': project.pk}
        initial.update(dict(request.GET.items()))      
        frm = form(initial=initial)

        frm.restrict_by('project', project.pk)
        if request.GET.has_key('clone'):
            clone_id = request.GET['clone']
            try:
                manager = getattr(project, model.__name__.lower()+'_set')
                clone_obj = manager.get(pk=clone_id)
            except:
                info_msg = 'Could not clone %(name)s!' % {'name': smart_str(model._meta.verbose_name)}
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
@project_required
def add_new_object(request, id, model, form, field):
    """
    A generic view which displays a form of type `form` which when submitted 
    will create a new object of type `model` and set it's foreign key field 
    `field` to the related object identified by the primary key `id`.
    """
    project = request.project
    object_type = model.__name__
    try:
        manager = getattr(project, field+'_set')
        related = manager.get(pk=id)
        related_type = related._meta.verbose_name
    except:
        raise Http404
    form_info = {
        'title': 'New %s' % object_type,
        'sub_title': 'Adding a new %s to %s "%s"' % (object_type, related_type, smart_str(related)),
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
            info_msg = '%s "%s" added to %s "%s"' % (object_type, smart_str(new_obj), related_type, smart_str(related))
            ActivityLog.objects.log_activity(
                project.pk,
                request.user.pk,
                request.META['REMOTE_ADDR'],
                new_obj, 
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
                    }, context_instance=RequestContext(request))
            else:
                return render_to_response('lims/refresh.html', context_instance=RequestContext(request))
        else:
            return render_to_response('objforms/form_base.html', {
                'info': form_info,
                'form': frm, 
                }, context_instance=RequestContext(request))
    else:
        frm = form(initial={'project': project.pk, field: related.pk})
        frm.restrict_by('project', project.pk)
        frm[field].field.widget.attrs['disabled'] = 'disabled'
        return render_to_response('objforms/form_base.html', {
            'info': form_info, 
            'form': frm, 
            }, context_instance=RequestContext(request))

@login_required
@manager_required
def object_list(request, model, template='objlist/object_list.html', link=True, can_add=False, can_upload=False, can_receive=False, can_prioritize=False, is_individual=False):
    """
    A generic view which displays a list of objects of type ``model`` owned by
    the current users project. The list is displayed using the template
    `template`. 
    
    Keyworded options:
        - ``link`` (boolean) specifies whether or not to link each item to it's detailed page.
        - ``can_add`` (boolean) specifies whether or not new entries can be added on the list page.   
        - 
    """
    log_set = [
        ContentType.objects.get_for_model(model).pk, 
    ]
    ol = ObjectList(request, request.manager)
    if not request.user.is_superuser:
        project = request.user.get_profile()
        logs = project.activitylog_set.filter(content_type__in=log_set)[:ACTIVITY_LOG_LENGTH]
    else:
        logs = ActivityLog.objects.filter(content_type__in=log_set)[:ACTIVITY_LOG_LENGTH]
    return render_to_response(template, {'ol': ol, 
                                         'link': link, 
                                         'can_add': can_add, 
                                         'can_upload': can_upload, 
                                         'can_receive': can_receive, 
                                         'can_prioritize': can_prioritize,
                                         'is_individual': is_individual,
                                         'handler': request.path,
                                         'logs': logs},                                         
        context_instance=RequestContext(request)
    )

@login_required
@manager_required    
def basic_object_list(request, model, template='objlist/basic_object_list.html'):
    """
    A very basic object list that will only display .name and .id for the entity
    The template this uses will be rendered in the sidebar controls.
    """
    ol = ObjectList(request, request.manager, num_show=200)
    handler = request.path
    # if path has /basic on it, remove that. 
    if 'basic' in handler:
        handler = handler[0:-6]
    return render_to_response(template, {'ol' : ol, 'type' : ol.model.__name__.lower(), 'handler': handler }, context_instance=RequestContext(request))

@login_required
@manager_required    
def unassigned_object_list(request, model, related_field, template='objlist/basic_object_list.html'):
    """
    Request a basic list of objects for which the related field is null.
    The template this uses will be rendered in the sidebar controls.
    """
    params = {'%s__isnull' % related_field : True}
    manager = FilterManagerWrapper(request.manager, **params)
    ol = ObjectList(request, manager, num_show=200)
    handler = request.path
    # if path has /basic on it, remove that. 
    if 'basic' in handler:
        handler = handler[0:-6]
    return render_to_response(template, {'ol' : ol, 'type' : ol.model.__name__.lower(), 'handler': handler }, context_instance=RequestContext(request))

    
@login_required
@manager_required
def basic_crystal_list(request, model, template="objlist/basic_object_list.html"):
    # get all crystals
    # filter result to just this project
    # filter results to just ones with experiment = none
    ol = ObjectList(request, request.manager, num_show=200)
    handler = request.path
    # if path has /basic on it, remove that. 
    if 'basic' in handler:
        handler = handler[0:-6]
    ol.object_list = Crystal.objects.filter(experiment=None).filter(project=request.project)
    # filter ol.object_list to just crystals with no experiment
    return render_to_response(template, {'ol' : ol, 'type' : ol.model.__name__.lower(), 'handler': handler }, context_instance=RequestContext(request))

@login_required
@manager_required
def container_crystal_list(request, model, template="objlist/basic_object_list.html"):
    # get all crystals
    # filter result to just this project
    # filter results to just ones with experiment = none
    ol = ObjectList(request, request.manager, num_show=200)
    handler = request.path
    # if path has /basic on it, remove that. 
    if 'basic' in handler:
        handler = handler[0:-6]
    ol.object_list = Crystal.objects.filter(container=None).filter(project=request.project)
    # filter ol.object_list to just crystals with no experiment
    return render_to_response(template, {'ol' : ol, 'type' : ol.model.__name__.lower(), 'handler': handler }, context_instance=RequestContext(request))

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
    handler = request.path
    return render_to_response(template, {'ol': ol,'link': link, 'can_add': can_add, 'handler': handler },
        context_instance=RequestContext(request)
    )
    
@login_required
@manager_required
@transaction.commit_on_success
def change_priority(request, id,  model, action, field):
    """
    """
    try:
        obj = request.manager.get(pk=id)
    except:
        raise Http404
    
    if request.method == 'POST':
        
        try:
            filter, order = '__gt', '' # return results with priority > obj.priority
            if action == 'down': 
                filter, order = '__lt', '-' # return results with priority < obj.priority
                
            # order by priority, DESC (ie. 9,8,7,6,...)
            results = model.objects.order_by(order + field).filter(**{field + filter: getattr(obj, field)})
            next_obj = results[0]
                
        except IndexError:
            next_obj = None
            
        delta = int(action == 'up') or -1
        setattr(obj, field, getattr(next_obj or obj, field) + delta)
        obj.save()
    
    return render_to_response('lims/refresh.html', context_instance=RequestContext(request))

@login_required
@transaction.commit_on_success
def priority(request, id,  model, field):
    
    if request.method == 'POST':
        pks = request.POST.getlist('objlist-list-table[]')
        pks.reverse()
        i = 0
        for pk in pks:
            if pk: # not all rows have ids (hidden ones)
                pk = int(pk)
                instance = model.objects.get(pk=pk)
                setattr(instance, field, i)
                instance.save()
                i += 1
            
    return HttpResponse()
    
@login_required
@transaction.commit_on_success
def edit_profile(request, form, template='objforms/form_base.html', action=None):
    """
    View for editing user profiles
    """
    try:
        model = Project
        obj = request.user.get_profile()
        request.project = obj
        request.manager = Project.objects
    except:
        raise Http404
    return edit_object_inline(request, obj.pk, model=model, form=form, template=template)
    
    
@login_required
@manager_required
@transaction.commit_on_success
def edit_object_inline(request, id, model, form, template='objforms/form_base.html', action=None):
    """
    A generic view which displays a form of type ``form`` using the template 
    ``template``, for editing an object of type ``model``, identified by primary 
    key ``id``, which when submitted will update the entry asynchronously through
    AJAX.
    """
    try:
        obj = request.manager.get(pk=id)
    except:
        raise Http404
    
    save_label = None
    if action:
        save_label = action[0].upper() + action[1:]
    
    form_info = {
        'title': request.GET.get('title', 'Edit %s' % model._meta.verbose_name),
        'sub_title': obj.identity(),
        'action':  request.path,
        'target': 'entry-scratchpad',
        'save_label': save_label
    }
    if request.method == 'POST':
        frm = form(request.POST, instance=obj)
        if request.project:
            frm.restrict_by('project', request.project.pk)
        if frm.is_valid():
            form_info['message'] = '%s: "%s|%s" successfully modified' % ( model._meta.verbose_name, obj.identity(), obj.__unicode__())
            frm.instance._activity_log = {
                'message': form_info['message'],
                'ip_number': request.META['REMOTE_ADDR'],
                'action_type': ActivityLog.TYPE.MODIFY,}
            frm.save()
            # if an action ('send', 'close') is specified, the perform the action
            if action:
                perform_action(obj, action, data=frm.cleaned_data)
            request.user.message_set.create(message = form_info['message'])
            
            return render_to_response('lims/message.html', context_instance=RequestContext(request))
        else:
            return render_to_response(template, {
            'info': form_info, 
            'form' : frm, 
            })
    else:
        frm = form(instance=obj, initial=dict(request.GET.items())) # casting to a dict pulls out first list item in each value list
        if request.project:
            frm.restrict_by('project', request.project.pk)
        return render_to_response(template, {
        'info': form_info, 
        'form' : frm,
        })
       
       
@login_required
@transaction.commit_on_success
def remove_object(request, src_id, obj_id, source, object, dest_id=None, destination=None, reverse=False):
    """
    New way to remove objects. Expected to be called via AJAX. By default removes object with id obj_id 
    from source with src_id. 
    reverse instead removes source from object. 
    """
    if request.method != 'POST':
        raise Http404
    
    if reverse:
        # swap obj and destination
        obj_id, src_id = src_id, obj_id
        object, source = source, object
    
    model = source;
    manager = model.objects
    request.project = None
    if not request.user.is_superuser:
        try:
            project = request.user.get_profile()
            request.project = project
            manager = FilterManagerWrapper(manager, project__exact=project)
        except Project.DoesNotExist:
            raise Http404    

    form_info = {
        'title': request.GET.get('title', 'Remove %s' % model.__name__),
        'sub_title': obj_id,
        'action':  request.path,
        'target': 'entry-scratchpad'
    }

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
    
#    try:
#        # get all items of the type we want to add to
#        manager = getattr(project, source.__name__.lower()+'_set')
#        obj_manager = getattr(project, object.__name__.lower()+'_set')
#        
#    except: 
#        raise Http404
    
    #get just the items we want
    src = manager.get(pk=src_id)
    to_remove = obj_manager.get(pk=obj_id)
    # get the display name
    display_name = to_remove.name
    if reverse:
        display_name = src.name
    
    if src.is_editable():
        #if replace == True or dest.(object.__name__.lower()) == None
        try:
            getattr(src, object.__name__.lower())
            setattr(src, object.__name__.lower(), None)
            if object.__name__.lower() == "container":
                setattr(src, "container_location", None)            
        except AttributeError:
            # attrib didn't exist, append 's' for many field
            try:
                current = getattr(src, '%ss' % object.__name__.lower())
                # want destination.objects.add(to_add)
                current.remove(to_remove)
                #setattr(dest, '%ss' % object.__name__.lower(), current_values)
            except AttributeError:
                message = '%s has not been removed. No Field (tried %s and %s)' % (display_name, object.__name__.lower(), '%ss' % object.__name__.lower())
                request.user.message_set.create(message = message)
                return render_to_response('lims/refresh.html', context_instance=RequestContext(request))
                       
        message = '%s has been successfully removed' % display_name
        src._activity_log = {
            'message': message,
            'ip_number': request.META['REMOTE_ADDR'],
            'action_type': ActivityLog.TYPE.MODIFY,}
        src.save()
        form_info['message'] = '%s has been successfully removed' % display_name
    
    else:
        message = '%s has not been removed, as %s is not editable' % (display_name, src.name)

    request.user.message_set.create(message = message)
    return render_to_response('lims/refresh.html', {
        'context': RequestContext(request), 
        'info': form_info,
        })

@login_required
@project_required
@transaction.commit_on_success
def remove_object_old(request, id, model, field):
    """
    A generic view which displays a confirmation form and if confirmed, will
    set the foreign key field ``field`` of the object of type ``model`` identified
    by primary key ``id`` to null. The model must have specified ``null=True`` as an
    option of the field.
    """
    project = request.project
    try:
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
            smart_str(obj), 
            related_type.lower(), 
            smart_str(related)
            )
    }
    if request.method == 'POST':
        if request.POST.has_key('_confirmed'):
            setattr(obj,field,None)
            obj.save()
            form_info['message'] = '%s "%s" removed from %s  "%s".' % (
                object_type, 
                smart_str(obj), 
                related_type.lower(), 
                smart_str(related)
                )
            ActivityLog.objects.log_activity(
                project.pk,
                request.user.pk, 
                request.META['REMOTE_ADDR'],
                obj, 
                ActivityLog.TYPE.MODIFY,
                form_info['message']
                )
            request.user.message_set.create(message = form_info['message'])            
            return render_to_response('lims/refresh.html', context_instance=RequestContext(request))
        else:
            return render_to_response('lims/refresh.html', context_instance=RequestContext(request))
    else:
        return render_to_response('lims/forms/confirm_action.html', {
            'info': form_info, 
            'id': obj.pk,
            'confirm_action': 'Remove %s' % object_type,
            },)
        
        
@login_required
@manager_required
@transaction.commit_on_success
def delete_object(request, id, model, form, template='objforms/form_base.html', orphan_models = None):
    """
    A generic view which displays a form of type ``form`` using the template 
    ``template``, for deleting an object of type ``model``, identified by primary 
    key ``id``, which when submitted will delete the entry asynchronously through
    AJAX.
    """
    try:
        obj = request.manager.get(pk=id)
    except:
        raise Http404
    
    orphan_models = orphan_models or []
    
    form_info = {
        'title': 'Delete %s?' % obj.__unicode__(),
        'sub_title': 'The %s %s will be deleted' % ( model.__name__, obj.__unicode__()),
        'action':  request.path,
        'target': 'entry-scratchpad',
        'message': 'Are you sure you want to delete %s "%s"?' % (
            model.__name__, obj.__unicode__()
            ),
        'save_label': 'Delete'
    }
    if request.method == 'POST':
        frm = form(request.POST, instance=obj)
        if request.project:
            frm.restrict_by('project', request.project.pk)
        if request.POST.has_key('_save'):
            delete(model, id, orphan_models)
            form_info['message'] = '%s %s successfully deleted' % ( model.__name__, obj.__unicode__())
            if hasattr(obj, 'project'):
                ActivityLog.objects.log_activity(
                    request.project.pk,
                    request.user.pk, 
                    request.META['REMOTE_ADDR'],
                    obj, 
                    ActivityLog.TYPE.DELETE,
                    form_info['message']
                    )
            request.user.message_set.create(message = form_info['message'])
            # messages are simply passed down to the template via the request context
            return render_to_response("lims/message.html", context_instance=RequestContext(request))
        else:
            return render_to_response(template, {
            'info': form_info, 
            'form' : frm, 
            })
    else:
        frm = form(instance=obj, initial=None) 
        if request.project:
            frm.restrict_by('project', request.project.pk)
        return render_to_response(template, {
        'info': form_info, 
        'form' : frm, 
        'save_label': 'Delete',
        })

@login_required
@project_required
@transaction.commit_on_success
def close_object(request, id, model, form, template="objforms/form_base.html"):
    """
    A generic view which displays a confirmation form and if confirmed, will
    archive the object of type ``model`` identified by primary key ``id``.
    
    If supplied, all instances of ``cascade_models`` (which is a list of tuples 
    of (Model, fk_field)) with a ForeignKey referencing ``model``/``id`` will also
    be archived.
    """
    project = request.project
    try:
        obj = model.objects.get(pk=id)
    except:
        raise Http404
    object_type = model.__name__
    

    form_info = {
        'title': 'Close %s?' % obj.__unicode__(),
        'sub_title': 'The %s %s will be closed.' % (model.__name__, obj.__unicode__()),
        'action':  request.path,
        'target': 'entry-scratchpad',
        'message': 'Are you sure you want to close %s "%s"?' % (
            model.__name__, 
            obj.__unicode__()
            ),
        'save_label': 'Close'
    }
    if request.method == 'POST':
        if request.POST.has_key('_save'):
            str_obj = smart_str(obj)
            archive(model, id)
            form_info['message'] = '%s "%s" closed.' % (
                model.__name__, 
                obj.__unicode__()
                )
            ActivityLog.objects.log_activity(
                project.pk,
                request.user.pk, 
                request.META['REMOTE_ADDR'],
                obj, 
                ActivityLog.TYPE.ARCHIVE,
                form_info['message']
                )
            request.user.message_set.create(message = form_info['message'])   
            return render_to_response("lims/message.html", context_instance=RequestContext(request))         
            
        else:
            return render_to_response('lims/refresh.html', context_instance=RequestContext(request))
    else:
        frm = form(instance=obj, initial=None) 
        if request.project:
            frm.restrict_by('project', request.project.pk)
        return render_to_response(template, {
        'info': form_info, 
        'form' : frm, 
        'save_label': 'Delete',
        })
        
@login_required
@project_required
def shipment_pdf(request, id):
    """ """
    project = request.project
    try:
        shipment = Shipment.objects.get(id=id)
    except:
        raise Http404
    
    # create a temporary directory
    temp_dir = tempfile.mkdtemp()
    
    try:
    
        # configure an HttpResponse so that it has the mimetype and attachment name set correctly
        response = HttpResponse(mimetype='application/pdf')
        filename = ('%s-%s.pdf' % (project.name, shipment.label)).replace(' ', '_')
        response['Content-Disposition'] = 'attachment; filename=%s' % filename
        
        # create a temporary file into which the LaTeX will be written
        temp_file = tempfile.mkstemp(dir=temp_dir, suffix='.tex')[1]
        # render and output the LaTeX into temap_file
        tex = loader.render_to_string('lims/tex/shipment.tex', {'project': project, 'shipment' : shipment})
        tex_file = open(temp_file, 'w')
        tex_file.write(tex)
        tex_file.close()
        
        # the arg for generate.sh is simply the .tex filename minus the .tex
        arg = os.path.basename(temp_file).replace('.tex', '')
        devnull = file('/dev/null', 'rw')
        stdout = sys.stdout
        stderr = sys.stderr
        if not settings.DEBUG:
            stdout = devnull
            stderr = devnull
        subprocess.call(['/bin/bash', settings.TEX_TOOLS_DIR + '/ps4pdf.sh', arg], 
                        env={'TEXINPUTS' : '.:' + settings.TEX_TOOLS_DIR + ':',
                             'PATH' : settings.TEX_BIN_PATH},
                        cwd=temp_dir,
                        #stdout=stdout.fileno(),
                        #stderr=stderr.fileno(),
                        #stdin=devnull
                        )
        
        # open the resulting .pdf and write it out to the response/browser
        pdf_file = open(temp_file.replace('.tex', '.pdf'), 'r')
        pdf = pdf_file.read()
        pdf_file.close()
        response.write(pdf)
        
        # return the response
        return response
        
    finally:
        
        if not settings.DEBUG:
            # remove the tempfiles
            shutil.rmtree(temp_dir)

@login_required
@project_required
def shipment_xls(request, id):
    """ """
    project = request.project
    try:
        shipment = Shipment.objects.get(id=id)
    except:
        raise Http404
    
    temp_dir = tempfile.mkdtemp()
    
    try:
    
        # configure an HttpResponse so that it has the mimetype and attachment name set correctly
        response = HttpResponse(mimetype='application/xls')
        filename = ('%s-%s.xls' % (project.name, shipment.label)).replace(' ', '_')
        response['Content-Disposition'] = 'attachment; filename=%s' % filename
        
        # create a temporary directory
        temp_dir = tempfile.mkdtemp()
        # create a temporary file into which the .xls will be written
        temp_file = tempfile.mkstemp(dir=temp_dir, suffix='.xls')[1]
        
        # export it
        # why we use all?
        #workbook = LimsWorkbookExport(project.experiment_set.all(), project.crystal_set.all())
        dewars = shipment.dewar_set.all()
        
        containers = list()
        for dewar in dewars:
            for cont in dewar.container_set.all():
                containers.append(cont)
        
        crystals = list()
        for cont in containers:
            for crys in cont.crystal_set.all():
                crystals.append(crys)
        
        ship_experiments = list()
        for cont in containers:
            for exp in cont.get_experiment_list():
                if exp not in ship_experiments:
                    ship_experiments.append(exp)
    
        workbook = LimsWorkbookExport(ship_experiments, crystals)
        errors = workbook.save(temp_file)
        
        # open the resulting .xls and write it out to the response/browser
        xls_file = open(temp_file)
        xls = xls_file.read()
        xls_file.close()
        response.write(xls)
        
        # return the response
        return response
        
    finally:
        
        if not settings.DEBUG:
            # remove the tempfiles
            shutil.rmtree(temp_dir)
    
@jsonrpc_method('lims.add_data', authenticated=getattr(settings, 'AUTH_REQ', True))
def add_data(request, data_info):
    info = {}
    
    # check if project_id is provided if not check if project_name is provided
    if data_info.get('project_id') is None and data_info.get('project_name') is not None:
        project = create_project(username=data_info['project_name'])
        data_info['project_id'] = project.pk
        del data_info['project_name']
    # convert unicode to str
    data_owner = Project.objects.get(pk=data_info['project_id'])
    for k,v in data_info.items():
        if k == 'url':
            v = create_download_key(v, data_owner.pk)
        info[smart_str(k)] = v
    try:
        new_obj = Data(**info)
        # check type, and change status accordingly
        if new_obj.kind == Result.RESULT_TYPES.SCREENING:
            new_obj.crystal.screen_status = Crystal.EXP_STATES.COMPLETED
            new_obj.crystal.save()
        elif new_obj.kind == Result.RESULT_TYPES.COLLECTION:
            new_obj.crystal.collect_status = Crystal.EXP_STATES.COMPLETED
            new_obj.crystal.save()
        new_obj.save()
        return {'data_id': new_obj.pk}
    except Exception, e:
        raise e
        return {'error': str(e)}

@jsonrpc_method('lims.add_result', authenticated=getattr(settings, 'AUTH_REQ', True))
def add_result(request, res_info):
    info = {}
    # convert unicode to str
    data_owner = Project.objects.get(pk=res_info['project_id'])
    for k,v in res_info.items():
        if k == 'url':
            v = create_download_key(v, data_owner.pk)
        info[smart_str(k)] = v
    try:
        new_obj = Result(**info)
        new_obj.save()
        return {'result_id': new_obj.pk}
    except Exception, e:
        raise e
        return {'error':str(e)}

@jsonrpc_method('lims.add_strategy', authenticated=getattr(settings, 'AUTH_REQ', True))
def add_strategy(request, stg_info):
    info = {}
    # convert unicode to str
    for k,v in stg_info.items():
        info[smart_str(k)] = v
    new_obj = Strategy(**info)
    new_obj.save()
    return {'strategy_id': new_obj.pk}

@login_required
def data_viewer(request, id):
    # use the data_viewer template
    # load data for displaying
    manager = Data.objects
    
    try:
        data = manager.get(pk=id)
    except:
        raise Http404
    
    results = Result.objects.filter(data__id=id)
    expanded_frame_set = data.get_frame_list();
    
    return render_to_response('lims/entries/data.html', {'data':data, 'results':results, 'expanded_frame_set': expanded_frame_set})

@login_required
def result_print(request, id):
    manager = Result.objects
    
    try:
        result = manager.get(pk=id)
    except:
        raise Http404
    
    admin = request.user.is_superuser
    return render_to_response('lims/entries/result_print.html', {'object':result, 'admin':admin})

@login_required
def rescreen(request, id):
    crystal = Crystal.objects.get(pk=id)
    crystal.rescreen()
    return render_to_response('lims/refresh.html')
    
@login_required
def recollect(request, id):
    crystal = Crystal.objects.get(pk=id)
    crystal.recollect()
    return render_to_response('lims/refresh.html')
    
@login_required
def complete(request, id):
    crystal = Crystal.objects.get(pk=id)
    crystal.complete()
    return render_to_response('lims/refresh.html')


# -------------------------- PLOTTING ----------------------------------------#
import numpy
from matplotlib.backends.backend_agg import FigureCanvasAgg as FigureCanvas
from matplotlib.ticker import Formatter, FormatStrFormatter, Locator
from matplotlib.figure import Figure
from matplotlib import rcParams
from matplotlib.colors import LogNorm, Normalize
import matplotlib.cm as cm
#from mpl_toolkits.axes_grid import AxesGrid

# Adjust rc parameters
rcParams['legend.loc'] = 'best'
rcParams['legend.fontsize'] = 12
rcParams['legend.isaxes'] = False
rcParams['figure.facecolor'] = 'white'
rcParams['figure.edgecolor'] = 'white'
rcParams['mathtext.fontset'] = 'stix'
rcParams['mathtext.fallback_to_cm'] = True
rcParams['font.size'] = 14
rcParams['font.family'] = 'serif'
rcParams['font.serif'] = 'Gentium Basic'

class ResFormatter(Formatter):
    def __call__(self, x, pos=None):
        if x <= 0.0:
            return u""
        else:
            return u"%0.2f" % (x**-0.5)

class ResLocator(Locator):
    def __call__(self, *args, **kwargs):
        locs = numpy.linspace(0.0156, 1, 30 )
        return locs


PLOT_WIDTH = 8
PLOT_HEIGHT = 7 
PLOT_DPI = 75
IMG_WIDTH = int(round(PLOT_WIDTH * PLOT_DPI))

@login_required
@cache_page(60*3600)
def plot_shell_stats(request, id):
    try:
        project = request.user.get_profile()
        result = project.result_set.get(pk=id)
    except:
        raise Http404
    # extract shell statistics to plot
    data = result.details['shell_statistics']
    shell = numpy.array(data['shell'])**-2
    fig = Figure(figsize=(PLOT_WIDTH, PLOT_HEIGHT), dpi=PLOT_DPI)
    ax1 = fig.add_subplot(211)
    ax1.plot(shell, data['completeness'], 'r-')
    ax1.set_ylabel('completeness (%)', color='r')
    ax11 = ax1.twinx()
    ax11.plot(shell, data['r_meas'], 'g-', label='R-meas')
    ax11.plot(shell, data['r_mrgdf'], 'g:+', label='R-mrgd-F')
    ax11.legend(loc='center left')
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
    ax2.plot(shell, data['i_sigma'], 'm-')
    ax2.set_xlabel('Resolution Shell')
    ax2.set_ylabel('I/SigmaI', color='m')
    ax21 = ax2.twinx()
    ax21.plot(shell, data['sig_ano'], 'b-')
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

    ax1.xaxis.set_major_formatter(ResFormatter())
    ax1.xaxis.set_minor_formatter(ResFormatter())
    ax1.xaxis.set_major_locator(ResLocator())
    ax2.xaxis.set_major_formatter(ResFormatter())
    ax2.xaxis.set_minor_formatter(ResFormatter())
    ax2.xaxis.set_major_locator(ResLocator())

    canvas = FigureCanvas(fig)
    response = HttpResponse(content_type='image/png')
    canvas.print_png(response)
    return response


@login_required
@cache_page(60*3600)
def plot_error_stats(request, id):
    try:
        project = request.user.get_profile()
        result = project.result_set.get(pk=id)
    except:
        raise Http404

    data = result.details['standard_errors'] # extract data to plot
    shell = numpy.array(data['shell'])**-2    
    fig = Figure(figsize=(PLOT_WIDTH, PLOT_HEIGHT), dpi=PLOT_DPI)
    ax1 = fig.add_subplot(211)
    ax1.plot(shell, data['chi_sq'], 'r-')
    ax1.set_ylabel(r'$\chi^{2}$', color='r')
    ax11 = ax1.twinx()
    ax11.plot(shell, data['i_sigma'], 'b-')
    ax11.set_ylabel(r'I/Sigma', color='b')
    ax1.grid(True)
    for tl in ax11.get_yticklabels():
        tl.set_color('b')
    for tl in ax1.get_yticklabels():
        tl.set_color('r')
    ax1.yaxis.set_major_formatter(FormatStrFormatter('%0.1f'))
    ax11.yaxis.set_major_formatter(FormatStrFormatter('%0.1f'))
    ax1.set_ylim((0, 3))
    #ax11.set_ylim((0, 105))

    ax2 = fig.add_subplot(212, sharex=ax1)
    ax2.plot(shell, data['r_obs'], 'g-', label='R-observed')
    ax2.plot(shell, data['r_exp'], 'r:', label='R-expected')
    ax2.set_xlabel('Resolution Shell')
    ax2.set_ylabel('R-factors (%)')
    ax2.legend(loc='best')
    ax2.grid(True)
    ax2.yaxis.set_major_formatter(FormatStrFormatter('%0.0f'))
    ax2.set_ylim((0,105))

    ax1.xaxis.set_major_formatter(ResFormatter())
    ax1.xaxis.set_minor_formatter(ResFormatter())
    ax1.xaxis.set_major_locator(ResLocator())

    ax2.xaxis.set_major_formatter(ResFormatter())
    ax2.xaxis.set_minor_formatter(ResFormatter())
    ax2.xaxis.set_major_locator(ResLocator())

    # make and return png image
    canvas = FigureCanvas(fig)
    response = HttpResponse(content_type='image/png')
    canvas.print_png(response)
    return response


@login_required
@cache_page(60*3600)
def plot_diff_stats(request, id):
    try:
        project = request.user.get_profile()
        result = project.result_set.get(pk=id)
    except:
        raise Http404
        
    # extract statistics to plot
    data = result.details['diff_statistics']
    fig = Figure(figsize=(PLOT_WIDTH, PLOT_HEIGHT * 0.66), dpi=PLOT_DPI)
    ax1 = fig.add_subplot(111)
    ax1.plot(data['frame_diff'], data['rd'], 'r-', label="all")
    ax1.set_ylabel('R-d')
    ax1.grid(True)
    ax1.yaxis.set_major_formatter(FormatStrFormatter('%0.2f'))

    ax1.plot(data['frame_diff'], data['rd_friedel'], 'm-', label="friedel")
    ax1.plot(data['frame_diff'], data['rd_non_friedel'], 'k-', label="non_friedel")
    ax1.set_xlabel('Frame Difference')
    ax1.legend()

    # make and return png image
    canvas = FigureCanvas(fig)
    response = HttpResponse(content_type='image/png')
    canvas.print_png(response)
    return response


@login_required
@cache_page(60*3600)
def plot_wilson_stats(request, id):
    try:
        project = request.user.get_profile()
        result = project.result_set.get(pk=id)
    except:
        raise Http404
        
    # extract statistics to plot
    data = result.details['wilson_plot']
    fig = Figure(figsize=(PLOT_WIDTH, PLOT_HEIGHT * 0.6), dpi=PLOT_DPI)
    ax1 = fig.add_subplot(111)
    plot_data = zip(data['inv_res_sq'], data['log_i_sigma'])
    plot_data.sort()
    plot_data = numpy.array(plot_data)
    ax1.plot(plot_data[:,0], plot_data[:,1], 'r-+')
    ax1.set_xlabel('Resolution')
    ax1.set_ylabel(r'$ln\left(\frac{<I>}{\sigma(f)^2}\right)$')
    ax1.grid(True)
    ax1.xaxis.set_major_formatter(ResFormatter())
    ax1.xaxis.set_major_locator(ResLocator())
    
    # set font parameters for the ouput table
    wilson_line = result.details['wilson_line']
    wilson_scale = result.details['wilson_scale']
    fontpar = {}
    fontpar["family"]="monospace"
    fontpar["size"]=9
    info =  "Estimated B: %0.3f\n" % wilson_line[0]
    info += "sigma a: %8.3f\n" % wilson_line[1]
    info += "sigma b: %8.3f\n" % wilson_line[2]
    info += "Scale factor: %0.3f\n" % wilson_scale    
    fig.text(0.55,0.65, info, fontdict=fontpar, color='k')

    # make and return png image
    canvas = FigureCanvas(fig)
    response = HttpResponse(content_type='image/png')
    canvas.print_png(response)
    return response


@login_required
@cache_page(60*3600)
def plot_frame_stats(request, id):
    try:
        project = request.user.get_profile()
        result = project.result_set.get(pk=id)
    except:
        raise Http404
    # extract statistics to plot
    data = result.details['frame_statistics']
    fig = Figure(figsize=(PLOT_WIDTH, PLOT_HEIGHT), dpi=PLOT_DPI)
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
    ax2.set_ylim((min(data['divergence'])-0.02, max(data['divergence'])+0.02))
    ax2.yaxis.set_major_formatter(FormatStrFormatter('%0.3f'))
    ax2.grid(True)
    if data.get('frame_no') is not None:
        ax21 = ax2.twinx()
        ax21.plot(data['frame_no'], data['i_sigma'], 'b-')

        ax21.set_ylabel('I/Sigma(I)', color='b')
        for tl in ax21.get_yticklabels():
            tl.set_color('b')
        for tl in ax2.get_yticklabels():
            tl.set_color('m')

        ax3 = fig.add_subplot(313, sharex=ax1)
        ax3.plot(data['frame_no'], data['r_meas'], 'k-')
        ax3.set_xlabel('Frame Number')
        ax3.set_ylabel('R-meas', color='k')
        ax31 = ax3.twinx()
        ax31.plot(data['frame_no'], data['unique'], 'c-')
        ax3.grid(True)
        ax31.set_ylabel('Unique Reflections', color='c')
        for tl in ax31.get_yticklabels():
            tl.set_color('c')
        for tl in ax3.get_yticklabels():
            tl.set_color('k')
        ax21.yaxis.set_major_formatter(FormatStrFormatter('%0.1f'))
        ax3.yaxis.set_major_formatter(FormatStrFormatter('%0.3f'))
        ax31.yaxis.set_major_formatter(FormatStrFormatter('%0.0f'))

    canvas = FigureCanvas(fig)
    response = HttpResponse(content_type='image/png')
    canvas.print_png(response)
    return response


@login_required
@cache_page(60*3600)
def plot_twinning_stats(request, id):
    try:
        project = request.user.get_profile()
        result = project.result_set.get(pk=id)
    except:
        raise Http404
    # extract statistics to plot
    data = result.details['twinning_l_test']
    fig = Figure(figsize=(PLOT_WIDTH, PLOT_HEIGHT * 0.6), dpi=PLOT_DPI)
    ax1 = fig.add_subplot(111)
    ax1.plot(data['abs_l'], data['observed'], 'b-+', label='observed')
    ax1.plot(data['abs_l'], data['untwinned'], 'r-+', label='untwinned')
    ax1.plot(data['abs_l'], data['twinned'], 'm-+', label='twinned')
    ax1.set_xlabel('$|L|$')
    ax1.set_ylabel('$P(L>=1)$')
    ax1.grid(True)
    
    # set font parameters for the ouput table
    l_statistic = result.details.get('twinning_l_statistic')
    if l_statistic is not None:
        fontpar = {}
        fontpar["family"]="monospace"
        fontpar["size"]=9
        info =  "Observed:     %0.3f\n" % l_statistic[0]
        info += "Untwinned:    %0.3f\n" % l_statistic[1]
        info += "Perfect twin: %0.3f\n" % l_statistic[2]
        fig.text(0.6,0.2, info, fontdict=fontpar, color='k')
    ax1.legend()
    

    # make and return png image
    canvas = FigureCanvas(fig)
    response = HttpResponse(content_type='image/png')
    canvas.print_png(response)
    return response

@login_required
@cache_page(60*3600)
def plot_profiles_stats(request, id):
    try:
        project = request.user.get_profile()
        result = project.result_set.get(pk=id)
    except:
        raise Http404
    # extract statistics to plot
    profiles = result.details['integration_profiles']
    fig = Figure(figsize=(PLOT_WIDTH, PLOT_WIDTH), dpi=PLOT_DPI)
    cmap = cm.get_cmap('gray_r')
    norm = Normalize(None, 100, clip=True)
    grid = AxesGrid(fig, 111,
                    nrows_ncols = (9,10),
                    share_all=True,
                    axes_pad = 0,
                    label_mode = '1',
                    cbar_mode=None)
    for i, profile in enumerate(profiles):
        grid[i*10].plot([profile['x']],[profile['y']], 'cs', markersize=15)
        for loc in ['left','top','bottom','right']:
            grid[i*10].axis[loc].toggle(ticklabels=False, ticks=False)
        for j,spot in enumerate(profile['spots']):
            idx = i*10 + j+1
            _a = numpy.array(spot).reshape((9,9))
            intpl = 'nearest' #'mitchell'
            grid[idx].imshow(_a, cmap=cmap, norm=norm, interpolation=intpl)
            for loc in ['left','top','bottom','right']:
                grid[idx].axis[loc].toggle(ticklabels=False, ticks=False)
    
    # make and return png image
    canvas = FigureCanvas(fig)
    response = HttpResponse(content_type='image/png')
    canvas.print_png(response)
    return response

