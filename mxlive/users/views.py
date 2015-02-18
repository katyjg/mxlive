from datetime import timedelta
from django.conf import settings
from django.contrib import messages
from django.contrib.auth import REDIRECT_FIELD_NAME
from django.contrib.auth.decorators import login_required, user_passes_test
from django.contrib.contenttypes.models import ContentType
from django.core.urlresolvers import reverse
from django.db import IntegrityError
from django.db import transaction
from django.http import Http404, HttpResponseRedirect, HttpResponse
from django.shortcuts import render_to_response, get_object_or_404
from django.template import RequestContext
from django.template import loader
from django.utils import dateformat, timezone
from django.views.decorators.cache import cache_page
from apikey.views import apikey_required
from download.views import create_download_key, create_cache_dir, send_raw_file
from .excel import LimsWorkbookExport
from .models import *
from objlist.views import ObjectList
from staff.models import *
from django.utils.encoding import smart_str

import shutil
import subprocess
import sys
import tempfile

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
    """ Decorator that enforces the existence of a mxlive.users.models.Project """
    def project_required_wrapper(request, *args, **kwargs):
        try:
            project = request.user.get_profile()
            request.project = project
            return function(request, *args, **kwargs)
        except Project.DoesNotExist:
            raise Http404
    return project_required_wrapper

def project_optional(function):
    """ Decorator that enforces the existence of a mxlive.users.models.Project """
    def project_optional_wrapper(request, *args, **kwargs):
        try:
            project = request.user.get_profile()
            request.project = project
            return function(request, *args, **kwargs)
        except Project.DoesNotExist:
            if not request.user.is_staff:
                raise
            project=None
            request.project = project
            return function(request, *args, **kwargs)
    return project_optional_wrapper

