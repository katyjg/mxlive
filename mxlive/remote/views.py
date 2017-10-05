import json
from django import http
from django.conf import settings
from middleware import get_client_address
from django.views.decorators.csrf import csrf_exempt
from django.utils.decorators import method_decorator
import decimal
import requests

from django.views.generic import View
from django.http import JsonResponse
from django.contrib.auth import get_user_model

from lims.models import ActivityLog
from lims.templatetags.converter import humanize_duration

from signing import Signer

IMAGE_URL = settings.IMAGE_PREPEND or ''


@method_decorator(csrf_exempt, name='dispatch')
class AccessList(View):

    def get(self, request, *args, **kwargs):
        from staff.models import UserList
        client_addr = kwargs.get('ipnumber', get_client_address(request))

        list = UserList.objects.filter(address=client_addr, active=True).first()
        if list:
            return JsonResponse([p.username for p in list.users.all()], safe=False)
        else:
            return JsonResponse([], safe=False)


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
            ActivityLog.objects.log_activity(request, session, ActivityLog.TYPE.CREATE, 'Session launched')

        session_info = {'session': session.name,
                        'duration': humanize_duration(session.total_time())}
        return JsonResponse(session_info)


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
            session = project.sessions.get(beamline=beamline, name=session_name)
        except Session.DoesNotExist:
            raise http.Http404("Session does not exist.")

        session.close()
        session_info = {'session': session.name,
                        'duration': humanize_duration(session.stretches.with_duration().last().duration)}
        return JsonResponse(session_info)


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
        from lims.models import Project, Beamline, Container
        project_name = kwargs.get('username')
        beamline_name = kwargs.get('beamline')

        try:
            project = Project.objects.get(username__exact=project_name)
        except Project.DoesNotExist:
            raise http.Http404("Project does not exist.")

        try:
            beamline = Beamline.objects.get(acronym=beamline_name)
        except:
            raise http.Http404("Beamline does not exist")

        sample_list = project.sample_set.filter(container__status=Container.STATES.ON_SITE).order_by('priority')

        return JsonResponse([s.json_dict() for s in sample_list if not s.dewar() or s.dewar() == beamline], safe=False)


TRANSFORMS = {
    'file_name': 'filename',
    'exposure_time': 'exposure',
    'kind': 'type',
}


class AddReport(VerificationMixin, View):

    def post(self, request, *args, **kwargs):
        info = request.POST.copy()

        from lims.models import Project, Data, AnalysisReport
        project_name = kwargs.get('username')
        try:
            project = Project.objects.get(username__exact=project_name)
        except Project.DoesNotExist:
            raise http.Http404("Project does not exist.")

        try:
            data = Data.objects.get(pk=info.get('data_id'))
        except:
            raise http.Http404("Data does not exist")

        sample = data.sample
        group = sample and sample.group or None
        details = {
            'project': project,
            'data': data,
            'sample': sample,
            'group': group,
            'score': info.get('score'),
            'kind': info.get('type'),
            'details': info.get('details'),
            'name': info.get('name')
        }
        report = AnalysisReport.objects.filter(pk=info.get('id')).first()

        if report:
            project.reports.filter(pk=data.pk).update(**details)
        else:
            report, created = AnalysisReport.objects.get_or_create(**details)

        ActivityLog.objects.log_activity(request, report, ActivityLog.TYPE.CREATE, "{} uploaded from {}".format(
            data.get_kind_display(), kwargs.get('beamline', 'beamline')))
        return JsonResponse({'id': report.pk})


import pprint


class AddData(VerificationMixin, View):

    def post(self, request, *args, **kwargs):
        info = request.POST.copy()
        pprint.pprint(info)

        from lims.models import Project, Beamline, Data
        project_name = kwargs.get('username')
        beamline_name = kwargs.get('beamline')
        try:
            project = Project.objects.get(username__exact=project_name)
        except Project.DoesNotExist:
            raise http.Http404("Project does not exist.")

        try:
            beamline = Beamline.objects.get(acronym=beamline_name)
        except:
            raise http.Http404("Beamline does not exist")

        # Download  key
        url = IMAGE_URL + '/data/create/'
        r = requests.post(url, data={'path': info.get('directory')})
        if r.status_code == 200:
            key = r.json()['key']
        else:
            raise http.HttpResponseServerError("Unable to create SecurePath")

        session = beamline.active_session()
        sample = project.sample_set.filter(pk=info.get('sample_id')).first()
        data = Data.objects.filter(pk=info.get('id')).first()

        details = {
            'session': session.project == project and session or None,
            'project': project,
            'beamline': beamline,
            'url': key,
            'sample': sample,
            'group': sample and sample.group or None,
        }

        base_fields = ['energy', 'frames', 'file_name', 'exposure_time', 'kind', 'attenuation', 'name', 'beam_size']
        details.update(**{f: info.get(f in TRANSFORMS and TRANSFORMS[f] or f) for f in base_fields})

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
            data.get_kind_display(), beamline.acronym))
        return JsonResponse({'id': data.pk})
