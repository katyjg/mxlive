# Create your views here.

import json
from django.http import HttpResponse, Http404
from django.core import serializers, exceptions
from mxlive.middleware import get_client_address
from django.db.models import Q
from mxlive.apikey.views import apikey_required
from django.utils import timezone
from django.views.decorators.csrf import csrf_exempt

class JsonResponse(HttpResponse):
    def __init__(self, obj, safe=False):
        content = json.dumps(obj, indent=2, ensure_ascii=False)
        super(JsonResponse, self).__init__(
            content, content_type='application/json')


def get_userlist(request, ipnumber=None, *args, **kwargs):
    from staff.models import UserList
    if ipnumber is None:
        client_addr = get_client_address(request)
    else:
        client_addr = ipnumber
    list = UserList.objects.filter(address=client_addr, active=True).first()
    if list:
        return JsonResponse([p.user.username for p in list.users.all()], safe=True)
    else:
        return JsonResponse([], safe=True)


@apikey_required
def get_project_samples(request, *args, **kwargs):
    from lims.models import Project, Container, Crystal, Experiment, Beamline
    from staff.models import Runlist
    project_name = kwargs.get('project')
    beamline_name = kwargs.get('beamline')
    try:
        project = Project.objects.get(name__exact=project_name)
    except Project.DoesNotExist:
        raise Http404("Project does not exist.")

    cnt_list = project.container_set.filter(
        Q(status__exact=Container.STATES.ON_SITE) |
        Q(status__exact=Container.STATES.LOADED))
    xtl_list = project.crystal_set.filter(
        Q(status__exact=Crystal.STATES.ON_SITE) |
        Q(status__exact=Crystal.STATES.LOADED)).order_by('priority')
    exp_list = project.experiment_set.filter(
        Q(status__exact=Experiment.STATES.ACTIVE) |
        Q(status__exact=Experiment.STATES.PROCESSING) |
        Q(status__exact=Experiment.STATES.COMPLETE))
    containers = {}
    crystals = {}
    experiments = {}
    rl_dict = {}

    try:
        beamline = Beamline.objects.get(name__exact=beamline_name)
        active_runlist = beamline.runlist_set.filter(status=Runlist.STATES.LOADED).first()
        if active_runlist:
            rl_dict = active_runlist.json_dict()
    except Beamline.DoesNotExist:
        raise Http404("Beamline does not exist.")
    except Runlist.MultipleObjectsReturned:
        raise Http404("Expected only one RunList object. Found many.")

    for cnt_obj in cnt_list:
        if cnt_obj.pk in rl_dict.get('containers', {}):
            containers[str(cnt_obj.pk)] = rl_dict['containers'][cnt_obj.pk]
        else:
            containers[str(cnt_obj.pk)] = cnt_obj.json_dict()
    for xtl_obj in xtl_list:
        crystals[str(xtl_obj.pk)] = xtl_obj.json_dict()
    for exp_obj in exp_list:
        experiments[str(exp_obj.pk)] = exp_obj.json_dict()

    return JsonResponse({'containers': containers, 'crystals': crystals, 'experiments': experiments})


@apikey_required
def get_active_runlist(request, *args, **kwargs):
    from lims.models import Beamline
    from staff.models import Runlist
    beamline_name = kwargs.get('beamline')
    try:
        # should only be one runlist per beamline
        beamline = Beamline.objects.get(name__exact=beamline_name)
        active_runlist = beamline.runlist_set.filter(status=Runlist.STATES.LOADED).first()
        if active_runlist:
            return JsonResponse(active_runlist.json_dict())
        else:
            return JsonResponse({})
    except Beamline.DoesNotExist:
        raise Http404("Beamline does not exist.")

@csrf_exempt
@apikey_required
def post_data_object(request, *args, **kwargs):
    from lims.models import Project, Beamline, ActivityLog, Crystal, Result, SpaceGroup, Experiment
    from lims.views import create_download_key
    model = kwargs.get('model')
    if request.method == 'POST':
        info = json.loads(request.body)

        # check if project is provided
        try:
            project_name = kwargs.get('project')
            owner = Project.objects.get(name=project_name)
            info['project'] = owner
        except Project.DoesNotExist:
            raise Http404('Unknown Project')

        # check if beamline  is provided
        try:
            beamline_name = kwargs.get('beamline')
            beamline = Beamline.objects.get(name=beamline_name)
            info['beamline'] = beamline.pk
        except Beamline.DoesNotExist:
            if model !=  Result:
                raise Http404('Unknown Beamline')

        # Download  key
        if 'url' in info:
            info['url'] = create_download_key(info['url'], info['project'].pk)

        # Check if crystal exists
        if 'crystal_id' in info:
            info['crystal'] = Crystal.objects.filter(project=owner, pk=info.pop('crystal_id')).first()
            if info['crystal']:
                info['experiment'] = info['crystal'].experiment
                info.pop('experiment_id', '')
            else:
                info.pop('crystal')

        if 'experiment_id' in info and not info.get('experiment'):
            info['experiment'] = Experiment.objects.filter(project=owner, pk=info.pop('experiment_id')).first()
            if not info['experiment']:
                info.pop('experiment')

        if 'space_group_id' in info:
            info['space_group'] = SpaceGroup.objects.filter(pk=info.pop('space_group_id')).first()
            if not info['space_group']:
                info.pop('space_group')

        if 'data_id' in info:
            info['data'] = SpaceGroup.objects.filter(pk=info.pop('data_id')).first()
            if not info['data']:
                info.pop('data')

        # Result does not have beamline
        if model == Result:
            info.pop('beamline', '')

        # if id is provided, make sure it is owned by current owner otherwise add new entry
        # to prevent overwriting other's stuff
        obj = model.objects.filter(project=owner, pk=info.get('id')).first()
        import sys
        print >>sys.stderr, model, info.keys()
        if not obj:
            info['created'] = timezone.now()
            obj = model.objects.create(**info)
        else:
            model.objects.filter(pk=obj.pk).update(**info)

        # check type, and change status accordingly
        ActivityLog.objects.log_activity(request, obj, ActivityLog.TYPE.CREATE, "{} uploaded from beamline".format(model.__name__))
        return JsonResponse({'id': obj.pk})
    else:
        raise exceptions.SuspiciousOperation('Method not allowed')
