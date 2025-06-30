from django import http

from django.http import JsonResponse
from django.contrib import messages
from django.urls import reverse
from django.utils import timezone
from django.utils.decorators import method_decorator
from django.views.decorators.cache import never_cache
from django.views.decorators.csrf import csrf_exempt
from django.views.generic import detail, View

from mxlive.lims.models import Beamline, Project, Shipment, LoadHistory
from mxlive.utils.mixins import AdminRequiredMixin
from . import models
from .models import SELECT_DURATION
from ..remote.views import AuthenticationRequiredMixin


@method_decorator(never_cache, name='dispatch')
class PuckLoader(AdminRequiredMixin, detail.DetailView):
    model = Beamline
    template_name = "loader/app.html"

    def get_object(self, queryset=None):
        acronym = self.kwargs.get('beamline')
        return Beamline.objects.get(acronym__iexact=acronym)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        automounter = self.object.active_automounter()
        config, created = models.Config.objects.get_or_create(
            beamline=self.object, automounter=automounter
        )

        if config.check_timeout():
            messages.warning(self.request, f'Puck selection expired: {SELECT_DURATION}s')
        context['config'] = config
        context['projects'] = Project.objects.filter(
            shipments__status=Shipment.STATES.ON_SITE,
        )
        if self.kwargs.get('project'):
            project = Project.objects.filter(name=self.kwargs['project']).first()
            if project:
                context['active_project'] = project
                context['containers'] = project.containers.on_site().order_by('name')
        return context


@method_decorator(csrf_exempt, name='dispatch')
class SelectPuck(AdminRequiredMixin, View):

    def post(self, request, *args, **kwargs):
        beamline = kwargs.get('beamline')
        project = kwargs.get('project')
        puck = kwargs.get('puck')

        beamline = Beamline.objects.get(acronym__iexact=beamline)
        project = Project.objects.get(name__iexact=project)
        puck = project.containers.on_site().filter(pk=puck).first()
        if not puck:
            return JsonResponse({"error": "Puck not found"})

        config, created = models.Config.objects.get_or_create(beamline=beamline, automounter=beamline.active_automounter())

        if not config.automounter.accepts(puck):
            return JsonResponse({'error': "Puck not accepted by automounter"})

        to_select = puck if (config.selected != puck) else None
        if to_select and to_select.location is not None:
            config.select(None)
            return JsonResponse({'error': "Cannot select a loaded puck"})

        config.select(to_select)
        return JsonResponse({
            'url': reverse('project-puck-loader', kwargs={'beamline': beamline.acronym, 'project': project.name})
        })


class LoadPuck(AuthenticationRequiredMixin, View):

    def post(self, request, *args, **kwargs):
        acronym = kwargs.get('beamline')
        position = kwargs.get('position')

        config = models.Config.objects.filter(beamline__acronym=acronym).first()
        if not config:
            return http.HttpResponseBadRequest("Automounter not found")
        if not config.selected:
            return http.HttpResponseBadRequest("No puck selected")
        if config.check_timeout():
            return http.HttpResponseBadRequest("Puck selection expired")

        puck = config.load(position)
        return JsonResponse({'loaded': puck.name, 'location': position})


class UnloadPuck(AuthenticationRequiredMixin, View):

    def post(self, request, *args, **kwargs):
        acronym = kwargs.get('beamline')
        position = kwargs.get('position')

        config = models.Config.objects.filter(beamline__acronym=acronym).first()
        if not config:
            return http.HttpResponseBadRequest("Automounter not found")

        puck = config.get_container(position)
        if not puck:
            return http.HttpResponseBadRequest("No puck found at this location")

        config.unload(puck)
        return JsonResponse({'unloaded': puck.name, 'location': position})


class CheckPending(AdminRequiredMixin, View):

    def get(self, request, *args, **kwargs):
        acronym = kwargs.get('beamline')
        config = models.Config.objects.filter(beamline__acronym=acronym).first()
        config.check_timeout()

        if not config:
            return JsonResponse({'time': 0})

        return JsonResponse({'time': round(config.updated.timestamp(), 0)})
