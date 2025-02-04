import os
from datetime import datetime, timedelta
import msgpack
import json
import functools
import operator

import requests
from django import http

from django.conf import settings
from django.contrib.auth import get_user_model
from django.db.models import Q

from django.http import JsonResponse, HttpResponse
from django.urls import reverse_lazy
from django.utils import timezone, dateparse
from django.utils.decorators import method_decorator
from django.utils.encoding import force_str
from django.views.decorators.csrf import csrf_exempt
from django.views.generic import View
from django.contrib.auth.mixins import LoginRequiredMixin

from mxlive.utils.signing import Signer, InvalidSignature
from mxlive.utils.data import parse_frames

from .middleware import get_client_address
from mxlive.lims.models import ActivityLog
from mxlive.lims.models import Beamline, Dewar
from mxlive.lims.models import Data, DataType
from mxlive.lims.models import Project, Session
from mxlive.lims.templatetags.converter import humanize_duration
from mxlive.staff.models import UserList, RemoteConnection

if settings.LIMS_USE_SCHEDULE:
    HALF_SHIFT = int(getattr(settings, 'HOURS_PER_SHIFT', 8)/2)

PROXY_URL = getattr(settings, 'DOWNLOAD_PROXY_URL', '')
MAX_CONTAINER_DEPTH = getattr(settings, 'MAX_CONTAINER_DEPTH', 2)


def make_secure_path(path):
    # Download  key
    url = PROXY_URL + '/data/create/'
    r = requests.post(url, data={'path': path})
    if r.status_code == 200:
        key = r.json()['key']
        return key
    else:
        raise ValueError('Unable to create SecurePath')


@method_decorator(csrf_exempt, name='dispatch')
class AuthenticationRequiredMixin(object):
    """
    Mixin to verify that the user is logged-in without any redirects
    """

    def dispatch(self, request, *args, **kwargs):
        if hasattr(request, 'user') and request.user.is_authenticated:
            return super().dispatch(request, *args, **kwargs)
        else:
            return http.HttpResponseForbidden()



@method_decorator(csrf_exempt, name='dispatch')
class AccessList(View):
    """
    Returns list of usernames that should be able to access the remote server referenced by the IP number inferred from
    the request.

    :key: r'^accesslist/$'
    """

    def get(self, request, *args, **kwargs):

        from mxlive.staff.models import UserList
        client_addr = get_client_address(request)

        userlist = UserList.objects.filter(address=client_addr, active=True).first()

        if userlist:
            return JsonResponse(userlist.access_users(), safe=False)
        else:
            return JsonResponse([], safe=False)

    def post(self, request, *args, **kwargs):

        client_addr = get_client_address(request)
        user_list = UserList.objects.filter(address=client_addr, active=True).first()

        tz = timezone.get_current_timezone()
        errors = []

        if user_list:
            data = msgpack.loads(request.body)
            for conn in data:
                try:
                    project = Project.objects.get(username=conn['project'])
                except:
                    errors.append("User '{}' not found.".format(conn['project']))
                status = conn['status']
                try:
                    dt = tz.localize(datetime.strptime(conn['date'], "%Y-%m-%d %H:%M:%S"))
                    r, created = RemoteConnection.objects.get_or_create(name=conn['name'], userlist=user_list, user=project)
                    r.status = status
                    if created:
                        r.created = dt
                    else:
                        r.end = dt
                    r.save()
                except:
                    pass

            return JsonResponse(user_list.access_users(), safe=False)
        else:
            return JsonResponse([], safe=False)


@method_decorator(csrf_exempt, name='dispatch')
class SSHKeys(View):
    """
    Returns SSH keys for specified user  if the remote server referenced by the IP number inferred from
    the request exists.

    :key: r'^keys/<username>$'
    """

    def get(self, request, *args, **kwargs):

        client_addr = get_client_address(request)
        user_list = UserList.objects.filter(address=client_addr, active=True).first()
        user = Project.objects.filter(username=self.kwargs.get('username')).first()

        msg = ''
        if user:
            msg = '\n'.join(user.sshkeys.values_list('key', flat=True)).encode()

        return HttpResponse(msg, content_type='text/plain')


@method_decorator(csrf_exempt, name='dispatch')
class UpdateUserKey(View):
    """
    API for adding a public key to an MxLIVE Project.
    """

    def post(self, request, *args, **kwargs):

        public = request.POST.get('public')
        signer = Signer(public=public)

        value = signer.unsign(kwargs.get('signature'))

        if value == kwargs.get('username'):
            User = get_user_model()
            modified = User.objects.filter(username=kwargs['username']).filter(Q(key__isnull=True) | Q(key='')).update(
                key=public)

            if not modified:
                return http.HttpResponseNotModified()

            ActivityLog.objects.log_activity(request, User.objects.get(username=kwargs['username']),
                                             ActivityLog.TYPE.MODIFY, 'User Key Initialized')
        else:
            return http.HttpResponseForbidden()

        return JsonResponse({})


