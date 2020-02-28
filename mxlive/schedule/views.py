from django.views.generic import TemplateView
from django.contrib.messages.views import SuccessMessageMixin
from django.urls import reverse_lazy
from django.views.generic import edit
from django.utils import timezone
from django.conf import settings
from django.db.models import Q
from django.http import JsonResponse

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
        context['beamlines'] = Beamline.objects.filter(simulated=False)
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
    success_url = reverse_lazy('calendar')
    success_message = "Beamtime has been created"

    def get_initial(self):
        initial = super().get_initial()
        try:
            start = datetime.strptime(self.request.GET.get('start'), "%Y-%m-%dT%H")
            end = datetime.strptime(self.request.GET.get('end'), "%Y-%m-%dT%H") + timedelta(hours=settings.HOURS_PER_SHIFT)
            beamline = Beamline.objects.filter(acronym=self.request.GET.get('beamline')).first()
            info = {'start': start, 'end': end, 'beamline': beamline}
            if models.Beamtime.objects.filter(beamline=beamline).filter((
                Q(start__gte=start) & Q(start__lt=end)) | (
                Q(end__lte=end) & Q(end__gt=start)) | (
                Q(start__gte=start) & Q(end__lte=end))).exists():
                    info['warning'] = "Another project is scheduled in this time. Proceeding to schedule this beamtime will remove the existing beamtime."

            initial.update(**info)
        except:
            pass

        return initial

    def form_valid(self, form):
        super().form_valid(form)
        obj = self.object

        models.Beamtime.objects.filter(beamline=obj.beamline).filter(
            Q(start__lt=obj.start) & Q(end__gt=obj.start)).update(**{'end': obj.start})
        models.Beamtime.objects.filter(beamline=obj.beamline).filter(
            Q(start__lt=obj.end) & Q(end__gt=obj.end)).update(**{'start': obj.end})
        models.Beamtime.objects.filter(beamline=obj.beamline).filter((
            Q(start__gte=obj.start) & Q(start__lt=obj.end)) | (
            Q(end__lte=obj.end) & Q(end__gt=obj.start)) | (
            Q(start__gte=obj.start) & Q(end__lte=obj.end))).exclude(pk=obj.pk).delete()

        success_url = self.get_success_url()
        return JsonResponse({'url': success_url})


class BeamtimeEdit(AdminRequiredMixin, SuccessMessageMixin, AsyncFormMixin, edit.UpdateView):
    form_class = forms.BeamtimeForm
    template_name = "modal/form.html"
    model = models.Beamtime
    success_url = reverse_lazy('calendar')
    success_message = "Beamtime has been updated"


class BeamtimeDelete(AdminRequiredMixin, SuccessMessageMixin, AsyncFormMixin, edit.DeleteView):
    template_name = "modal/delete.html"
    model = models.Beamtime
    success_url = reverse_lazy('calendar')
    success_message = "Beamtime has been deleted"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['form_action'] = reverse_lazy('beamtime-delete', kwargs={'pk': self.object.pk})
        return context

    def delete(self, request, *args, **kwargs):
        super().delete(request, *args, **kwargs)
        success_url = self.get_success_url()
        return JsonResponse({'url': success_url})


class SupportCreate(AdminRequiredMixin, SuccessMessageMixin, AsyncFormMixin, edit.CreateView):
    form_class = forms.BeamlineSupportForm
    template_name = "modal/form.html"
    model = models.BeamlineSupport
    success_url = reverse_lazy('calendar')
    success_message = "Beamline Support has been created"

    def get_initial(self):
        initial = super().get_initial()
        dt = self.request.GET.get('date')
        if dt:
            initial['date'] = datetime.strptime(dt, "%Y-%m-%d")

        return initial


class SupportEdit(AdminRequiredMixin, SuccessMessageMixin, AsyncFormMixin, edit.UpdateView):
    form_class = forms.BeamlineSupportForm
    template_name = "modal/form.html"
    model = models.BeamlineSupport
    success_url = reverse_lazy('calendar')
    success_message = "Beamline Support has been updated"


class SupportDelete(AdminRequiredMixin, SuccessMessageMixin, AsyncFormMixin, edit.DeleteView):
    template_name = "modal/delete.html"
    model = models.BeamlineSupport
    success_url = reverse_lazy('calendar')
    success_message = "Beamline Support has been deleted"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['form_action'] = reverse_lazy('support-delete', kwargs={'pk': self.object.pk})
        return context

    def delete(self, request, *args, **kwargs):
        super().delete(request, *args, **kwargs)
        success_url = self.get_success_url()
        return JsonResponse({'url': success_url})


class DowntimeCreate(AdminRequiredMixin, SuccessMessageMixin, AsyncFormMixin, edit.CreateView):
    form_class = forms.DowntimeForm
    template_name = "modal/form.html"
    model = models.Downtime
    success_url = reverse_lazy('calendar')
    success_message = "Downtime has been created"

    def get_initial(self):
        initial = super().get_initial()
        try:
            start = datetime.strptime(self.request.GET.get('start'), "%Y-%m-%dT%H")
            end = datetime.strptime(self.request.GET.get('end'), "%Y-%m-%dT%H") + timedelta(hours=settings.HOURS_PER_SHIFT)
            beamline = Beamline.objects.filter(acronym=self.request.GET.get('beamline')).first()
            info = {'start': start, 'end': end, 'beamline': beamline}

            initial.update(**info)
        except:
            pass

        return initial


class DowntimeEdit(AdminRequiredMixin, SuccessMessageMixin, AsyncFormMixin, edit.UpdateView):
    form_class = forms.DowntimeForm
    template_name = "modal/form.html"
    model = models.Downtime
    success_url = reverse_lazy('calendar')
    success_message = "Downtime has been updated"

    def form_valid(self, form):
        fv = super(DowntimeEdit, self).form_valid(form)
        obj = form.instance
        if form.data.get('submit') == 'Delete':
            obj.delete()
            self.success_message = "Downtime has been deleted"
        return fv

