import json

import requests
from django import http
from django.conf import settings
from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from django.contrib.humanize.templatetags.humanize import naturaltime
from django.contrib.messages.views import SuccessMessageMixin
from django.db import transaction
from django.db.models import Count
from django.http import JsonResponse, Http404, HttpResponseRedirect
from django.urls import reverse, reverse_lazy
from django.utils import timezone
from django.views.generic import edit, detail, View
from formtools.wizard.views import SessionWizardView
from itemlist.views import ItemListView
from proxy.views import proxy_view

from mxlive.utils import filters
from mxlive.utils.mixins import AsyncFormMixin, AdminRequiredMixin, HTML2PdfMixin

from . import forms, models, stats

DOWNLOAD_PROXY_URL = getattr(settings, 'DOWNLOAD_PROXY_URL', "http://mxlive-data/download")


class ProjectDetail(UserPassesTestMixin, detail.DetailView):
    """
    This is the "Dashboard" view. Basic information about the Project is displayed:

    :For superusers, direct to staff.html, with context:
       - shipments: Any Shipments that are Sent or On-site
       - automounters: Any active Dewar objects (Beamline/Automounter)

    :For Users, direct to project.html, with context:
       - shipments: All Shipments that are Draft, Sent, or On-site, plus Returned shipments to bring the total displayed up to seven.
       - sessions: Any recent Session from any beamline
    """
    model = models.Project
    template_name = "users/project.html"
    slug_field = 'username'
    slug_url_kwarg = 'username'

    def test_func(self):
        # Allow access to admin or owner
        return self.request.user.is_superuser or self.get_object() == self.request.user

    def get_object(self, *args, **kwargs):
        # inject username in to kwargs if not already present
        if not self.kwargs.get('username'):
            self.kwargs['username'] = self.request.user.username
        if self.request.user.is_superuser:
            self.template_name = "users/staff.html"
        return super(ProjectDetail, self).get_object(*args, **kwargs)

    def get_context_data(self, **kwargs):
        context = super(ProjectDetail, self).get_context_data(**kwargs)
        if self.request.user.is_superuser:
            filters = {
                'shipment': {
                    'status__in': [models.Shipment.STATES.ON_SITE, models.Shipment.STATES.SENT]
                },
                'data': {
                    'sample__container__shipment__status__in': [
                        models.Shipment.STATES.ON_SITE, models.Shipment.STATES.SENT
                    ]
                },
                'reports': {
                    'data__sample__container__shipment__status__in': [
                        models.Shipment.STATES.ON_SITE, models.Shipment.STATES.SENT
                    ]
                },
                'sessions': {
                    'stretches__end__isnull': True
                }
            }
        else:
            filters = {
                'shipment': {
                    'project': self.request.user,
                    'status__lt': models.Shipment.STATES.ARCHIVED
                },
                'data': {
                    'project': self.request.user,
                    'sample__container__shipment__status__lt': models.Shipment.STATES.ARCHIVED
                },
                'reports': {
                    'project': self.request.user,
                    'data__sample__container__shipment__status__lt': models.Shipment.STATES.ARCHIVED
                },
                'sessions': {
                    'project': self.request.user,
                }
            }

        shipments = models.Shipment.objects.filter(**filters['shipment'])
        shipment_data = dict(models.Data.objects.filter(
            **filters['data']
        ).order_by('sample__container__shipment').values(
            shipment=models.F('sample__container__shipment')
        ).values_list('shipment', Count('shipment')))

        shipment_reports = dict(models.AnalysisReport.objects.filter(
            **filters['reports']
        ).order_by('data__sample__container__shipment').values(
            shipment=models.F('data__sample__container__shipment')
        ).values_list('shipment', Count('shipment')))

        shipment_containers = dict(shipments.values_list('pk', Count('containers')))
        shipment_groups = dict(shipments.values_list('pk', Count('groups')))
        shipment_samples = dict(shipments.values_list('pk', Count('containers__samples')))

        context['shipments'] = [
            (
                shipment,
                {
                    'groups': shipment_groups.get(shipment.pk),
                    'samples': shipment_samples.get(shipment.pk),
                    'containers': shipment_containers.get(shipment.pk),
                    'reports': shipment_reports.get(shipment.pk),
                    'data': shipment_data.get(shipment.pk),
                }
            )
            for shipment in shipments.prefetch_related('project').order_by('status', '-date_received', '-date_shipped')
        ]

        sessions = models.Session.objects.filter(**filters['sessions'])[:7]
        session_data = dict(sessions.values_list('pk', Count('datasets')))
        session_reports = dict(sessions.values_list('pk', Count('datasets__reports')))
        context['sessions'] = [
            (
                session,
                {
                    'data': session_data.get(session.pk),
                    'reports': session_reports.get(session.pk),
                }
            )
            for session in sessions.prefetch_related('project')
        ]

        if self.request.user.is_superuser:
            kinds = models.ContainerLocation.objects.all().filter(accepts__isnull=False).values_list('types', flat=True)
            context['automounters'] = models.Dewar.objects.filter(active=True).prefetch_related(
                'container','beamline').order_by('beamline__name')
            context['containers'] = models.Container.objects.filter(
                kind__in=kinds, dewars__isnull=True, status__gt=models.Container.STATES.DRAFT
            ).order_by('name')

        return context