# True = Staff; False = Users
MANAGER_FILTERS = {
    (Shipment, True) : {'status__in': [Shipment.STATES.SENT, Shipment.STATES.ON_SITE, Shipment.STATES.RETURNED], 'pk__in': Shipment.objects.exclude(modified__lte=timezone.now() - timedelta(days=7), status__exact=Shipment.STATES.RETURNED).values('pk')},
    (Shipment, False) : {'status__in': [Shipment.STATES.DRAFT, Shipment.STATES.SENT, Shipment.STATES.ON_SITE, Shipment.STATES.RETURNED]},
    (Dewar, True) : {'status__in': [Dewar.STATES.SENT, Dewar.STATES.ON_SITE, Dewar.STATES.RETURNED], 'pk__in': Dewar.objects.exclude(modified__lte=timezone.now() - timedelta(days=7), status__exact=Dewar.STATES.RETURNED).values('pk')},
    (Dewar, False) : {'status__in': [Dewar.STATES.DRAFT, Dewar.STATES.SENT, Dewar.STATES.ON_SITE, Dewar.STATES.RETURNED]},
    (Container, True) : {'status__in': [Container.STATES.SENT, Container.STATES.ON_SITE, Container.STATES.LOADED, Container.STATES.RETURNED], 'pk__in': Container.objects.exclude(modified__lte=timezone.now() - timedelta(days=7), status__exact=Container.STATES.RETURNED).values('pk')},
    (Container, False) : {'status__in': [Container.STATES.DRAFT, Container.STATES.SENT, Container.STATES.ON_SITE, Container.STATES.LOADED, Container.STATES.RETURNED]},
    (Crystal, True) : {'status__in': [Crystal.STATES.SENT, Crystal.STATES.ON_SITE, Crystal.STATES.LOADED, Crystal.STATES.RETURNED]},
    (Crystal, False) : {'status__in': [Crystal.STATES.DRAFT, Crystal.STATES.SENT, Crystal.STATES.ON_SITE, Crystal.STATES.LOADED, Crystal.STATES.RETURNED]},
    (Experiment, True) : {'status__in': [Experiment.STATES.ACTIVE, Experiment.STATES.PROCESSING, Experiment.STATES.COMPLETE, Experiment.STATES.REVIEWED], 'pk__in': Crystal.objects.filter(status__in=[Crystal.STATES.SENT, Crystal.STATES.ON_SITE, Crystal.STATES.LOADED]).values('experiment')},
    (Experiment, False) : {'status__in': [Experiment.STATES.DRAFT, Experiment.STATES.ACTIVE, Experiment.STATES.PROCESSING, Experiment.STATES.COMPLETE, Experiment.STATES.REVIEWED]},
    (Data, True) : {'status__in': [Data.STATES.ACTIVE, Data.STATES.ARCHIVED, Data.STATES.TRASHED]},
    (Data, False) : {'status__in': [Data.STATES.ACTIVE]},
    (Result, True) : {'status__in': [Result.STATES.ACTIVE, Result.STATES.ARCHIVED, Result.STATES.TRASHED]},
    (Result, False) : {'status__in': [Result.STATES.ACTIVE]},
    (Runlist, True) : {'status__in': [Runlist.STATES.PENDING, Runlist.STATES.LOADED, Runlist.STATES.UNLOADED, Runlist.STATES.CLOSED]},
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
        if model in [Data, Result] and not request.user.is_superuser:
            manager = FilterManagerWrapper(manager, status__lte=Data.STATES.ARCHIVED)
        if MANAGER_FILTERS.has_key((model, request.user.is_superuser)):
            if request.user.is_superuser or not project.show_archives:
                manager = FilterManagerWrapper(manager,**MANAGER_FILTERS[(model, request.user.is_superuser)])
        if MANAGER_ORDER_BYS.has_key((model, request.user.is_superuser)):
            manager = OrderByManagerWrapper(manager,*MANAGER_ORDER_BYS[(model, request.user.is_superuser)])
        request.manager = manager
        assert isinstance(request.manager, models.Manager)
        return function(request, *args, **kwargs)
    return manager_required_wrapper


def project_assurance(function):
    """ Decorator that creates a default mxlive.users.models.Project if there isn't one """
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
      1. /users/ - for users
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
    
    # if user has logged in past week, show recent items in past week otherwise
    # show recent items since last login.
    
    recent_start = timezone.now() - timedelta(days=7)
    last_login = ActivityLog.objects.last_login(request)
    if last_login is not None:
        if last_login.created < recent_start:
            recent_start = last_login.created       

    statistics = {
        'shipments': {
                'outgoing': project.shipment_set.filter(status__exact=Shipment.STATES.SENT).count(),
                'incoming': project.shipment_set.filter(status__exact=Shipment.STATES.RETURNED).count(),
                'on_site': project.shipment_set.filter(status__exact=Shipment.STATES.ON_SITE).count(),
                },
        'dewars': {
                'outgoing': project.dewar_set.filter(status__exact=Dewar.STATES.SENT).count(),
                'incoming': project.dewar_set.filter(status__exact=Dewar.STATES.RETURNED).count(),
                'on_site': project.dewar_set.filter(status__exact=Dewar.STATES.ON_SITE).count(),
                },
        'experiments': {
                'active': project.experiment_set.filter(status__exact=Experiment.STATES.ACTIVE).filter(pk__in=Crystal.objects.filter(status__in=[Crystal.STATES.ON_SITE, Crystal.STATES.LOADED]).values('experiment')).count(),
                'processing': project.experiment_set.filter(status__exact=Experiment.STATES.PROCESSING).count(),
                },
        'crystals': {
                'on_site': project.crystal_set.filter(status__in=[Crystal.STATES.ON_SITE, Crystal.STATES.LOADED]).count(),
                'outgoing': project.crystal_set.filter(status__exact=Crystal.STATES.SENT).count(),
                'incoming': project.crystal_set.filter(status__exact=Crystal.STATES.RETURNED).count(),
                },
        'reports':{
                'total': project.result_set.all().count(),
                'new': project.result_set.filter(modified__gte=recent_start).filter(**project.get_archive_filter()).count(),
                'start_date': recent_start,                
                },
        'datasets':{
                'total': project.data_set.all().count(),
                'new': project.data_set.filter(modified__gte=recent_start).filter(**project.get_archive_filter()).count(),
                'start_date': recent_start,
                },        
        'scanresults':{
                'total': project.scanresult_set.all().count(),
                'new': project.scanresult_set.filter(modified__gte=recent_start).filter(**project.get_archive_filter()).count(),
                'start_date': recent_start,
                },              
    }
    
    return render_to_response('users/project.html', {
        'project': project,
        'statistics': statistics,
        'activity_log': ObjectList(request, project.activitylog_set),
        'handler' : request.path,
        },
    context_instance=RequestContext(request))
 
@login_required
@project_required
@transaction.commit_on_success
def upload_shipment(request, model, form, template='users/forms/form_base.html'):
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
                frm.save(request) #FIXME ShipmentUpload form.save does not return the model being saved!
                message = "Shipment uploaded successfully.  Click 'Send' to alert CMCF staff of your shipment."
                messages.info(request, message)
                obj = Shipment.objects.filter(status__exact=0).get(name__exact=frm.get_shipment())
                return render_to_response("users/iframe_refresh.html", {'redirect_to': '/users/shipping/shipment/%s/' % obj.pk,}, context_instance=RequestContext(request))
            except IntegrityError:
                transaction.rollback()
                frm.add_excel_error('This data has been uploaded already')
                return render_to_response(template, {'form': frm, 'info': form_info}, context_instance=RequestContext(request))
        else:
            if frm.error_message():
                frm.fields = {}
                form_info['no_action'] = True
                form_info['message'] = 'Uh-oh!  Please fix the following errors with your spreadsheet, and then try again.'
            return render_to_response(template, {'form': frm, 'info': form_info}, context_instance=RequestContext(request))
    else:
        frm = form(initial={'project': project.pk})
        return render_to_response(template, {'form': frm, 'info': form_info}, context_instance=RequestContext(request))


@login_required
@transaction.commit_on_success
def add_existing_object(request, dest_id, obj_id, destination, obj, src_id=None, loc_id=None, source=None, replace=False, reverse=False):
    """
    New add method. Meant for AJAX, so only intended to be POST'd to. This will add an object of type 'object'
    and id 'obj_id' to the object of type 'destination' with the id of 'dest_id'.
    Replace means if the field already has an item in it, replace it, else fail
    Reverse means, due to model layout, you are actually adding destination to object
    """
    object_type = destination.__name__
    form_info = {
        'title': 'Add Existing %s' % (object_type),
        'sub_title': 'Select existing %ss to add to %s' % (object_type.lower(), obj),
        'action':  request.path,
        'target': 'entry-scratchpad',
    }
    if request.method != 'POST':
        raise Http404

    if reverse:
        # swap obj and destination
        obj_id, dest_id = dest_id, obj_id
        obj, destination = destination, obj

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

    model = obj
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
        
    lookup_name = obj.__name__.lower()
    if lookup_name == 'crystalform':
        lookup_name = 'crystal_form'
    
    if dest.is_editable():
        #if replace == True or dest.(obj.__name__.lower()) == None
        try:
            getattr(dest, lookup_name)
            setattr(dest, lookup_name, to_add)
        except AttributeError:
            # attrib didn't exist, append 's' for many field
            try:
                current = getattr(dest, '%ss' % lookup_name)
                # want destination.objects.add(to_add)
                current.add(to_add)
                #setattr(dest, '%ss' % obj.__name__.lower(), current_values)
            except AttributeError:
                message = '%s has not been added. No Field (tried %s and %s)' % (display_name, lookup_name, '%ss' % lookup_name)
                messages.info(request, message)
                return render_to_response('users/refresh.html', context_instance=RequestContext(request))
                
        if loc_id:
            setattr(dest, 'container_location', loc_id)
        if ((destination.__name__ == 'Experiment' and obj.__name__ == 'Crystal') or (destination.__name__ == 'Container' and obj.__name__ == 'Dewar')):
            for exp in dest.get_experiment_list():
                if exp:
                    exp.priority = 0
                    exp.save()    
    
        dest.save()
        message = '%s (%s) added' % (dest.__class__._meta.verbose_name, display_name)
        ActivityLog.objects.log_activity(request, dest, ActivityLog.TYPE.MODIFY, 
            '%s added to %s (%s)' % (dest._meta.verbose_name, to_add._meta.verbose_name, to_add))
    else:
        message = '%s has not been added, as %s is not editable' % (display_name, dest.name)

    messages.info(request, message)
    return render_to_response('users/refresh.html', {
        'info': form_info,
        }, context_instance=RequestContext(request))
    
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
    cnt_type = ContentType.objects.get_for_model(obj)
    history = ActivityLog.objects.filter(content_type__pk=cnt_type.id, object_id=obj.id)
    
    # determine if there is a list url for this model and pass it in as list_url
    if request.user.is_staff:
        url_prefix = 'staff'
    else:
        url_prefix = 'users'
    url_name = "%s-%s-list" % (url_prefix, model.__name__.lower())
    try:
        list_url = (model == Runlist and reverse(url_name)+'?status__lte=4') or reverse(url_name)
    except:
        list_url = None
    return render_to_response(template, {
        'object': obj,
        'history': history[:ACTIVITY_LOG_LENGTH],
        'handler' : request.path,
        'list_url': list_url,
        }, context_instance=RequestContext(request))
    
@login_required
@project_optional
@transaction.commit_on_success
def create_object(request, model, form, id=None, template='users/forms/new_base.html', action=None, redirect=None, modal_upload=False):
    """
    A generic view which displays a Form of type ``form`` using the Template
    ``template`` and when submitted will create a new object of type ``model``.
    """
    if request.project:
        project = request.project
        project_pk = project.pk
    else:
        project = None
        project_pk = None
    object_type = model._meta.verbose_name

    form_info = {
        'title': 'New %s' % object_type,
        'action':  request.path,
        'add_another': True, # does not work right now
    }
    if modal_upload:
        form_info['enctype'] = 'multipart/form-data'

    if request.method == 'POST':
        frm = form(request.POST, request.FILES)
        frm.restrict_by('project', project_pk)
        if frm.is_valid():
            new_obj = frm.save()
            info_msg = 'New %(name)s (%(obj)s) added' % {'name': smart_str(model._meta.verbose_name), 'obj': smart_str(new_obj)}
            ActivityLog.objects.log_activity(request, new_obj, ActivityLog.TYPE.CREATE, 
                'new %s added' % (smart_str(model._meta.verbose_name),))
            messages.info(request, info_msg)
            if request.POST.has_key('_addanother'):
                initial = {'project': project_pk}
                initial.update(dict(request.GET.items()))      
                frm = form(initial=initial)
                frm.restrict_by('project', project_pk)
                return render_to_response(template, {
                    'info': form_info, 
                    'form': frm, 
                    }, context_instance=RequestContext(request))
            else:
                if modal_upload:
                    return render_to_response("users/iframe_refresh.html", context_instance=RequestContext(request))
                # messages are simply passed down to the template via the request context
                return render_to_response("users/redirect.html", context_instance=RequestContext(request))
        else:
            return render_to_response(template, {
                'info': form_info,
                'form': frm,
                }, context_instance=RequestContext(request))
    else:
        if project:
            initial = {'project': project_pk}
            if id:
                initial['shipment'] = id
            initial.update(dict(request.GET.items()))      
            frm = form(initial=initial)
        else:
            frm = form(initial=None)

        frm.restrict_by('project', project_pk)
        if request.GET.has_key('clone'):
            clone_id = request.GET['clone']
            try:
                manager = getattr(project, model.__name__.lower()+'_set')
                clone_obj = manager.get(pk=clone_id)
            except:
                info_msg = 'Could not clone %(name)s!' % {'name': smart_str(model._meta.verbose_name)}
                messages.info(request, info_msg)
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
            }, context_instance=RequestContext(request))