class LaunchSession(AuthenticationRequiredMixin, View):
    """
    Method to start an MxLIVE Session from the beamline. If a Session with the same name already exists, a new Stretch
    will be added to the Session.
    """

    def post(self, request, *args, **kwargs):
        beamline_name = kwargs.get('beamline')
        session_name = kwargs.get('session')
        project = request.user

        try:
            beamline = Beamline.objects.get(acronym__exact=beamline_name)
        except Beamline.DoesNotExist:
            raise http.Http404("Beamline does not exist.")

        end_time = None
        if settings.LIMS_USE_SCHEDULE:
            now = timezone.now()
            beamtime = project.beamtime.filter(beamline=beamline, start__lte=now + timedelta(hours=HALF_SHIFT),
                                               end__gte=now - timedelta(hours=HALF_SHIFT))
            if beamtime.exists():
                end_time = max(beamtime.values_list('end', flat=True)).isoformat()
            elif not beamline.active:
                end_time = (timezone.now() + timedelta(hours=2)).isoformat()

        session, created = Session.objects.get_or_create(project=project, beamline=beamline, name=session_name)
        if created:
            # Download  key
            try:
                key = make_secure_path(os.path.join(project_name, session.name))
                session.url = key
                session.save()
            except ValueError:
                return http.HttpResponseServerError("Unable to create SecurePath")
        session.launch()
        if created:
            ActivityLog.objects.log_activity(request, session, ActivityLog.TYPE.CREATE, 'Session launched')

        feedback_url = force_str(reverse_lazy('session-feedback', kwargs={'key': session.feedback_key()}))

        session_info = {'session': session.name,
                        'duration': humanize_duration(session.total_time()),
                        'survey': request.build_absolute_uri(feedback_url),
                        'end_time': end_time}
        return JsonResponse(session_info)


class CloseSession(AuthenticationRequiredMixin, View):
    """
    Method to close an MxLIVE Session from the beamline.

    """

    def post(self, request, *args, **kwargs):
        beamline_name = kwargs.get('beamline')
        session_name = kwargs.get('session')
        project = request.user

        try:
            beamline = Beamline.objects.get(acronym__exact=beamline_name)
        except Beamline.DoesNotExist:
            raise http.Http404("Beamline does not exist.")

        try:
            session = project.sessions.get(beamline=beamline, name=session_name)
        except Session.DoesNotExist:
            raise http.Http404("Session does not exist.")

        session.close()
        session_info = {'session': session.name,
                        'duration': humanize_duration(session.stretches.with_duration().last().duration)}
        return JsonResponse(session_info)


KEYS = {
    'container__name': 'container',
    'container__kind__name': 'container_type',
    'group__name': 'group',
    'id': 'id',
    'name': 'name',
    'barcode': 'barcode',
    'comments': 'comments',
    'location__name': 'location',
    'port_name': 'port'
}


def prep_sample(info, **kwargs):
    sample = {
        KEYS.get(key): value
        for key, value in info.items()
    }
    sample.update(**kwargs)
    return sample


class ProjectSamples(AuthenticationRequiredMixin, View):
    """
    :Return: Dictionary for each On-Site sample owned by the User and NOT loaded on another beamline.
    """

    def get(self, request, *args, **kwargs):
        from mxlive.lims.models import Project, Beamline, Container
        beamline_name = kwargs.get('beamline')

        project = request.user

        try:
            beamline = Beamline.objects.get(acronym=beamline_name)
            dewar = beamline.dewars.select_related('container').get(active=True)
        except (Beamline.DoesNotExist, Dewar.DoesNotExist):
            raise http.Http404("Beamline or Automounter does not exist")

        lookups = ['container__{}'.format('__'.join(['parent']*(i+1))) for i in range(MAX_CONTAINER_DEPTH)]
        query = Q(container__status=Container.STATES.ON_SITE)
        query &= (
            functools.reduce(operator.or_, [Q(**{lookup:dewar.container}) for lookup in lookups]) |
            functools.reduce(operator.and_, [Q(**{"{}__isnull".format(lookup):True}) for lookup in lookups])
        )

        sample_list = project.samples.filter(query).order_by('group__priority', 'priority').values(
            'container__name', 'container__kind__name', 'group__name', 'id', 'name', 'barcode', 'comments',
            'location__name', 'container__location__name', 'port_name'
        )
        samples = [prep_sample(sample, priority=i) for i, sample in enumerate(sample_list)]
        return JsonResponse(samples, safe=False)


TRANSFORMS = {
    'file_name': 'filename',
    'exposure_time': 'exposure',
}