class ProjectStatistics(UserPassesTestMixin, detail.DetailView):
    """
    This is the "Dashboard" view. Basic information about the Project is displayed:

    :For superusers, direct to staff.html, with context:
       - shipments: Any Shipments that are Sent or On-site
       - automounters: Any active Dewar objects (Beamline/Automounter)

    :For Users, direct to project.html, with context:
       - shipments: All Shipments that are Draft, Sent, or On-site, plus Returned shipments to bring the total displayed up to seven.
       - sessions: Any recent Session from any beamline
    """
    model = models.Project
    template_name = "users/entries/project-statistics.html"
    slug_field = 'username'
    slug_url_kwarg = 'username'

    def test_func(self):
        # Allow access to admin or owner
        return self.request.user.is_superuser or self.get_object() == self.request.user

    def get_object(self, *args, **kwargs):
        # inject username in to kwargs if not already present
        if not self.kwargs.get('username'):
            self.kwargs['username'] = self.request.user
        return super(ProjectStatistics, self).get_object(*args, **kwargs)


class OwnerRequiredMixin(LoginRequiredMixin, UserPassesTestMixin):
    """
    Mixin to limit access to the owner of an object (or superusers).
    Must be used with an object-based View (e.g. DetailView, EditView)
    """
    owner_field = 'project'

    def test_func(self):
        return self.request.user.is_superuser or getattr(self.get_object(), self.owner_field) == self.request.user


class ProjectEdit(UserPassesTestMixin, SuccessMessageMixin, AsyncFormMixin, edit.UpdateView):
    form_class = forms.ProjectForm
    template_name = "modal/form.html"
    model = models.Project
    success_url = reverse_lazy('dashboard')
    success_message = "Your profile has been updated."

    def get_object(self):
        return models.Project.objects.get(username=self.kwargs.get('username'))

    def test_func(self):
        """Allow access to admin or owner"""
        return self.request.user.is_superuser or self.get_object() == self.request.user



class ProjectLabels(AdminRequiredMixin, HTML2PdfMixin, detail.DetailView):
    template_name = "users/pdf/return_labels.html"
    model = models.Project
    slug_field = 'username'
    slug_url_kwarg = 'username'

    def get_template_name(self):
        return self.template_name

    def get_template_context(self):
        object = self.get_object()
        context = {
            'project': object,
            'shipment': object,
            'admin_project': models.Project.objects.filter(is_superuser=True).first()
        }
        return context


class ListViewMixin(LoginRequiredMixin):
    paginate_by = 25
    template_name = "users/list.html"
    link_data = False
    show_project = True

    def get_list_columns(self):
        columns = super().get_list_columns()
        if self.request.user.is_superuser and self.show_project:
            return ['project__name'] + columns
        return columns

    def get_queryset(self):
        selector = {}
        if not self.request.user.is_superuser:
            selector = {'project': self.request.user}
        return super().get_queryset().filter(**selector)

    def page_title(self):
        return self.model._meta.verbose_name_plural.title()


class DetailListMixin(OwnerRequiredMixin):
    add_url = None
    list_filters = []
    paginate_by = 25

    def get_context_data(self, **kwargs):
        c = super(DetailListMixin, self).get_context_data(**kwargs)
        c['object'] = self.get_object()
        c['total_objects'] = self.get_queryset().count()
        return c

    def get_object(self):
        return self.extra_model.objects.get(pk=self.kwargs['pk'])

    def get_queryset(self):
        qs = super(DetailListMixin, self).get_queryset()
        return self.get_object().samples.all()


class ShipmentList(ListViewMixin, ItemListView):
    model = models.Shipment
    list_filters = ['created', 'status']
    list_columns = ['id', 'name', 'date_shipped', 'carrier', 'num_containers', 'status']
    list_search = ['project__username', 'project__name', 'name', 'comments', 'status']
    link_url = 'shipment-detail'
    link_data = False
    ordering = ['status', '-modified']
    paginate_by = 25

    def get_queryset(self):
        if self.request.user.is_superuser:
            return super(ShipmentList, self).get_queryset().filter(
                status__gte=models.Shipment.STATES.SENT)
        return super(ShipmentList, self).get_queryset()


class ShipmentDetail(OwnerRequiredMixin, detail.DetailView):
    model = models.Shipment
    template_name = "users/entries/shipment.html"


class ShipmentLabels(HTML2PdfMixin, ShipmentDetail):
    template_name = "users/pdf/send_labels.html"

    def get_template_name(self):
        if self.request.user.is_superuser:
            template = 'users/pdf/return_labels.html'
        else:
            template = 'users/pdf/send_labels.html'
        return template

    def get_template_context(self):
        object = self.get_object()
        context = {
            'project': object.project,
            'shipment': object,
            'admin_project': models.Project.objects.filter(is_superuser=True).first()
        }
        return context