@login_required
@manager_required
def object_list(request, model, template='objlist/object_list.html', link=False, modal_link=False, modal_edit=False, modal_upload=False, delete_inline=False, can_add=False, can_prioritize=False, num_show=None, view_only=False):
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
    ol = ObjectList(request, request.manager, num_show=num_show)
    if not request.user.is_superuser:
        project = request.user.get_profile()
        logs = project.activitylog_set.filter(content_type__in=log_set)[:ACTIVITY_LOG_LENGTH]
    else:
        logs = ActivityLog.objects.filter(content_type__in=log_set)[:ACTIVITY_LOG_LENGTH]
    return render_to_response(template, {'ol': ol, 
                                         'link': link,
                                         'modal_link': modal_link,
                                         'modal_edit': modal_edit,
                                         'modal_upload': modal_upload,
                                         'delete_inline': delete_inline,
                                         'can_add': can_add, 
                                         'can_prioritize': can_prioritize,
                                         'viewonly': view_only,
                                         'handler': request.path,
                                         'logs': logs},                                         
        context_instance=RequestContext(request)
    )

@login_required
@manager_required    
def basic_object_list(request, model, template='objlist/basic_object_list.html'):
    """
    Request a basic list of objects for which the orphan field specified as a GET parameter is null.
    The template this uses will be rendered in the sidebar controls.
    """
    ol = {}
    if request.GET.get('orphan_field', None) is not None:
        params = {'%s__isnull' %  str(request.GET['orphan_field']): True}
        objects = request.manager.filter(**params)
    else:
        objects = request.manager.all()
    ol['object_list'] = objects
    handler = request.path
    # if path has /basic on it, remove that. 
    if 'basic' in handler:
        handler = handler[0:-6]
    return render_to_response(template, {'ol' : ol, 'type' : model.__name__.lower(), 'handler': handler }, context_instance=RequestContext(request))

