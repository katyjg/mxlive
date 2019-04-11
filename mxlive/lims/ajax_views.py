import re

from django import http
from django.db import transaction
from django.http import JsonResponse
from django.utils.decorators import method_decorator
from django.views.decorators.csrf import csrf_exempt
from django.views.generic import View

from lims import models

@method_decorator(csrf_exempt, name='dispatch')
class FetchReport(View):

    def get(self, request, *args, **kwargs):
        try:
            report = models.AnalysisReport.objects.get(pk=kwargs.get('pk'))
        except models.AnalysisReport.DoesNotExist:
            raise http.Http404("Report does not exist.")

        if report.project != request.user and not request.user.is_superuser:
            raise http.Http404()

        return JsonResponse({'details': report.details}, safe=False)


@method_decorator(csrf_exempt, name='dispatch')
class UpdatePriority(View):

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
            group.sample_set.filter(pk=pk).update(priority=i + 1)

        return JsonResponse([], safe=False)


@method_decorator(csrf_exempt, name='dispatch')
class BulkSampleEdit(View):

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


def update_locations(request):
    container = models.Container.objects.get(pk=request.GET.get('pk', None))
    locations = list(container.kind.container_locations.values_list('pk', 'name'))
    return JsonResponse(locations, safe=False)
