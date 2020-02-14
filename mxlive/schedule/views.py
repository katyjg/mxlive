from django.views.generic import TemplateView
from django.contrib.messages.views import SuccessMessageMixin
from django.urls import reverse_lazy
from django.views.generic import edit
from django.utils import timezone
from django.conf import settings
from django.http import HttpResponse

from mxlive.utils.mixins import AsyncFormMixin, AdminRequiredMixin

from . import models, forms
from mxlive.lims.models import Beamline

from datetime import datetime, timedelta


class CalendarView(TemplateView):
    template_name = 'schedule/schedule.html'

    def get_context_data(self, **kwargs):
        context = super(CalendarView, self).get_context_data(**kwargs)
        try:
            d = '{}-W{}-1'.format(kwargs.get('year', ''), kwargs.get('week', ''))
            now = datetime.strptime(d, '%G-W%V-%w')
        except:
            now = timezone.now()
        (year, week, _) = now.isocalendar()
        context['year'] = year
        context['week'] = week
        context['beamlines'] = Beamline.objects.all()
        context['facility_modes_url'] = settings.FACILITY_MODES
        context['next_week'] = (now + timedelta(days=7)).isocalendar()[:2]
        context['last_week'] = (now - timedelta(days=7)).isocalendar()[:2]
        return context


class BeamlineProjectCreate(AdminRequiredMixin, SuccessMessageMixin, AsyncFormMixin, edit.CreateView):
    form_class = forms.BeamlineProjectForm
    template_name = "modal/form.html"
    model = models.BeamlineProject
    success_url = reverse_lazy('dashboard')
    success_message = "Beamline Project has been created"


class BeamlineProjectEdit(AdminRequiredMixin, SuccessMessageMixin, AsyncFormMixin, edit.UpdateView):
    form_class = forms.BeamlineProjectForm
    template_name = "modal/form.html"
    model = models.BeamlineProject
    success_url = reverse_lazy('dashboard')
    success_message = "Beamline Project has been updated"


class BeamlineProjectDelete(AdminRequiredMixin, SuccessMessageMixin, AsyncFormMixin, edit.DeleteView):
    template_name = "modal/delete.html"
    model = models.BeamlineProject
    success_url = reverse_lazy('dashboard')
    success_message = "Beamline Project has been deleted"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['form_action'] = reverse_lazy('beamline-project-delete', kwargs={'pk': self.object.pk})
        return context


class BeamtimeCreate(AdminRequiredMixin, SuccessMessageMixin, AsyncFormMixin, edit.CreateView):
    form_class = forms.BeamtimeForm
    template_name = "modal/form.html"
    model = models.Beamtime
    success_url = reverse_lazy('dashboard')
    success_message = "Beamtime has been created"

    def get_initial(self):
        initial = super().get_initial()
        try:
            initial['start'] = datetime.strptime(self.request.GET.get('start'), "%Y-%m-%dT%H")
            initial['end'] = datetime.strptime(self.request.GET.get('end'), "%Y-%m-%dT%H") + timedelta(hours=settings.HOURS_PER_SHIFT)
            initial['beamline'] = Beamline.objects.filter(acronym=self.request.GET.get('beamline')).first()
        except:
            pass

        return initial

    def form_valid(self, form):
        access = form.cleaned_data.get('access', [])
        obj = super().form_valid(form)

        for kind in access:
            self.object.access.add(kind)

        return obj


class BeamtimeEdit(AdminRequiredMixin, SuccessMessageMixin, AsyncFormMixin, edit.UpdateView):
    form_class = forms.BeamtimeForm
    template_name = "modal/form.html"
    model = models.Beamtime
    success_url = reverse_lazy('dashboard')
    success_message = "Beamtime has been updated"


class BeamtimeDelete(AdminRequiredMixin, SuccessMessageMixin, AsyncFormMixin, edit.DeleteView):
    template_name = "modal/delete.html"
    model = models.Beamtime
    success_url = reverse_lazy('dashboard')
    success_message = "Beamtime has been deleted"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['form_action'] = reverse_lazy('beamtime-delete', kwargs={'pk': self.object.pk})
        return context