class AddReport(AuthenticationRequiredMixin, View):
    """
    Method to add meta-data and JSON details about an AnalysisReport.

    :param username: User__username
    :param data_id: Data objects referenced
    :param score: float
    :param type: str
    :param details: JSON dict
    :param name: str
    :param beamline: Beamline__acronym

    :Return: {'id': < Created AnalysisReport.pk >}
    """

    def post(self, request, *args, **kwargs):
        info = msgpack.loads(request.body, raw=False)

        from mxlive.lims.models import Data, AnalysisReport
        project = request.user
        try:
            data = Data.objects.filter(pk__in=info.get('data_id'))
        except:
            raise http.Http404("Data does not exist")

        # Download  key
        try:
            key = make_secure_path(info.get('directory'))
        except ValueError:
            return http.HttpResponseServerError("Unable to create SecurePath")

        details = {
            'project': project,
            'score': info.get('score') if info.get('score') else 0,
            'kind': info.get('kind', 'Data Analysis'),
            'details': info.get('details'),
            'name': info.get('title'),
            'url': key
        }
        report = AnalysisReport.objects.filter(pk=info.get('id')).first()

        if report:
            project.reports.filter(pk=report.pk).update(**details)
        else:
            report, created = AnalysisReport.objects.get_or_create(**details)

        for d in data:
            report.data.add(d)

        ActivityLog.objects.log_activity(request, report, ActivityLog.TYPE.CREATE, "{} uploaded from {}".format(
            report.name, kwargs.get('beamline', 'beamline')))
        return JsonResponse({'id': report.pk})


class AddData(AuthenticationRequiredMixin, View):
    """
    Method to add meta-data about Data collected on the Beamline.

    :param username: User__username
    :param data_id: If updating an existing Data object
    :param directory: Path to files
    :param energy: float (in keV)
    :param type: str (one of the acronyms defined for a Data Type)
    :param exposure: float (in seconds)
    :param attenuation: float (in percent)
    :param beam_size: float (in microns)
    :param name: str
    :param filename: filename (if single frame) or formattable template (e.g. "test_{:0>4d}.img")
    :param beamline: Beamline__acronym
    :param sample_id: If known
    :param frames: frames collected (e.g. "1-4,8,10-99"),
    :param start_time:  Starting time for data acquisition. If omitted, will be now - frames * exposure time
    :param end_time: End time for data acquisition. If omitted and start_time, is provided,
                     will be start_time + frames * exposure_time, otherwise it will be now

    :Return: {'id': < Created Data.pk >}
    """

    def post(self, request, *args, **kwargs):
        info = msgpack.loads(request.body, raw=False)
        beamline_name = kwargs.get('beamline')
        project = request.user

        try:
            beamline = Beamline.objects.get(acronym=beamline_name)
        except:
            raise http.Http404("Beamline does not exist")

        # Download  key
        try:
            key = make_secure_path(info.get('directory'))
        except ValueError:
            return http.HttpResponseServerError("Unable to create SecurePath")

        session = beamline.active_session()
        sample = project.samples.filter(pk=info.get('sample_id')).first()
        data = Data.objects.filter(pk=info.get('id')).first()

        details = {
            'session': (session and session.project == project) and session or None,
            'project': project,
            'beamline': beamline,
            'url': key,
            'sample': sample,
            'group': sample and sample.group or None,
        }

        base_fields = ['energy', 'frames', 'file_name', 'exposure_time', 'attenuation', 'name', 'beam_size']
        details.update({f: info.get(f in TRANSFORMS and TRANSFORMS[f] or f) for f in base_fields})
        details.update(kind=DataType.objects.get_by_natural_key(info['type']))
        num_frames = 1
        if info.get('frames'):
            num_frames = len(parse_frames(info['frames']))
            details.update(num_frames=num_frames)

        # Set start and end time for dataset
        end_time = timezone.now() if 'end_time' not in info else dateparse.parse_datetime(info['end_time'])
        start_time = (
            end_time - timedelta(seconds=(num_frames*info['exposure_time']))
        ) if 'start_time' not in info else dateparse.parse_datetime(info['start_time'])
        details.update(start_time=start_time, end_time=end_time)

        for k in ['sample_id', 'group', 'port', 'frames', 'energy', 'filename', 'exposure', 'attenuation',
                  'container', 'name', 'directory', 'type', 'id']:
            if k in info:
                info.pop(k)

        details['meta_data'] = info

        if data:
            Data.objects.filter(pk=data.pk).update(**details)
        else:
            data, created = Data.objects.get_or_create(**details)

        ActivityLog.objects.log_activity(request, data, ActivityLog.TYPE.CREATE, "{} uploaded from {}".format(
            data.kind.name, beamline.acronym))
        return JsonResponse({'id': data.pk})