class ShipmentEdit(OwnerRequiredMixin, SuccessMessageMixin, AsyncFormMixin, edit.UpdateView):
    form_class = forms.ShipmentForm
    template_name = "modal/form.html"
    model = models.Shipment
    success_message = "Shipment has been updated."

    def get_success_url(self):
        return reverse_lazy('shipment-detail', kwargs={'pk': self.object.pk})

    def get_initial(self):
        initial = super(ShipmentEdit, self).get_initial()
        initial.update(project=self.request.user)
        return initial


class ShipmentComments(AdminRequiredMixin, SuccessMessageMixin, AsyncFormMixin, edit.UpdateView):
    form_class = forms.ShipmentCommentsForm
    template_name = "modal/form.html"
    model = models.Shipment
    success_message = "Shipment has been edited by staff."

    def get_success_url(self):
        return self.object.get_absolute_url()

    def form_valid(self, form):
        obj = form.instance
        if form.data.get('submit') == 'Recall':
            obj.unreceive()
            message = "Shipment un-received by staff"
            models.ActivityLog.objects.log_activity(self.request, obj, models.ActivityLog.TYPE.MODIFY, message)
        return super(ShipmentComments, self).form_valid(form)


class ShipmentDelete(OwnerRequiredMixin, SuccessMessageMixin, AsyncFormMixin, edit.DeleteView):
    template_name = "modal/delete.html"
    model = models.Shipment
    success_message = "Shipment has been deleted."
    success_url = reverse_lazy('dashboard')

    def delete(self, request, *args, **kwargs):
        super(ShipmentDelete, self).delete(request, *args, **kwargs)
        success_url = self.get_success_url()
        models.ActivityLog.objects.log_activity(self.request, self.object, models.ActivityLog.TYPE.DELETE,
                                                self.success_message)
        return JsonResponse({'url': success_url})


class SendShipment(ShipmentEdit):
    form_class = forms.ShipmentSendForm

    def get_initial(self):
        initial = super(SendShipment, self).get_initial()
        initial['components'] = models.ComponentType.objects.filter(
            pk__in=self.object.components.values_list('kind__pk'))
        return initial

    def form_valid(self, form):
        components = form.cleaned_data.get('components', [])
        models.Component.objects.filter(
            pk__in=self.object.components.exclude(kind__in=components).values_list('pk')).delete()
        for component in components.exclude(pk__in=self.object.components.values_list('kind__pk')):
            models.Component.objects.create(shipment=self.object, kind=component)

        form.instance.send()
        message = "Shipment sent"
        models.ActivityLog.objects.log_activity(self.request, self.object, models.ActivityLog.TYPE.MODIFY, message)
        return super().form_valid(form)


class ReturnShipment(ShipmentEdit):
    form_class = forms.ShipmentReturnForm
    success_url = reverse_lazy('dashboard')

    def form_valid(self, form):
        obj = form.instance.returned()
        message = "Shipment returned"
        models.ActivityLog.objects.log_activity(self.request, obj, models.ActivityLog.TYPE.MODIFY, message)
        return super(ReturnShipment, self).form_valid(form)


class RecallSendShipment(ShipmentEdit):
    form_class = forms.ShipmentRecallSendForm

    def get_initial(self):
        initial = super(RecallSendShipment, self).get_initial()
        initial['components'] = models.ComponentType.objects.filter(
            pk__in=self.object.components.values_list('kind__pk'))
        return initial

    def form_valid(self, form):
        components = form.cleaned_data.get('components', [])
        models.Component.objects.filter(
            pk__in=self.object.components.exclude(kind__in=components).values_list('pk')).delete()
        for component in components.exclude(pk__in=self.object.components.values_list('kind__pk')):
            models.Component.objects.create(shipment=self.object, kind=component)

        obj = form.instance
        if form.data.get('submit') == 'Recall':
            obj.unsend()
            message = "Shipping recalled"
            models.ActivityLog.objects.log_activity(self.request, obj, models.ActivityLog.TYPE.MODIFY, message)
        return super(RecallSendShipment, self).form_valid(form)


class RecallReturnShipment(ShipmentEdit):
    form_class = forms.ShipmentRecallReturnForm

    def form_valid(self, form):
        obj = form.instance
        if form.data.get('submit') == 'Recall':
            obj.unreturn()
            message = "Shipping recalled by staff"
            models.ActivityLog.objects.log_activity(self.request, obj, models.ActivityLog.TYPE.MODIFY, message)
        return super(RecallReturnShipment, self).form_valid(form)


class ArchiveShipment(ShipmentEdit):
    form_class = forms.ShipmentArchiveForm

    def form_valid(self, form):
        obj = form.instance
        obj.archive()


class ReceiveShipment(ShipmentEdit):
    form_class = forms.ShipmentReceiveForm

    def form_valid(self, form):
        obj = form.instance
        obj.receive()
        message = "Shipment received on-site"
        models.ActivityLog.objects.log_activity(self.request, obj, models.ActivityLog.TYPE.MODIFY, message)
        return super(ReceiveShipment, self).form_valid(form)


class SampleList(ListViewMixin, ItemListView):
    model = models.Sample
    list_filters = ['modified']
    list_columns = ['id', 'name', 'comments', 'container', 'location']
    list_search = ['project__name', 'name', 'barcode', 'comments']
    link_url = 'sample-detail'
    ordering = ['-created', '-priority']
    ordering_proxies = {}
    list_transforms = {}