@login_required
@transaction.commit_on_success
def priority(request, id,  model, field):
    if request.method == 'POST':
        pks = map(int, request.POST.getlist('id_list[]'))
        _priorities_changed = False
        for obj in model.objects.filter(pk__in=pks).all():
            new_priority = pks.index(obj.pk) + 1
            if obj.priority != new_priority:
                obj.priority = new_priority
                obj.save()
                _priorities_changed = True
    if _priorities_changed:
        messages.info(request, "%s priority updated" % model.__name__)
    return render_to_response('users/refresh.html', context_instance=RequestContext(request))
    
@login_required
@transaction.commit_on_success
def edit_profile(request, form, id=None, template='objforms/form_base.html', action_url=None):
    """
    View for editing user profiles
    """
    if request.GET.get('warning', None) == 'label':
        form.warning_message = "We don't have your address on file yet.  Please update your profile information before printing off shipping labels."
    else:
        form.warning_message = None
    try:
        model = Project
        obj = request.user.get_profile()
        request.project = obj
        request.manager = Project.objects
    except:
        raise Http404
    if id: action_url = '/users/shipping/shipment/%s/send/' % id
    return edit_object_inline(request, obj.pk, model=model, form=form, template=template, action_url=action_url)
    
@login_required
@manager_required
@transaction.commit_on_success
def edit_object_inline(request, id, model, form, template='objforms/form_base.html', modal_upload=False, action_url=None):
    """
    A generic view which displays a form of type ``form`` using the template 
    ``template``, for editing an object of type ``model``, identified by primary 
    key ``id``, which when submitted will update the entry asynchronously through
    AJAX.
    """
    if request.project:
        project = request.project
        project_pk = project.pk
    else:
        project = None
        project_pk = None

    try:
        obj = request.manager.get(pk=id)
    except:
        raise Http404

    if not obj.is_editable():
        raise Http404
    
    form_info = {
        'title': request.GET.get('title', 'Edit %s' % model._meta.verbose_name),
        'sub_title': obj.identity(),
        'action':  request.path,
        'target': 'entry-scratchpad',
        'save_label': 'Save'
    }

    if modal_upload:
        form_info['enctype'] = 'multipart/form-data'

    if request.method == 'POST':
        frm = form(request.POST, instance=obj)
        frm.restrict_by('project', project_pk)
        if frm.is_valid():
            form_info['message'] = '%s (%s) modified' % ( model._meta.verbose_name, obj)
            frm.save()
            messages.info(request, form_info['message'])
            
            ActivityLog.objects.log_activity(request, obj, ActivityLog.TYPE.MODIFY, 
                '%s edited' % ( model._meta.verbose_name,))         
            if modal_upload:
                return render_to_response("users/iframe_refresh.html", context_instance=RequestContext(request))
            if action_url: 
                return HttpResponseRedirect(action_url)
            return render_to_response('users/redirect.html', context_instance=RequestContext(request))
        else:
            return render_to_response(template, {
            'info': form_info, 
            'form' : frm, 
            }, context_instance=RequestContext(request))
    else:
        frm = form(instance=obj, initial=dict(request.GET.items())) # casting to a dict pulls out first list item in each value list
        frm.restrict_by('project', project_pk)
        return render_to_response(template, {
        'info': form_info, 
        'form' : frm,
        }, context_instance=RequestContext(request))
       
       
