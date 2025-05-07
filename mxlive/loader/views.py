from django import http
from django.conf import settings
from django.http import JsonResponse
from django.contrib import messages
from django.urls import reverse
from django.utils import timezone
from django.utils.decorators import method_decorator
from django.views.decorators.csrf import csrf_exempt
from django.views.generic import detail, View

from mxlive.lims.models import Beamline, Project, Shipment, LoadHistory
from mxlive.utils.mixins import AdminRequiredMixin
from . import models
from ..remote.views import AuthenticationRequiredMixin


SELECT_DURATION = getattr(settings, 'LOADER_SELECT_DURATION', 5 * 60)  # Default to 5 minutes


class PuckLoader(AdminRequiredMixin, detail.DetailView):
    model = Beamline
    template_name = "loader/app.html"

    def get_object(self, queryset=None):
        acronym = self.kwargs.get('beamline')
        return Beamline.objects.get(acronym__iexact=acronym)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        config, created = models.Config.objects.get_or_create(
            beamline=self.object, automounter=self.object.active_automounter()
        )
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
            messages.error(request, 'Puck not found')
            return JsonResponse({"url": "", "error": "Puck not found"})

        config, created = models.Config.objects.get_or_create(beamline=beamline, automounter=beamline.active_automounter())
        elapsed = timezone.now() - config.modified
        if config.selected and elapsed.total_seconds() > SELECT_DURATION:
            config.selected = None
            config.save()

        if not config.automounter.accepts(puck):
            messages.error(request, 'Puck not accepted by automounter')
            return JsonResponse({"url": "", 'error': "Puck not accepted by automounter"})

        if config.selected != puck:
            config.selected = puck
            config.save()
        elif config.selected == puck:
            config.selected = None
            config.save()
        return JsonResponse({
            'url': reverse('project-puck-loader', kwargs={'beamline': beamline.acronym, 'project': project.name})
        })


class LoadPuck(AuthenticationRequiredMixin, View):
    def post(self, request, *args, **kwargs):
        beamline = kwargs.get('beamline')
        position = kwargs.get('position')

        beamline = Beamline.objects.get(acronym__iexact=beamline)
        config = models.Config.objects.filter(beamline=beamline).first()
        if not config:
            return http.HttpResponseBadRequest("Automounter not found")

        if not config.selected:
            return http.HttpResponseBadRequest("No puck selected")

        elapsed = timezone.now() - config.modified
        if elapsed.total_seconds() > SELECT_DURATION:
            return http.HttpResponseBadRequest("Puck selection expired")

        location = config.automounter.kind.locations.filter(name=position).first()
        if not location:
            return http.HttpResponseBadRequest("Invalid Position")

        puck = config.selected
        config.selected = None
        config.save()

        # remove an existing puck from position
        existing_puck = config.automounter.children.filter(location=location).first()
        if existing_puck:
            LoadHistory.objects.filter(child=existing_puck).active().update(end=timezone.now())
            models.Container.objects.filter(pk=existing_puck.pk).update(parent=None, location=None)

        LoadHistory.objects.create(child=puck, parent=config.automounter, location=location)
        models.Container.objects.filter(pk=puck.pk).update(parent=config.automounter, location=location)

        return JsonResponse({'loaded': puck.name, 'location': location.name})


class UnloadPuck(AuthenticationRequiredMixin, View):
    def post(self, request, *args, **kwargs):
        beamline = kwargs.get('beamline')
        position = kwargs.get('position')

        beamline = Beamline.objects.get(acronym__iexact=beamline)
        config = models.Config.objects.filter(beamline=beamline).first()
        if not config:
            return http.HttpResponseBadRequest("Automounter not found")

        location = config.automounter.kind.locations.filter(name=position).first()
        if not location:
            return http.HttpResponseBadRequest("Invalid location")

        puck = config.automounter.children.filter(location=location).first()
        if not puck:
            return http.HttpResponseBadRequest("No puck found at this location")

        config.selected = puck  # Set the selected puck to the one being unloaded in case we need to reload it
        config.save()

        LoadHistory.objects.filter(child=puck).active().update(end=timezone.now())
        models.Container.objects.filter(pk=puck.pk).update(parent=None, location=None)

        return JsonResponse({'unloaded': puck.name, 'location': location.name})