class SampleDetail(OwnerRequiredMixin, SuccessMessageMixin, AsyncFormMixin, edit.UpdateView):
    model = models.Sample
    form_class = forms.SampleForm
    template_name = "users/entries/sample.html"
    success_url = reverse_lazy('sample-list')
    success_message = "Sample has been updated"


class SampleEdit(OwnerRequiredMixin, SuccessMessageMixin, AsyncFormMixin, edit.UpdateView):
    form_class = forms.SampleForm
    template_name = "modal/form.html"
    model = models.Sample
    success_url = reverse_lazy('sample-list')
    success_message = "Sample has been updated."

    def get_success_url(self):
        return ""


class SampleDelete(OwnerRequiredMixin, SuccessMessageMixin, AsyncFormMixin, edit.DeleteView):
    success_url = reverse_lazy('dashboard')
    template_name = "modal/delete.html"
    model = models.Sample
    success_message = "Sample has been deleted."

    def delete(self, request, *args, **kwargs):
        super(SampleDelete, self).delete(request, *args, **kwargs)
        models.ActivityLog.objects.log_activity(self.request, self.object, models.ActivityLog.TYPE.DELETE,
                                                self.success_message)
        return JsonResponse({'url': self.success_url})

    def get_context_data(self, **kwargs):
        context = super(SampleDelete, self).get_context_data(**kwargs)
        context['form_action'] = reverse_lazy('sample-delete', kwargs={'pk': self.object.pk})
        return context


class ContainerList(ListViewMixin, ItemListView):
    model = models.Container
    list_filters = ['modified', 'kind', 'status']
    list_columns = ['name', 'id', 'shipment', 'kind', 'capacity', 'num_samples', 'status']
    list_search = ['project__name', 'name', 'comments']
    link_url = 'container-detail'
    ordering = ['-created']
    ordering_proxies = {}
    list_transforms = {}


class ContainerDetail(DetailListMixin, SampleList):
    extra_model = models.Container
    template_name = "users/entries/container.html"
    list_columns = ['name', 'barcode', 'group', 'location', 'comments']
    link_url = 'sample-edit'
    link_attr = 'data-form-link'
    show_project = False
    detail_target = '#modal-target'

    def page_title(self):
        object = self.get_object()
        return 'Samples in {}'.format(object.name)

    def get_list_filters(self):
        filters = super().get_list_filters()
        if self.get_object().has_children():
            filters.append('container')
        return filters

    def get_object(self):
        obj = super(ContainerDetail, self).get_object()
        if obj.status != self.extra_model.STATES.DRAFT:
            self.detail_ajax = False
            self.detail_target = None
        return obj

    def get_detail_url(self, obj):
        if self.get_object().status == self.extra_model.STATES.DRAFT:
            return super(ContainerDetail, self).get_detail_url(obj)
        return reverse_lazy('sample-detail', kwargs={'pk': obj.pk})


class ContainerEdit(OwnerRequiredMixin, SuccessMessageMixin, AsyncFormMixin, edit.UpdateView):
    form_class = forms.ContainerForm
    template_name = "modal/form.html"
    model = models.Container
    success_message = "Container has been updated."

    def get_initial(self):
        initial = super(ContainerEdit, self).get_initial()
        initial.update(project=self.request.user)
        return initial

    def get_success_url(self):
        return self.object.get_absolute_url()


class ContainerLoad(AdminRequiredMixin, ContainerEdit):
    form_class = forms.ContainerLoadForm
    template_name = "modal/form.html"

    def form_valid(self, form):
        data = form.cleaned_data
        location = data.get('location')
        parent = data['parent']
        root = parent.get_load_root()

        if location:
            models.LoadHistory.objects.create(child=self.object, parent=data['parent'], location=location)
        else:
            parent = None
            models.LoadHistory.objects.filter(child=self.object).active().update(end=timezone.now())

        models.Container.objects.filter(pk=self.object.pk).update(parent=parent, location=location)
        return JsonResponse(root.get_layout(), safe=False)


class LocationLoad(AdminRequiredMixin, ContainerEdit):
    form_class = forms.LocationLoadForm
    success_message = "Container has been loaded"

    def get_initial(self):
        initial = super(LocationLoad, self).get_initial()
        initial.update(location=self.object.kind.locations.get(name=self.kwargs['location']))
        return initial

    def form_valid(self, form):
        data = form.cleaned_data
        models.Container.objects.filter(pk=data['child'].pk).update(
            parent=self.object, location=data['location']
        )
        models.LoadHistory.objects.create(child=data['child'], parent=self.object, location=data['location'])

        root = self.object.get_load_root()
        return JsonResponse(root.get_layout(), safe=False)