@login_required
@transaction.commit_on_success
def staff_comments(request, id, model, form, template='objforms/form_base.html', user='staff'):
    try:
        obj = model.objects.get(pk=id)
    except:
        raise Http404

    form_info = {
        'title': 'Add a note to this %s' % model._meta.verbose_name,
        'sub_title': obj.identity(),
        'action':  request.path,
        'target': 'entry-scratchpad',
        'save_label': 'Save'
    }
    if request.method == 'POST':
        frm = form(request.POST, instance=obj)
        try:
            if not obj.comments: base_comments = ''
            else: base_comments = obj.comments
        except:
            base_comments = ''
        if frm.is_valid():
            if user == 'staff':
                author = ' by staff'
                frm.save()
            elif user == 'user' and request.POST.get('comments', None):
                author = ''
                obj.comments = base_comments + '\n\n%s - %s' % \
                    (dateformat.format(timezone.now(), 'Y-m-d P'), request.POST.get('comments'))
                obj.save()
            form_info['message'] = 'comments added to %s (%s)%s' % ( model._meta.verbose_name, obj, author)
            messages.info(request, form_info['message'])
            ActivityLog.objects.log_activity(request, obj, ActivityLog.TYPE.MODIFY, 
                'comments added to %s%s' % ( model._meta.verbose_name, author))            
            return render_to_response('users/redirect.html', context_instance=RequestContext(request))
        else:
            return render_to_response(template, {
            'info': form_info, 
            'form' : frm, 
            }, context_instance=RequestContext(request))
    else:
        frm = form(instance=obj, initial=dict(request.GET.items())) 
        return render_to_response(template, {
        'info': form_info, 
        'form' : frm,
        }, context_instance=RequestContext(request))

@login_required
@transaction.commit_on_success
def remove_object(request, src_id, obj_id, source, obj, dest_id=None, destination=None, reverse=False):
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
        obj, source = source, obj
    
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

    model = obj
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
    src = manager.get(pk=src_id)
    to_remove = obj_manager.get(pk=obj_id)
    # get the display name
    display_name = to_remove.name
    if reverse:
        display_name = src.name

    if src.is_editable():
        #if replace == True or dest.(obj.__name__.lower()) == None
        try:
            getattr(src, obj.__name__.lower())
            setattr(src, obj.__name__.lower(), None)
            if obj.__name__.lower() == "container":
                setattr(src, "container_location", None)
        except AttributeError:
            # attrib didn't exist, append 's' for many field
            try:
                current = getattr(src, '%ss' % obj.__name__.lower())
                # want destination.objects.add(to_add)
                current.remove(to_remove)
                if src.__class__.__name__.lower() == "runlist":
                    src.remove_container(to_remove)
                #setattr(dest, '%ss' % obj.__name__.lower(), current_values)
            except AttributeError:
                message = '%s has not been removed. No Field (tried %s and %s)' % (display_name, obj.__name__.lower(), '%ss' % obj.__name__.lower())
                messages.info(request, message)
                return render_to_response('users/refresh.html', context_instance=RequestContext(request))
                       
        src.save()
        message = '%s removed from %s' % (src, to_remove)
        ActivityLog.objects.log_activity(request, src, ActivityLog.TYPE.MODIFY, 
            '%s removed from %s' % (src._meta.verbose_name, to_remove._meta.verbose_name))
           
    else:
        message = '%s has not been removed, as %s is not editable' % (display_name, src.name)

    messages.info(request, message)

    return render_to_response('users/refresh.html', {
        'info': form_info,
        }, context_instance=RequestContext(request))

@login_required
@manager_required
@transaction.commit_on_success
def delete_object(request, id, model, form, template='objforms/form_base.html'):
    """
    A generic view which displays a form of type ``form`` using the template 
    ``template``, for deleting an object of type ``model``, identified by primary 
    key ``id``, which when submitted will delete the entry asynchronously through
    AJAX.
    """
    if request.project:
        project = request.project
        project_pk = project.pk
    else:
        project = None
        project_pk = None

    try:
        obj = request.manager.get(pk=id)
    except:
        raise Http404

    if not obj.is_deletable():
        raise Http404    

    form_info = {
        'title': 'Delete %s?' % obj.__unicode__(),
        'sub_title': 'The %s (%s) will be deleted' % ( model._meta.verbose_name, obj.__unicode__()),
        'action':  request.path,
        'message': 'Are you sure you want to delete %s "%s"?' % (
            model.__name__, obj.__unicode__()
            ),
        'save_label': 'Delete'
    }
    if request.method == 'POST':
        frm = form(request.POST, instance=obj)
        frm.restrict_by('project', project_pk)
        if request.POST.has_key('_save'):
            form_info['message'] = '%s (%s) deleted' % ( model._meta.verbose_name, obj)
            cascade = False
            if request.POST.get('cascade'):
                cascade = True
            obj.delete(request=request, cascade=cascade)
            messages.info(request, form_info['message'])
            
            # prepare url to redirect after delete. Always return to list
            # Since this view is called from Ajax, the client has to interpret the
            # redirect message and act accordingly
            # example: JSON {"url" : "/path/to/redirect/to"}
            
            if request.user.is_staff:
                url_prefix = 'staff'
            else:
                url_prefix = 'users'
            url_name = "%s-%s-list" % (url_prefix, model.__name__.lower())
            try:
                redirect = reverse(url_name)
            except:
                redirect = request.META['HTTP_REFERER']
            return render_to_response("users/redirect.json", {
            'redirect_to': redirect,
            }, context_instance=RequestContext(request), mimetype="application/json")
        else:
            return render_to_response(template, {
            'info': form_info, 
            'form' : frm, 
            }, context_instance=RequestContext(request))
    else:
        frm = form(instance=obj, initial=None) 
        if 'cascade' in frm.fields:
            frm.fields['cascade'].label = 'Delete all %s associated with this %s.' % (obj.HELP.get('cascade','objects'), model.__name__.lower())
            frm.fields['cascade'].help_text = 'If this box is left unchecked, only the %s will be deleted. %s' % (model.__name__.lower(), obj.HELP.get('cascade_help',''))
        frm.restrict_by('project', project_pk)
        return render_to_response(template, {
        'info': form_info, 
        'form' : frm, 
        'save_label': 'Delete',
        }, context_instance=RequestContext(request))

