import json
from django.http import HttpResponse, Http404
from django import http
from django.core import serializers, exceptions
from middleware import get_client_address
from django.db.models import Q
from django.utils import timezone
from django.views.decorators.csrf import csrf_exempt
from django.utils.decorators import method_decorator
import decimal

from django.views.generic import View
from django.http import JsonResponse
from django.contrib.auth import get_user_model

from lims.models import ActivityLog

from signing import Signer


@method_decorator(csrf_exempt, name='dispatch')
class VerificationMixin(object):

    def is_valid(self, request, **kwargs):
        assert kwargs.get('username') and kwargs.get('signature'), "Must provide a username and a signature."
        User = get_user_model()
        try:
            user = User.objects.get(username=kwargs.get('username'))
        except User.DoesNotExist:
            raise http.Http404("User not found")

        signer = Signer(public=user.key)
        value = signer.unsign(kwargs.get('signature'))
        return value == kwargs.get('username')

    def dispatch(self, request, *args, **kwargs):
        if self.is_valid(request, **kwargs):
            return super(VerificationMixin, self).dispatch(request, *args, **kwargs)
        return http.HttpResponseNotAllowed()


@method_decorator(csrf_exempt, name='dispatch')
class UpdateUserKey(View):

    def post(self, request, *args, **kwargs):

        public = request.POST.get('public')
        signer = Signer(public=public)

        value = signer.unsign(kwargs.get('signature'))

        if value == kwargs.get('username'):
            User = get_user_model()
            modified = User.objects.filter(username=kwargs['username'], key__isnull=True).update(key=public)

            if not modified:
                return http.HttpResponseNotModified()

            ActivityLog.objects.log_activity(request, User.objects.get(username=kwargs['username']),
                                         ActivityLog.TYPE.MODIFY, 'User Key Initialized')
        else:
            return http.HttpResponseNotAllowed()

        return http.HttpResponse()


class LaunchSession(VerificationMixin, View):

    def post(self, request, *args, **kwargs):
        from lims.models import Project, Beamline, Session
        project_name = kwargs.get('username')
        beamline_name = kwargs.get('beamline')
        session_name = kwargs.get('session')
        try:
            project = Project.objects.get(username__exact=project_name)
        except Project.DoesNotExist:
            raise http.Http404("Project does not exist.")

        try:
            beamline = Beamline.objects.get(acronym__exact=beamline_name)
        except Beamline.DoesNotExist:
            raise http.Http404("Beamline does not exist.")

        session, created = Session.objects.get_or_create(project=project, beamline=beamline, name=session_name)
        session.launch()
        if created:
            ActivityLog.objects.log_activity(request, session, ActivityLog.TYPE.CREATE, 'Session Started')

        return http.HttpResponse()


class CloseSession(VerificationMixin, View):

    def post(self, request, *args, **kwargs):
        from lims.models import Project, Beamline, Session
        project_name = kwargs.get('username')
        beamline_name = kwargs.get('beamline')
        session_name = kwargs.get('session')
        try:
            project = Project.objects.get(username__exact=project_name)
        except Project.DoesNotExist:
            raise http.Http404("Project does not exist.")

        try:
            beamline = Beamline.objects.get(acronym__exact=beamline_name)
        except Beamline.DoesNotExist:
            raise http.Http404("Beamline does not exist.")

        try:
            session = project.session_set.filter(beamlinle=beamline, name=session_name)
        except Session.DoesNotExist:
            raise http.Http404("Session does not exist.")

        session.end()

        return http.HttpResponse()


class ActiveLayout(VerificationMixin, View):

    def get(self, request, *args, **kwargs):
        from lims.models import Beamline, Dewar
        beamline_name = kwargs.get('beamline')
        try:
            # should only be one active layout per beamline
            beamline = Beamline.objects.get(name__exact=beamline_name)
            active_layout = Dewar.objects.filter(active=True, beamline=beamline).first()
            if active_layout:
                return JsonResponse(active_layout.json_dict())
            else:
                return JsonResponse({})
        except Beamline.DoesNotExist:
            raise http.Http404("Beamline does not exist.")