class EmptyContainers(AdminRequiredMixin, edit.UpdateView):
    form_class = forms.EmptyContainers
    template_name = "modal/form.html"
    model = models.Project
    success_message = "Containers have been removed for {username}."
    success_url = reverse_lazy('dashboard')

    def get_object(self, queryset=None):
        return models.Project.objects.get(username=self.kwargs.get('username'))

    def get_initial(self):
        initial = super(EmptyContainers, self).get_initial()
        initial['parent'] = models.Container.objects.get(pk=self.kwargs.get('pk'))
        return initial

    def form_valid(self, form):
        data = form.cleaned_data
        root = data['parent'].get_load_root()
        containers = self.object.containers.filter(parent=data.get('parent'))
        models.LoadHistory.objects.filter(child__in=containers).active().update(end=timezone.now())
        containers.update(**{'location': None, 'parent': None})
        return JsonResponse(root.get_layout(), safe=False)


class ContainerDelete(OwnerRequiredMixin, SuccessMessageMixin, AsyncFormMixin, edit.DeleteView):
    success_url = reverse_lazy('dashboard')
    template_name = "modal/delete.html"
    model = models.Container
    success_message = "Container has been deleted."

    def delete(self, request, *args, **kwargs):
        super(ContainerDelete, self).delete(request, *args, **kwargs)
        models.ActivityLog.objects.log_activity(self.request, self.object, models.ActivityLog.TYPE.DELETE,
                                                self.success_message)
        return JsonResponse({'url': self.success_url})


class GroupList(ListViewMixin, ItemListView):
    model = models.Group
    list_filters = ['modified', 'status']
    list_columns = ['id', 'name', 'kind', 'plan', 'num_samples', 'status']
    list_search = ['project__name', 'comments', 'name']
    link_url = 'group-detail'
    ordering = ['-modified', '-priority']
    ordering_proxies = {}
    list_transforms = {}


def movable(val, record):
    return "<span class='cursor'><i class='movable ti ti-move'></i> {}</span>".format(val or "")


class GroupDetail(DetailListMixin, SampleList):
    extra_model = models.Group
    template_name = "users/entries/group.html"
    list_columns = ['priority', 'name', 'barcode', 'container_and_location', 'comments']
    list_transforms = {
        'priority': movable,
    }
    link_url = 'sample-edit'
    link_attr = 'data-form-link'
    detail_target = '#modal-target'

    def page_title(self):
        object = self.get_object()
        if 'project' in self.list_columns:
            self.list_columns.pop(0)
        return 'Samples in {}'.format(object.name)

    def get_object(self):
        obj = super(GroupDetail, self).get_object()
        if obj.status != self.extra_model.STATES.DRAFT:
            self.detail_ajax = False
            self.detail_target = None
        return obj

    def get_detail_url(self, obj):
        if self.get_object().status == self.extra_model.STATES.DRAFT:
            return super(GroupDetail, self).get_detail_url(obj)
        return reverse_lazy('sample-detail', kwargs={'pk': obj.pk})


class GroupEdit(OwnerRequiredMixin, SuccessMessageMixin, AsyncFormMixin, edit.UpdateView):
    form_class = forms.GroupForm
    template_name = "users/forms/group-edit.html"
    model = models.Group
    success_message = "Group has been updated."
    success_url = reverse_lazy('group-list')

    def get_initial(self):
        self.original_name = self.object.name
        return super(GroupEdit, self).get_initial()

    def form_valid(self, form):
        resp = super(GroupEdit, self).form_valid(form)
        for s in self.object.samples.all():
            if self.original_name in s.name:
                models.Sample.objects.filter(pk=s.pk).update(name=s.name.replace(self.original_name, self.object.name))
        return JsonResponse({})


class GroupDelete(OwnerRequiredMixin, SuccessMessageMixin, AsyncFormMixin, edit.DeleteView):
    success_url = reverse_lazy('dashboard')
    template_name = "modal/delete.html"
    model = models.Group
    success_message = "Group has been deleted."

    def delete(self, request, *args, **kwargs):
        group = self.get_object()
        super(GroupDelete, self).delete(request, *args, **kwargs)
        models.ActivityLog.objects.log_activity(self.request, group, models.ActivityLog.TYPE.DELETE,
                                                self.success_message)
        return JsonResponse({'url': group.shipment.get_absolute_url()})


class DataList(ListViewMixin, ItemListView):
    model = models.Data
    list_filters = ['modified', 'kind', 'beamline']
    list_columns = ['id', 'name', 'sample', 'frame_sets', 'session__name', 'energy', 'beamline', 'kind', 'modified']
    list_search = ['id', 'name', 'beamline__name', 'sample__name', 'frames', 'project__name', 'modified']
    link_url = 'data-detail'
    link_field = 'name'
    link_attr = 'data-link'
    ordering = ['-modified']
    list_transforms = {}

    def get_queryset(self):
        return super(DataList, self).get_queryset().defer('meta_data', 'url')


class DataDetail(OwnerRequiredMixin, detail.DetailView):
    model = models.Data
    template_name = "users/entries/data.html"


def format_score(val, record):
    return "{:.2f}".format(val)


class ReportList(ListViewMixin, ItemListView):
    model = models.AnalysisReport
    list_filters = ['modified', 'kind' ]
    list_columns = ['id','kind', 'score', 'modified']
    list_search = ['project__username', 'name', 'data__name']
    link_field = 'id'
    link_url = 'report-detail'
    ordering = ['-modified']
    ordering_proxies = {}
    list_transforms = {
        'score': format_score
    }

    def get_queryset(self):
        return super().get_queryset().defer('details', 'url')