@login_required
@project_optional
@transaction.commit_on_success
def action_object(request, id, model, form, template="objforms/form_base.html", action=None):
    """
    A generic view which displays a confirmation form and if confirmed, will
    archive the object of type ``model`` identified by primary key ``id``.
    
    If supplied, all instances of ``cascade_models`` (which is a list of tuples 
    of (Model, fk_field)) with a ForeignKey referencing ``model``/``id`` will also
    be archived.
    """
    if request.project:
        project = request.project
        project_pk = project.pk
    else:
        project = None
        project_pk = None
    try:
        obj = model.objects.get(pk=id)
    except:
        raise Http404

    save_label = None
    save_labeled = None
    if action:
        save_label = action[0].upper() + action[1:]
        if save_label[-1:] == 'e': save_labeled = '%sd' % save_label
        elif save_label[-1:] == 'd': save_labeled = '%st' % save_label[:-1]
        else: save_labeled = '%sed' % save_label        

    initial = {}
    form_info = {
        'title': '%s %s?' % (save_label, obj.__unicode__()),
        'sub_title': 'The %s %s will be %s' % (model.__name__, obj.__unicode__(), save_labeled),
        'action':  request.path,
        'target': 'entry-scratchpad',
        'save_label': save_label
    }
    if action == 'archive' and obj.is_closable():
        form_info['message'] = 'Are you sure you want to archive %s "%s"?  ' % (model.__name__, obj.__unicode__())
    elif action == 'send' and obj.is_sendable():
        dewars = obj.dewar_set.all()
        containers = project.container_set.filter(dewar__in=dewars)
        conts = ['%d %s%s' % (containers.filter(kind=num).count(), kind, containers.filter(kind=num) > 1 and 's' or '') for num, kind in Container.TYPE if containers.filter(kind=num).count() ]
        num_crystals = project.crystal_set.filter(container__pk__in=containers).count()
        form_info['sub_title'] = ''
        form_info['message'] = '%d Crystals are being sent in %s (%d Dewar%s).' % \
            (num_crystals, ', '.join(conts), dewars.count(), dewars.count() > 1 and 's' or '') 
        if project: 
            if project.carrier: initial['carrier'] = Carrier.objects.get(pk=project.carrier.pk)
            form_info['update_profile'] = True
            if project.address and project.city and project.province and project.country and project.postal_code:
                msg = '<strong>Return samples to:</strong><small>\n%s\n%s%s\n%s\n%s, %s %s\n%s\nPhone: %s\n%s</small>' % (project.contact_person,
                    project.department and '%s\n' % project.department or '', project.organisation,
                    project.address, project.city, project.province, project.postal_code, project.country,
                    project.contact_phone, project.contact_fax and "Fax: %s" % project.contact_fax or '')
                form.warning_message = msg
                form.error_message = ''
            else:
                form.warning_message = ''
                form.error_message = ["The address we have for your lab is incomplete. Update your profile for return shipping."]
    elif action == 'load' and obj.is_loadable(): pass
    elif action == 'unload' and obj.is_unloadable(): pass 
    elif action == 'return' and obj.is_returnable(): pass
    elif action == 'trash' and obj.is_trashable(): 
        form_info['message'] = 'Are you sure you want to trash %s "%s"?  ' % (model._meta.verbose_name, obj.__unicode__())
    else: raise Http404

    if request.method == 'POST':
        if request.POST.has_key('_updateprofile'):
            return HttpResponseRedirect('/users/profile/edit/%s/' % obj.pk)
        frm = form(request.POST, instance=obj)
        frm.restrict_by('project', project_pk)
        if frm.is_valid():
            form_info['message'] = '%s (%s) modified' % ( model._meta.verbose_name, obj)
            frm.save()
            # if an action ('send', 'close') is specified, the perform the action
            if action:
                if action == 'send': obj.send(request=request)
                if action == 'load': obj.load(request=request)
                if action == 'unload': obj.unload(request=request)
                if action == 'return': obj.returned(request=request)
                if action == 'archive': 
                    obj.archive(request=request)
                    if not obj.project.show_archives and model.__name__ is not 'Data':
                        messages.info(request, form_info['message'])
                        url_name = "users-%s-list" % (model.__name__.lower())   
                        return render_to_response("users/redirect.json", {'redirect_to': reverse(url_name),}, context_instance=RequestContext(request), mimetype="application/json")  
                if action == 'trash': 
                    obj.trash(request=request)    
                    if model.__name__ is not 'Data':
                        messages.info(request, form_info['message'])
                        url_name = "users-%s-list" % (model.__name__.lower())   
                        return render_to_response("users/redirect.json", {'redirect_to': reverse(url_name),}, context_instance=RequestContext(request), mimetype="application/json")
            return render_to_response('users/redirect.html', context_instance=RequestContext(request))
        else:
            return render_to_response('users/refresh.html', context_instance=RequestContext(request))
    else:
        frm = form(instance=obj, initial=initial) 
        frm.restrict_by('project', project_pk)
        if action == 'archive':
            frm.help_text = 'You can access archived objects by editing \n your profile and selecting "Show Archives" '
        return render_to_response(template, {
        'info': form_info, 
        'form' : frm, 
        'save_label': 'Archive',
        }, context_instance=RequestContext(request))
        
