import re

from django import http
from django.db import transaction
from django.http import JsonResponse, HttpResponseNotFound
from django.utils.decorators import method_decorator
from django.views.decorators.csrf import csrf_exempt
from django.utils import timezone
from django.views.generic import View

from mxlive.utils.mixins import LoginRequiredMixin, AdminRequiredMixin
from . import models

@method_decorator(csrf_exempt, name='dispatch')
class FetchReport(LoginRequiredMixin, View):

    def get(self, request, *args, **kwargs):
        try:
            report = models.AnalysisReport.objects.get(pk=kwargs.get('pk'))
        except models.AnalysisReport.DoesNotExist:
            raise http.Http404("Report does not exist.")

        if report.project != request.user and not request.user.is_superuser:
            raise http.Http404()

        return JsonResponse({'details': report.details}, safe=False)


@method_decorator(csrf_exempt, name='dispatch')
class UpdatePriority(LoginRequiredMixin, View):

    @transaction.atomic
    def post(self, request, *args, **kwargs):
        try:
            group = models.Group.objects.get(pk=request.POST.get('group'))
        except models.Group.DoesNotExist:
            raise http.Http404("Group does not exist.")

        if group.project != request.user:
            raise http.Http404()

        pks = [u for u in request.POST.getlist('samples[]') if u]
        for i, pk in enumerate(pks):
            group.samples.filter(pk=pk).update(priority=i + 1)

        return JsonResponse([], safe=False)


@method_decorator(csrf_exempt, name='dispatch')
class BulkSampleEdit(LoginRequiredMixin, View):

    @transaction.atomic
    def post(self, request, *args, **kwargs):
        errors = []

        group = request.POST.get('group')
        if models.Group.objects.get(pk=group).project.username != self.request.user.username:
            errors.append('You do not have permission to modify these samples.')
            return JsonResponse(errors, safe=False)

        data = {}
        i = 0
        while request.POST.getlist('samples[{}][]'.format(i)):
            info = request.POST.getlist('samples[{}][]'.format(i))
            data[info[0]] = {'name': info[1], 'barcode': info[2], 'comments': info[3]}
            i += 1

        for name in set([v['name'] for v in data.values()]):
            if not re.compile('^[a-zA-Z0-9-_]+$').match(name):
                errors.append('{}: Names cannot contain any spaces or special characters'.format(name.encode('utf-8')))

        names = list(
            models.Sample.objects.filter(group__pk=group).exclude(pk__in=data.keys()).values_list('name', flat=True))
        names.extend([v['name'] for v in data.values()])

        duplicates = set([name for name in names if names.count(name) > 1])
        for name in duplicates:
            errors.append('{}: Each sample in the group must have a unique name'.format(name))

        if not errors:
            for pk, info in data.items():
                models.Sample.objects.filter(pk=pk).update(**info)

        return JsonResponse(errors, safe=False)


class UpdateLocations(AdminRequiredMixin, View):

    def get(self, request, *args, **kwargs):
        container = models.Container.objects.get(pk=self.kwargs['pk'])
        locations = list(container.kind.locations.values_list('pk', 'name'))
        return JsonResponse(locations, safe=False)


class FetchContainerLayout(LoginRequiredMixin, View):
    def get(self, request, *args, **kwargs):
        if request.user.is_superuser:
            qs = models.Container.objects.filter()
        else:
            qs = models.Container.objects.filter(project=self.request.user)

        try:
            container = qs.get(pk=self.kwargs['pk'])
            return JsonResponse(container.get_layout(), safe=False)
        except models.Container.DoesNotExist:
            raise http.Http404('Container Not Found!')


class UnloadContainer(AdminRequiredMixin, View):

    @transaction.atomic
    def post(self, request, *args, **kwargs):
        try:
            container = models.Container.objects.get(pk=self.kwargs['pk'])
            root = container.parent.get_load_root()
        except models.Group.DoesNotExist:
            raise http.Http404("Can't unload Container.")

        models.LoadHistory.objects.filter(child=self.kwargs['pk']).active().update(end=timezone.now())
        models.Container.objects.filter(pk=container.pk).update(parent=None, location=None)

        return JsonResponse(root.get_layout(), safe=False)