class ReportDetail(OwnerRequiredMixin, detail.DetailView):
    model = models.AnalysisReport
    template_name = "users/entries/report.html"


class ShipmentDataList(DataList):
    template_name = "users/entries/shipment-data.html"
    lookup = 'group__shipment__pk'
    detail_model = models.Shipment

    def page_title(self):
        return 'Data in {} - {}'.format(self.object.__class__.__name__.title(), self.object)

    def get_queryset(self):
        try:
            self.object = self.detail_model.objects.get(**self.kwargs)
        except self.detail_model.DoesNotExist:
            raise Http404
        qs = super().get_queryset()
        return qs.filter(**{self.lookup: self.object.pk})

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context_name = self.object.__class__.__name__.lower()
        context[context_name] = self.object
        return context


class ShipmentReportList(ReportList):
    template_name = "users/entries/shipment-reports.html"
    lookup = 'data__group__shipment__pk'
    detail_model = models.Shipment

    def page_title(self):
        return 'Reports in {} - {}'.format(self.object.__class__.__name__.title(), self.object)

    def get_queryset(self):
        try:
            self.object = self.detail_model.objects.get(**self.kwargs)
        except self.detail_model.DoesNotExist:
            raise Http404
        qs = super().get_queryset()
        return qs.filter(**{self.lookup: self.object.pk})

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context_name = self.object.__class__.__name__.lower()
        context[context_name] = self.object
        return context


class SessionDataList(ShipmentDataList):
    template_name = "users/entries/session-data.html"
    lookup = 'session__pk'
    detail_model = models.Session


class SessionReportList(ShipmentReportList):
    template_name = "users/entries/session-reports.html"
    lookup = 'data__session__pk'
    detail_model = models.Session


class ActivityLogList(ListViewMixin, ItemListView):
    model = models.ActivityLog
    list_filters = ['created', 'action_type']
    list_columns = ['created', 'action_type', 'user_description', 'ip_number', 'object_repr', 'description']
    list_search = ['description', 'ip_number', 'content_type__name', 'action_type']
    ordering = ['-created']
    ordering_proxies = {}
    list_transforms = {}
    link_url = 'activitylog-detail'
    link_attr = 'data-link'
    detail_target = '#modal-target'


def format_total_time(val, record):
    return int(val) or ""


FromYearListFilter = filters.DateLimitFilterFactory(
    models.Session, field_name='created', filter_title='From Year', limit=filters.DATE_LIMIT.LEFT
)
ToYearListFilter = filters.DateLimitFilterFactory(
    models.Session, field_name='created', filter_title='To Year', limit=filters.DATE_LIMIT.RIGHT
)

class SessionList(ListViewMixin, ItemListView):
    model = models.Session
    list_filters = [FromYearListFilter, ToYearListFilter, 'beamline']
    list_columns = ['name', 'created', 'beamline', 'total_time', 'num_datasets', 'num_reports']
    list_search = ['beamline__acronym', 'project__username', 'name']
    link_field = 'name'
    ordering = ['-created']
    list_transforms = {
        'total_time': format_total_time
    }
    link_url = 'session-detail'


class SessionDetail(OwnerRequiredMixin, detail.DetailView):
    model = models.Session
    template_name = "users/entries/session.html"


class SessionStatistics(AdminRequiredMixin, detail.DetailView):
    model = models.Session
    template_name = "users/entries/session-statistics.html"


class BeamlineDetail(AdminRequiredMixin, detail.DetailView):
    model = models.Beamline
    template_name = "users/entries/beamline.html"

    def get_context_data(self, **kwargs):
        context = super(BeamlineDetail, self).get_context_data(**kwargs)
        context['projects'] = {}
        # }
        #     project: self.object.active_automounter().children.filter(project=project)
        #     for project in models.Project.objects.filter(
        #         pk__in=self.object.active_automounter().children.values_list('project', flat=True)).distinct()
        # }
        return context


def format_time(val, record):
    return naturaltime(val) or ""


class BeamlineHistory(AdminRequiredMixin, ListViewMixin, ItemListView):
    model = models.Session
    list_filters = ['project', ]
    list_columns = ['created', 'name', 'total_time', 'num_datasets', 'num_reports']
    list_transforms = {
        'start': format_time,
        'end': format_time,
        'total_time': lambda x,y: '{:0.2g} hrs'.format(x),
    }
    list_search = ['beamline', 'project', 'name']
    ordering = ['pk']
    detail_url_kwarg = 'pk'
    link_url = 'session-detail'

    def get_queryset(self):
        qs = super(BeamlineHistory, self).get_queryset()
        return qs.filter(beamline__pk=self.kwargs['pk'])