@login_required
@manager_required
def shipment_pdf(request, id, model, format):
    """ """
    if model != Project:
        try:
            obj = request.manager.get(pk=id)
        except:
            raise Http404
    else:
        obj = Project.objects.get(pk=id)

    if format == 'protocol':
        containers = obj.project.container_set.filter(dewar__in=obj.dewar_set.all())
        all_experiments = obj.project.experiment_set.filter(pk__in=obj.project.crystal_set.filter(container__dewar__shipment__exact=obj.pk).values('experiment'))
        experiments = list(all_experiments.filter(priority__gte=1).order_by('priority')) + list(all_experiments.exclude(priority__gte=1))
        group = None
        num_crystals = obj.project.crystal_set.filter(container__pk__in=containers).count()

    if format == 'runlist':
        containers = obj.containers.all()
        experiments = Experiment.objects.filter(pk__in=Crystal.objects.filter(container__in=obj.containers.all()).values('experiment')).order_by('priority').reverse()
        group = Project.objects.filter(pk__in=obj.containers.all().values('project'))
        try:
            num_crystals = obj.project.crystal_set.filter(container__pk__in=containers).count()
        except:
            num_crystals = 12

    work_dir = create_cache_dir(obj.label_hash())
    prefix = "%s-%s" % (obj.label_hash(), format)
    pdf_file = os.path.join(work_dir, '%s.pdf' % prefix)
    print pdf_file
    if not os.path.exists(pdf_file) or settings.DEBUG: # remove the True after testing
        # create a file into which the LaTeX will be written
        tex_file = os.path.join(work_dir, '%s.tex' % prefix)
        # render and output the LaTeX into temap_file
        if format == 'protocol' or format == 'runlist':
            if format == 'protocol':
                project = obj.project
            else:
                project = request.project
            tex = loader.render_to_string('users/tex/sample_list.tex', {'project': project, 'group': group, 'shipment' : obj, 'experiments': experiments, 'containers': containers, 'num_crystals': num_crystals })
        elif format == 'label':
            project = model == Project and obj or obj.project
            tex = loader.render_to_string('users/tex/send_labels.tex', {'project': project, 'shipment' : obj})
        elif format == 'return_label':
            project = model == Project and obj or obj.project
            obj = model == Shipment and obj or None
            tex = loader.render_to_string('users/tex/return_labels.tex', {'project': project, 'shipment' : obj})
        f = open(tex_file, 'w')
        f.write(tex)
        f.close()
        
        devnull = file('/dev/null', 'rw')
        stdout = sys.stdout
        stderr = sys.stderr
        if not settings.DEBUG:
            stdout = devnull
            stderr = devnull
        sys.path.append('/usr/local/texlive/2014/bin/x86_64-linux/')
        subprocess.call(['xelatex', '-interaction=nonstopmode', tex_file], 
                        cwd=work_dir,
                        )
        if format == 'protocol' or format == 'runlist':
            subprocess.call(['xelatex', '-interaction=nonstopmode', tex_file], 
                            cwd=work_dir,
                            )
    
    return send_raw_file(request, pdf_file, attachment=True)
        
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
        filename = ('%s-%s.xls' % (project.name, shipment.name)).replace(' ', '_')
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
    

# -------------------------- JSONRPC Methods ----------------------------------------#
import jsonrpc
from jsonrpc import jsonrpc_method, exceptions

