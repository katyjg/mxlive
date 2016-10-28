
from datetime import timedelta
from django.conf import settings
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.contrib.contenttypes.models import ContentType
from django.core.urlresolvers import reverse
from django.db import transaction
from django.http import Http404, HttpResponseRedirect
from django.shortcuts import render_to_response, get_object_or_404
from django.template import RequestContext
from django.utils.datastructures import MultiValueDict
from django.utils import timezone
from download.maketarball import create_tar
from download.models import SecurePath
from lims.models import *
from lims.views import admin_login_required, edit_object_inline
from lims.views import manager_required
from objlist.views import ObjectList
from .admin import runlist_site
from .models import Runlist
import os

#sys.path.append(os.path.join('/var/website/cmcf-website/cmcf'))
#from scheduler.models import Visit, Stat, WebStatus
#from scheduler.models import Beamline as CMCFBeamline

ACTIVITY_LOG_LENGTH  = 10 

@login_required
def staff_home(request):
    if not request.user.is_superuser:
        return HttpResponseRedirect(reverse('project-home'))
    
    recent_start = timezone.now() - timedelta(days=7)
    last_login = ActivityLog.objects.last_login(request)
    if last_login is not None:
        if last_login.created < recent_start:
            recent_start = last_login.created       

    statistics = {
        'shipments': {
                'outgoing': Shipment.objects.filter(status__exact=Shipment.STATES.SENT).count(),
                'incoming': Shipment.objects.filter(modified__gte=recent_start).filter(status__exact=Shipment.STATES.RETURNED).count(),
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
                'incoming': Crystal.objects.filter(modified__gte=recent_start).filter(status__exact=Crystal.STATES.RETURNED).count(),
                },
        'runlists':{
                'loaded': Runlist.objects.filter(status__exact=Runlist.STATES.LOADED).count(),
                'completed': Runlist.objects.filter(status__exact=Runlist.STATES.COMPLETED, modified__gte=recent_start).count(),
                'start_date': recent_start,
        },                
    }
    

    return render_to_response('users/staff.html', {
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
            messages.info(request, form_info['message'])           
            return render_to_response("users/redirect.html", context_instance=RequestContext(request)) 
        else:
            return render_to_response(template, {
            'info': form_info, 
            'form' : frm, 
            }, context_instance=RequestContext(request))
    else:
        try:
            obj = model.objects.get(pk=id)
            init_dict = {'barcode': 'SH%04i-%04i' % (obj.pk, obj.shipment.pk)}
            if not obj.storage_location:
                init_dict['storage_location'] = ''
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
    
    if dest.is_editable():
        if destination.__name__ == 'Runlist':
            if obj.__name__ == 'Experiment' or obj.__name__ == 'Project':
                container_list = Container.objects.filter(status__exact=Container.STATES.ON_SITE).exclude(
                    kind__exact=Container.TYPE.CANE
                ).exclude(pk__in=dest.containers.all()).filter(
                    pk__in=obj.objects.get(pk=obj_id).crystal_set.values('container')
                )
                for container in container_list:
                    dest.add_container(container)
                    try:
                        current = getattr(dest, 'containers')
                        current.add(container)
                    except AttributeError:
                        message = '%s has not been added. No Field (tried %s and %s)' % (display_name, lookup_name, '%ss' % lookup_name)
                        messages.info(request, message)
                        return render_to_response('users/refresh.html', context_instance=RequestContext(request))
                
        if loc_id:
            added = dest.container_to_location(to_add, loc_id)
            dest.container_to_location(to_add, loc_id)
            if added:
                try:
                    current = getattr(dest, '%ss' % lookup_name)
                    # want destination.objects.add(to_add)
                    current.add(to_add)
                    #setattr(dest, '%ss' % obj.__name__.lower(), current_values)
                except AttributeError:
                    message = '%s has not been added. No Field (tried %s and %s)' % (display_name, lookup_name, '%ss' % lookup_name)
                    messages.info(request, message)
                    return render_to_response('users/refresh.html', context_instance=RequestContext(request))
            else:
                message = '%s has not been added. Location %s is unavailable.' % (display_name, loc_id)
                messages.info(request, message)
                return render_to_response('users/refresh.html', {
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

    messages.info(request, message)
    return render_to_response('users/refresh.html', {
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
def project_basic_object_list(request, runlist_id, model, template='objlist/basic_object_list.html'):
    """
    Should display name and id for entity, but filter
    to only display projects with containers with unprocessed crystals available to add to a runlist.
    """
    ol = ObjectList(request, request.manager)
    try: 
        runlist = Runlist.objects.get(pk=runlist_id)
    except:
        runlist = None

    if runlist:
        ol.object_list = Project.objects.filter(pk__in=Container.objects.filter(status__exact=Container.STATES.ON_SITE).exclude(pk__in=runlist.containers.all()).exclude(kind__exact=Container.TYPE.CANE).values('project')).distinct()
    
    return render_to_response(template, {'ol': ol, 'type': ol.model.__name__.lower(), 'runlist': runlist_id }, context_instance=RequestContext(request))


@login_required
@manager_required
def container_basic_object_list(request, runlist_id, exp_id, model, template='objlist/basic_object_list.html'):
    """
    Slightly more complex than above. Should display name and id for entity, but filter
    to only display containers with a crystal in the specified experiment.
    """
    ol = ObjectList(request, request.manager)
    try: 
        runlist = Runlist.objects.get(pk=runlist_id)
    except:
        runlist = None

    '''
    try:
        experiment = Experiment.objects.get(pk=exp_id)
    except:
        experiment = None
        ol.object_list = None

    if runlist and experiment:
        ol.object_list = Container.objects.filter(status__exact=Container.STATES.ON_SITE).filter(pk__in=(experiment.crystal_set.all().values('container'))).exclude(pk__in=runlist.containers.all()).exclude(kind__exact=Container.TYPE.CANE)
    elif runlist:
        ol.object_list = Container.objects.filter(status__exact=Container.STATES.ON_SITE).exclude(pk__in=runlist.containers.all()).exclude(kind__exact=Container.TYPE.CANE)
    '''
    try:
        project = Project.objects.get(pk=exp_id)
    except:
        project = None
        ol.object_list = None
        
    if runlist and project:
        ol.object_list = Container.objects.filter(status__exact=Container.STATES.ON_SITE).filter(project__exact=project).exclude(pk__in=runlist.containers.all()).exclude(kind__exact=Container.TYPE.CANE)
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
                #tar_file = os.path.join(CACHE_DIR, path_obj.key, '%s.tar.gz' % (data.name))
                # if not os.path.exists(tar_file):
                #     try:
                #         threads[data.name] = threading.Thread(target=create_tar,
                #                                               args=[path_obj.path, tar_file],
                #                                               kwargs={'data_dir':True})
                #         threads[data.name].start()
                #         msg = "A tar file is being created for dataset %s.  Depending on the number of images, it may be awhile before it is available to download." % data.name
                #         messages.info(request, msg)
                #     except OSError:
                #         raise Http404
                messages.info(request, "Download enabled for {}".format(path_obj.path))
                data.toggle_download(True)
            if action == 2:
                obj = get_object_or_404(SecurePath, key=data.url)
                # msg = "The tar file has been deleted for dataset %s." % data.name
                # obj = get_object_or_404(SecurePath, key=data.url)
                # fname = os.path.join(CACHE_DIR, obj.key, '%s.tar.gz' % data.name)
                # if os.path.exists(fname):
                #     os.remove(fname)
                # elif os.path.exists('%s-tmp' % fname):
                #     os.remove('%s-tmp' % fname)
                # else:
                #     msg = "The tar file for dataset %s could not be removed because it does not exist." % data.name
                # messages.info(request, msg)
                messages.info(request, "Download disabled for {}".format(obj.path))
                data.toggle_download(False)
            
    return render_to_response('users/refresh.html')

@login_required
@transaction.commit_on_success
def edit_profile(request, form, id=None, template='objforms/form_base.html'):
    """
    View for editing user profiles
    """
    try:
        model = Project
        obj = Project.objects.get(pk=id)
        request.project = obj
        request.manager = Project.objects
    except:
        raise Http404
    return edit_object_inline(request, obj.pk, model=model, form=form, template=template, action_url='/staff/users')



@login_required
def object_history(request, model, id, template='objlist/generic_list.html'):
    ol = model.objects.filter(beamline__exact=model.objects.get(pk=id).beamline)
    log_set = [
        ContentType.objects.get_for_model(model).pk, 
    ]
    logs = ActivityLog.objects.filter(content_type__in=log_set)[:ACTIVITY_LOG_LENGTH]
    return render_to_response(template, {'ol': ol, 
                                         'handler': request.path,
                                         'logs': logs},
        context_instance=RequestContext(request)
    )

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
            form_info['message'] = 'Once unloaded, containers can be added or removed from the runlist before it is loaded again.'

    if request.method == 'POST':
        frm = form(request.POST, instance=obj)
        if request.POST.has_key('_save'):
            if action:
                if action == 'review': obj.review(request=request)
                if action == 'load': 
                    obj.load(request=request)
                    clone_info = {}
                    for param in ['beamline','comments','left','right','middle']:
                        clone_info[param] = getattr(obj, param)
                    clone = Runlist(**clone_info)
                    clone.name = 'RL'
                    for project in Project.objects.filter(pk__in=obj.containers.all().values('project')).distinct():
                        clone.name += '-%s' % project.name
                    clone.status = Runlist.STATES.CLOSED
                    clone.save()
                    clone.containers = obj.containers.all()
                    clone.save()
                if action == 'unload': 
                    obj.unload(request=request)
                    messages.info(request, 'Runlist (%s) unloaded from %s automounter.  Changes can now be made.' % (obj.name, obj.beamline))
                    #url_name = "staff-%s-list" % (model.__name__.lower()) 
                    #return render_to_response("users/redirect.json", {'redirect_to': reverse(url_name),}, context_instance=RequestContext(request), mimetype="application/json")   
            return render_to_response('users/refresh.html')
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


@admin_login_required
@transaction.commit_on_success
def create_project(request, form, template='users/forms/new_base.html'):
    import slap
    from django.contrib.auth import get_user_model

    form_info = {
        'title': 'New Account',
        'action': request.path,
    }

    if request.method == 'POST':
        frm = form(request.POST)
        if frm.is_valid():
            data = frm.cleaned_data
            user_info = {
                k: data.pop(k, '')
                for k in ['username', 'password', 'first_name', 'last_name']
                if k in data
            }
            # Make sure user with username does not already exist
            User = get_user_model()
            if User.objects.filter(username=user_info.get('username')).exists():
                user_info.pop('username', '')

            info = slap.add_user(user_info)
            info['email'] = data.get('contact_email', '')
            info.pop('password')

            # create local user
            obj = User.objects.create(**info)
            data['user'] = obj
            data['name'] = obj.username

            proj = Project.objects.create(**data)

            info_msg = 'New Account {} added'.format(proj)

            ActivityLog.objects.log_activity(
                request, obj, ActivityLog.TYPE.CREATE, info_msg
            )
            messages.info(request, info_msg)
            # messages are simply passed down to the template via the request context
            return render_to_response("users/redirect.html", context_instance=RequestContext(request))
        else:
            return render_to_response(template, {
                'info': form_info,
                'form': frm,
            }, context_instance=RequestContext(request))
    else:
        frm = form(initial=None)
        return render_to_response(template, {
            'info': form_info,
            'form': frm,
        }, context_instance=RequestContext(request))