class ParameterStatistics(BeamlineDetail):
    template_name = "users/entries/beamline-statistics.html"

    def get_context_data(self, **kwargs):
        context = super(ParameterStatistics, self).get_context_data(**kwargs)
        yearly = 'year' not in self.kwargs
        filters = {} if yearly else {'created__year': self.kwargs.get('year')}

        context['year'] = self.kwargs.get('year')
        context['years'] = stats.get_data_periods(period='year')

        context['report'] = stats.parameter_stats(self.object, **filters)
        return context

    def page_title(self):
        if self.kwargs.get('year'):
            return '{} Monthly Parameters'.format(self.kwargs['year'])
        else:
            return 'Yearly Parameters'


class UsageStatistics(BeamlineDetail):
    template_name = "users/entries/beamline-usage.html"

    def get_context_data(self, **kwargs):
        context = super(UsageStatistics, self).get_context_data(**kwargs)
        yearly = 'year' not in self.kwargs
        period = 'year' if yearly else 'month'

        context['year'] = self.kwargs.get('year')
        context['years'] = stats.get_data_periods(period='year')

        filters = {} if yearly else {'created__year': self.kwargs.get('year')}
        context['report'] = stats.usage_stats(self.object, period=period, **filters)
        return context

    def page_title(self):
        if self.kwargs.get('year'):
            return '{} Monthly Usage'.format(self.kwargs['year'])
        else:
            return 'Yearly Usage'


class DewarEdit(OwnerRequiredMixin, SuccessMessageMixin, AsyncFormMixin, edit.UpdateView):
    form_class = forms.DewarForm
    template_name = "modal/form.html"
    model = models.Dewar
    success_url = reverse_lazy('dashboard')
    success_message = "Comments have been updated."


class ShipmentCreate(LoginRequiredMixin, SessionWizardView):
    form_list = [('shipment', forms.AddShipmentForm),
                 ('containers', forms.ShipmentContainerForm),
                 ('groups', forms.ShipmentGroupForm)]
    template_name = "modal/wizard.html"

    def get_form_initial(self, step):
        if step == 'shipment':
            today = timezone.now()
            day_count = self.request.user.shipments.filter(
                created__year=today.year, created__month=today.month, created__day=today.day
            ).count()
            return self.initial_dict.get(step, {
                'project': self.request.user,
                'name': '{} #{}'.format(timezone.now().strftime('%Y-%b%d'), day_count + 1)
            })
        elif step == 'groups':
            containers_data = self.storage.get_step_data('containers')
            if containers_data:
                names = containers_data.getlist('containers-name')
                kinds = containers_data.getlist('containers-kind')
                containers = [(names[i], kinds[i]) for i in range(len(names))]
                return self.initial_dict.get(step, {'containers': containers})
        return self.initial_dict.get(step, {})

    @transaction.atomic
    def done(self, form_list, **kwargs):
        project = None
        for label, form in kwargs['form_dict'].items():
            if label == 'shipment':
                data = form.cleaned_data
                if self.request.user.is_superuser:
                    data.update({
                        'project': data.get('project'),
                        'staff_comments': 'Created by staff!'
                    })
                else:
                    data.update({
                        'project': self.request.user
                    })
                project = data['project']
                self.shipment, created = models.Shipment.objects.get_or_create(**data)
            elif label == 'containers':
                for i, name in enumerate(form.cleaned_data['name_set']):
                    data = {
                        'kind': models.ContainerType.objects.get(pk=form.cleaned_data['kind_set'][i]),
                        'name': name.upper(),
                        'shipment': self.shipment,
                        'project': project
                    }
                    container, created = models.Container.objects.get_or_create(**data)
            elif label == 'groups':
                if self.request.POST.get('submit') == 'Fill':
                    for i, container in enumerate(self.shipment.containers.all()):
                        group = self.shipment.groups.create(name=container.name, project=project, priority=(i+1))
                        group_samples = [
                            models.Sample(
                                name='{}_{}'.format(group.name, j+1), group=group, project=project, container=container,
                                location=location
                            )
                            for j, location in enumerate(container.kind.locations.all())
                        ]
                        models.Sample.objects.bulk_create(group_samples)
                else:
                    for i, name in enumerate(form.cleaned_data['name_set']):
                        if name:
                            data = {
                                field: form.cleaned_data['{}_set'.format(field)][i]
                                for field in ['name', 'kind', 'comments', 'plan', 'absorption_edge']
                            }
                            data.update({
                                'resolution': None if not form.cleaned_data.get('resolution_set') else float(form.cleaned_data['resolution_set'][i]),
                                'shipment': self.shipment,
                                'project': project,
                                'priority': i + 1
                            })
                            group, created = models.Group.objects.get_or_create(**data)

        # Staff created shipments should be sent and received automatically.
        if self.request.user.is_superuser:
            self.shipment.send()
            self.shipment.receive()
        return JsonResponse({'url': reverse('shipment-detail', kwargs={'pk': self.shipment.pk})})