@jsonrpc_method('lims.add_data')
@apikey_required
def add_data(request, data_info):
    
    # check if project_id is provided if not check if project_name is provided
    if data_info.get('project_id') is not None:
        data_owner = Project.objects.get(pk=data_info['project_id'])   
    elif data_info.get('project_name') is not None:
        try:
            data_owner = Project.objects.get(name=data_info['project_name'])
        except:
            data_owner = create_project(username=data_info['project_name'])
        data_info['project_id'] = data_owner.pk
        del data_info['project_name']
    else:
        raise exceptions.InvalidRequestError('Unknown Project')
    
    # check if beamline_id is provided if not check if beamline_name is provided
    if data_info.get('beamline_id') is None:
        if data_info.get('beamline_name') is not None:
            try:
                beamline = Beamline.objects.get(name=data_info['beamline_name'])
                del data_info['beamline_name']
                data_info['beamline_id'] = beamline.pk
            except Beamline.DoesNotExist:
                raise exceptions.InvalidRequestError('Unknown Beamline')
      
    # convert unicode to str
    new_info = {}
    for k,v in data_info.items():
        if k == 'url':
            v = create_download_key(v, data_info['project_id'])
        new_info[str(k)] = v
    try:
        # if id is provided, make sure it is owned by current owner otherwise add new entry
        # to prevent overwriting other's stuff
        force_update = False
        if new_info.get('id') is not None:
            try:
                new_obj = data_owner.data_set.get(pk=new_info.get('id'))
                force_update = True
                new_info['created'] = timezone.now()
            except:
                new_info['id'] = None
        
        new_obj = Data(**new_info)
        new_obj.save(force_update=force_update)

        # check type, and change status accordingly
        if new_obj.crystal is not None:
            if new_obj.kind == Result.RESULT_TYPES.SCREENING:
                new_obj.crystal.change_screen_status(Crystal.EXP_STATES.COMPLETED)
            elif new_obj.kind == Result.RESULT_TYPES.COLLECTION:
                new_obj.crystal.change_collect_status(Crystal.EXP_STATES.COMPLETED)
        if new_obj.experiment is not None:
            if new_obj.experiment.status == Experiment.STATES.ACTIVE:
                new_obj.experiment.change_status(Experiment.STATES.PROCESSING)
        ActivityLog.objects.log_activity(request, new_obj, ActivityLog.TYPE.CREATE, "Dataset uploaded from beamline")
        return {'data_id': new_obj.pk}
    except Exception, e:
        raise exceptions.ServerError(e.message)


@jsonrpc_method('lims.add_report')
@apikey_required
def add_report(request, report_info):
    
    # check if project_id is provided if not check if project_name is provided
    if report_info.get('project_id') is not None:
        report_owner = Project.objects.get(pk=report_info['project_id'])   
    elif report_info.get('project_name') is not None:
        try:
            report_owner = Project.objects.get(name=report_info['project_name'])
        except:
            report_owner = create_project(username=report_info['project_name'])
        report_info['project_id'] = report_owner.pk
        del report_info['project_name']
    else:
        raise exceptions.InvalidRequestError('Unknown Project')
          
    # convert unicode to str
    new_info = {}
    for k,v in report_info.items():
        if k == 'url':
            v = create_download_key(v, report_info['project_id'])
        new_info[str(k)] = v
    try:
        # if id is provided, make sure it is owned by current owner otherwise add new entry
        # to prevent overwriting other's stuff
        force_update = False
        if new_info.get('id') is not None:
            try:
                new_obj = report_owner.result_set.get(pk=new_info.get('id'))
                force_update = True
                new_info['created'] = timezone.now()
            except:
                new_info['id'] = None
        
        new_obj = Result(**new_info)
        new_obj.save(force_update=force_update)

        ActivityLog.objects.log_activity(request, new_obj, ActivityLog.TYPE.CREATE, "New analysis Report uploaded from beamline")
        return {'result_id': new_obj.pk}
    except Exception, e:
        raise exceptions.ServerError(e.message)

@jsonrpc_method('lims.add_scan')
@apikey_required
def add_scan(request, scan_info):
    # check if project_id is provided if not check if project_name is provided
    if scan_info.get('project_id') is not None:
        scan_owner = Project.objects.get(pk=scan_info['project_id'])   
    elif scan_info.get('project_name') is not None:
        try:
            scan_owner = Project.objects.get(name=scan_info['project_name'])
        except:
            scan_owner = create_project(username=scan_info['project_name'])
        scan_info['project_id'] = scan_owner.pk
        del scan_info['project_name']
    else:
        raise exceptions.InvalidRequestError('Unknown Project')

    # check if beamline_id is provided if not check if beamline_name is provided
    if scan_info.get('beamline_id') is None:
        if scan_info.get('beamline_name') is not None:
            try:
                beamline = Beamline.objects.get(name=scan_info['beamline_name'])
                del scan_info['beamline_name']
                scan_info['beamline_id'] = beamline.pk
            except Beamline.DoesNotExist:
                raise exceptions.InvalidRequestError('Unknown Beamline')

    # convert unicode to str
    new_info = {}
    for k,v in scan_info.items():
        new_info[str(k)] = v
    try:
        # if id is provided, make sure it is owned by current owner otherwise add new entry
        # to prevent overwriting other's stuff
        force_update = False
        if new_info.get('id') is not None:
            try:
                new_obj = scan_owner.scan_result_set.get(pk=new_info.get('id'))
                force_update = True
                new_info['created'] = timezone.now()
            except:
                new_info['id'] = None
        new_obj = ScanResult(**new_info) 
        try:
            new_obj.experiment = new_obj.crystal.experiment
        except:
            pass
        new_obj.save(force_update=force_update)
        
        ActivityLog.objects.log_activity(request, new_obj, ActivityLog.TYPE.CREATE, "New scan uploaded from beamline")
        return {'scan_id': new_obj.pk}
    except Exception, e:
        raise exceptions.ServerError(e.message)
    

@jsonrpc_method('lims.add_strategy')
@apikey_required
def add_strategy(request, stg_info):
    info = {}
    # convert unicode to str
    for k,v in stg_info.items():
        info[smart_str(k)] = v
    try:
        new_obj = Strategy(**info)
        new_obj.save()
        ActivityLog.objects.log_activity(request, new_obj, ActivityLog.TYPE.CREATE, 
           "New strategy uploaded from beamline" % new_obj)
        return {'strategy_id': new_obj.pk}
    except Exception, e:
        raise exceptions.ServerError(e.message)