class ProjectSamples(VerificationMixin, View):

    def get(self, request, *args, **kwargs):
        from lims.models import Project, Beamline
        project_name = kwargs.get('username')
        beamline_name = kwargs.get('beamline')
        layout_dict = {}
        try:
            project = Project.objects.get(username__exact=project_name)
        except Project.DoesNotExist:
            raise http.Http404("Project does not exist.")

        try:
            beamline = Beamline.objects.get(acronym=beamline_name)
            active_layout = beamline.active_automounter()
            if active_layout:
                layout_dict = active_layout.json_dict()
        except:
            raise http.Http404("Beamline does not exist")

        container_list = project.container_set.filter(Q(pk__in=active_layout.children.values_list('pk',flat=True)) |
                                                      Q(parent__in=active_layout.children.all()))
        sample_list = project.sample_set.filter(container__in=container_list).order_by('priority')
        group_list = project.group_set.filter(pk__in=sample_list.values_list('group__pk',flat=True)).order_by('priority')

        containers = {}
        samples = {}
        groups = {}

        for container_obj in container_list:
            if container_obj.pk in layout_dict.get('containers', {}):
                containers[str(container_obj.pk)] = layout_dict['containers'][container_obj.pk]
            else:
                containers[str(container_obj.pk)] = container_obj.json_dict()
        for sample_obj in sample_list:
            samples[str(sample_obj.pk)] = sample_obj.json_dict()
        for group_obj in group_list:
            groups[str(group_obj.pk)] = group_obj.json_dict()

        return JsonResponse([s.json_dict() for s in sample_list])


class AddData(VerificationMixin, View):

    def post(self, request, *args, **kwargs):
        from lims.models import Project, Beamline, ActivityLog, Sample, Result, SpaceGroup, Group, Data
        model = kwargs.get('model')
        if request.method == 'POST':
            info = json.loads(request.body)

            # check if project is provided
            try:
                project_name = kwargs.get('project')
                owner = Project.objects.get(name=project_name)
                info['project'] = owner
            except Project.DoesNotExist:
                raise http.Http404('Unknown Project')

            # check if beamline  is provided
            if model != Result:
                try:
                    beamline_name = kwargs.get('beamline')
                    beamline = Beamline.objects.get(name=beamline_name)
                    info['beamline'] = beamline
                except Beamline.DoesNotExist:
                    raise http.Http404('Unknown Beamline')

            # Download  key
            if 'url' in info:
                # FIXME: Send path information to data server and receive a url back.
                #info['url'] = create_download_key(info['url'], info['project'].pk)
                pass

            # Check if crystal exists
            if 'crystal_id' in info:
                info['crystal'] = Sample.objects.filter(project=owner, pk=info.pop('crystal_id')).first()
                if info['crystal']:
                    info['experiment'] = info['crystal'].experiment
                    info.pop('experiment_id', '')
                else:
                    info.pop('crystal')

            if 'experiment_id' in info and not info.get('experiment'):
                info['experiment'] = Group.objects.filter(project=owner, pk=info.pop('experiment_id')).first()
                if not info['experiment']:
                    info.pop('experiment')

            if 'space_group_id' in info:
                info['space_group'] = SpaceGroup.objects.filter(pk=info.pop('space_group_id')).first()
                if not info['space_group']:
                    info.pop('space_group')

            if 'data_id' in info:
                info['data'] = Data.objects.filter(pk=info.pop('data_id')).first()
                if not info['data']:
                    info.pop('data')

            # if id is provided, make sure it is owned by current owner otherwise add new entry
            # to prevent overwriting other's stuff
            obj = model.objects.filter(project=owner, pk=info.get('id')).first()
            if not obj:
                info['created'] = timezone.now()
                obj = model.objects.create(**info)
            else:
                model.objects.filter(pk=obj.pk).update(**info)

            # check type, and change status accordingly
            ActivityLog.objects.log_activity(request, obj, ActivityLog.TYPE.CREATE,
                                             "{} uploaded from beamline".format(model.__name__))
            return JsonResponse({'id': obj.pk})
        else:
            raise exceptions.SuspiciousOperation('Method not allowed')


def json_encode_decimal(obj):
    if isinstance(obj, decimal.Decimal):
        return str(obj)
    raise TypeError(repr(obj) + " is not JSON serializable")


class JsonResponse(http.HttpResponse):
    def __init__(self, obj, safe=False):
        content = json.dumps(obj, indent=2, ensure_ascii=False, default=json_encode_decimal)
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