class ShipmentAddContainer(LoginRequiredMixin, SuccessMessageMixin, AsyncFormMixin, edit.FormView):
    form_class = forms.ShipmentContainerForm
    template_name = "users/forms/add-wizard.html"
    success_message = "Shipment updated"

    def get_initial(self):
        initial = super(ShipmentAddContainer, self).get_initial()
        initial['shipment'] = models.Shipment.objects.get(pk=self.kwargs.get('pk'))
        return initial

    @transaction.atomic
    def form_valid(self, form):
        data = form.cleaned_data
        data['shipment'].containers.exclude(pk__in=[int(pk) for pk in data['id_set'] if pk]).delete()
        for i, name in enumerate(data['name_set']):
            if data['id_set'][i]:
                models.Container.objects.filter(pk=int(data['id_set'][i])).update(name=data['name_set'][i])
            else:
                info = {
                    'kind': models.ContainerType.objects.get(pk=form.cleaned_data['kind_set'][i]),
                    'name': name.upper(),
                    'shipment': data['shipment'],
                    'project': self.request.user
                }
                container, created = models.Container.objects.get_or_create(**info)
        return HttpResponseRedirect(reverse('shipment-add-groups', kwargs={'pk': self.kwargs.get('pk')}))


class ShipmentAddGroup(LoginRequiredMixin, SuccessMessageMixin, AsyncFormMixin, edit.CreateView):
    model = models.Group
    form_class = forms.ShipmentGroupForm
    template_name = "users/forms/add-wizard.html"
    success_message = "Groups in shipment updated"

    def get_initial(self):
        initial = super(ShipmentAddGroup, self).get_initial()
        initial['shipment'] = models.Shipment.objects.get(pk=self.kwargs.get('pk'))
        initial['containers'] = [(c.pk, c.kind.pk) for c in initial['shipment'].containers.all()]
        initial['sample_locations'] = json.dumps(
            {g.name: {c.pk: list(c.samples.filter(group=g).values_list('location', flat=True))
                      for c in initial['shipment'].containers.all()}
             for g in initial['shipment'].groups.all()})
        if initial['shipment']:
            initial['containers'] = initial['shipment'].containers.all()
        return initial

    @transaction.atomic
    def form_valid(self, form):
        data = form.cleaned_data
        shipment = data['shipment']
        shipment.groups.exclude(pk__in=[int(v) for v in data['id_set'] if v]).delete()

        for i, name in enumerate(data['name_set']):
            info = {
                field: data['{}_set'.format(field)][i]
                for field in ['name', 'kind', 'plan', 'comments', 'absorption_edge']}
            info.update({
                'resolution': data['resolution_set'][i] and float(data['resolution_set'][i]) or None,
                'shipment': data['shipment'],
                'project': self.request.user,
                'priority': i + 1
            })
            if data['id_set'][i]:
                models.Group.objects.filter(pk=int(data['id_set'][i])).update(**info)
                group = models.Group.objects.get(pk=int(data['id_set'][i]))
            else:
                group, created = models.Group.objects.get_or_create(**info)

        return JsonResponse({})


class SeatSamples(OwnerRequiredMixin, AsyncFormMixin, detail.DetailView):
    template_name = "users/forms/seat-samples.html"
    model = models.Shipment


class ContainerSpreadsheet(LoginRequiredMixin, AsyncFormMixin, detail.DetailView):
    template_name = "users/forms/container-spreadsheet.html"
    model = models.Container

    @transaction.atomic
    def post(self, request, *args, **kwargs):
        if request.user.is_superuser:
            qs = models.Container.objects.filter()
        else:
            qs = models.Container.objects.filter(project=self.request.user)
        try:
            container = qs.get(pk=self.kwargs['pk'])
            samples = json.loads(request.POST.get('samples', '[]'))
            groups = {
                sample['group'] if sample['group'] else sample['name']  # use sample name if group is blank
                for sample in samples
                if sample['name']
            }
            group_map = {}
            for name in groups:
                group, created = models.Group.objects.get_or_create(
                    project=container.project, shipment=container.shipment,
                    name=name,
                )
                group_map[name] = group

            for sample in samples:
                group_name = sample['group'] if sample['group'] else sample['name']  # use name if group is blank
                info = {
                    'name': sample['name'],
                    'group': group_map.get(group_name),
                    'location_id': sample['location'],
                    'container': container,
                    'barcode': sample['barcode'],
                    'comments': sample['comments'],
                }
                if sample.get('name') and sample.get('sample'):  # update entries
                    models.Sample.objects.filter(project=container.project, pk=sample.get('sample')).update(**info)
                elif sample.get('name'):  # create new entry
                    models.Sample.objects.create(project=container.project, **info)
                else:  # delete existing entry
                    models.Sample.objects.filter(
                        project=container.project, location_id=sample['location'], container=container
                    ).delete()

            return JsonResponse({'url': container.get_absolute_url()}, safe=False)
        except models.Container.DoesNotExist:
            raise http.Http404('Container Not Found!')


class ProxyView(View):
    def get(self, request, *args, **kwargs):
        remote_url = DOWNLOAD_PROXY_URL + request.path
        if kwargs.get('section') == 'archive':
            return fetch_archive(request, remote_url)
        return proxy_view(request, remote_url)


def fetch_archive(request, url):
    r = requests.get(url, stream=True)
    if r.status_code == 200:
        resp = http.StreamingHttpResponse(r, content_type='application/x-gzip')
        resp['Content-Disposition'] = r.headers.get('Content-Disposition', 'attachment; filename=archive.tar.gz')
        return resp
    else:
        return http.HttpResponseNotFound()
