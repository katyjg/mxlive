import json

import requests
from django import http
from django.conf import settings
from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from django.contrib.humanize.templatetags.humanize import naturaltime
from django.contrib.messages.views import SuccessMessageMixin
from django.db import transaction
from django.db.models import Count
from django.http import JsonResponse, HttpResponse, Http404
from django.urls import reverse, reverse_lazy
from django.utils import timezone
from django.utils.text import slugify
from django.views.generic import edit, detail, View
from formtools.wizard.views import SessionWizardView
from itemlist.views import ItemListView
from proxy.views import proxy_view

from mxlive.lims import forms, models
from mxlive.utils.mixins import AjaxableResponseMixin, AdminRequiredMixin, HTML2PdfMixin

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

        sessions = models.Session.objects.filter(stretches__end__isnull=True)
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
            context['automounters'] = models.Dewar.objects.filter(active=True).prefetch_related('container',
                                                                                                'beamline').order_by(
                'beamline__name')
            context['containers'] = models.Container.objects.filter(
                kind__in=kinds, dewars__isnull=True, #status__gt=models.Container.STATES.DRAFT
            ).order_by('name')
        else:
            pass
            # referrer = self.request.META.get('HTTP_REFERER')
            # if referrer and re.sub('^https?:\/\/', '', referrer).split('/')[1] == 'login':
            #     context['show_help'] = self.request.user.show_archives
            #     if context['show_help']:
            #         models.Project.objects.filter(username=self.request.user.username).update(show_archives=False)

            # shipments = self.object.shipments.filter(status__lt=models.Shipment.STATES.ARCHIVED)
            # self.object.shipments.filter(status__lt=models.Shipment.STATES.ARCHIVED).order_by('modified')
            # base_set = sh.filter(status__lte=models.Shipment.STATES.ON_SITE).distinct()
            # if base_set.count() < 7:
            #     pks = [s.pk for s in list(
            #         chain(base_set, list(sh.exclude(pk__in=base_set.values_list('pk')))[0:7 - base_set.count()]))]
            # else:
            #     pks = base_set.values_list('pk')
            # context['shipments'] = sh.filter(pk__in=pks).order_by('status', '-modified')
            # sessions = self.get_object().sessions.filter(
            #     pk__in=models.Stretch.objects.recent_days(180).values_list('session__pk', flat=True)).order_by(
            #     '-created')
            # context['sessions'] = sessions.count() < 7 and sessions or sessions[:7]

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


class ProjectEdit(UserPassesTestMixin, SuccessMessageMixin, AjaxableResponseMixin, edit.UpdateView):
    form_class = forms.ProjectForm
    template_name = "forms/modal.html"
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

    def get_list_title(self):
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
    list_columns = ['identity', 'name', 'date_shipped', 'carrier', 'num_containers', 'status']
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


class ShipmentEdit(OwnerRequiredMixin, SuccessMessageMixin, AjaxableResponseMixin, edit.UpdateView):
    form_class = forms.ShipmentForm
    template_name = "forms/modal.html"
    model = models.Shipment
    success_message = "Shipment has been updated."
    success_url = reverse_lazy('shipment-list')

    def get_initial(self):
        initial = super(ShipmentEdit, self).get_initial()
        initial.update(project=self.request.user)
        return initial


class ShipmentComments(AdminRequiredMixin, SuccessMessageMixin, AjaxableResponseMixin, edit.UpdateView):
    form_class = forms.ShipmentCommentsForm
    template_name = "forms/modal.html"
    model = models.Shipment
    success_message = "Shipment has been edited by staff."
    success_url = reverse_lazy('shipment-list')

    def form_valid(self, form):
        obj = form.instance
        if form.data.get('submit') == 'Recall':
            obj.unreceive()
            message = "Shipment un-received by staff"
            models.ActivityLog.objects.log_activity(self.request, obj, models.ActivityLog.TYPE.MODIFY, message)
        return super(ShipmentComments, self).form_valid(form)


class ShipmentDelete(OwnerRequiredMixin, SuccessMessageMixin, AjaxableResponseMixin, edit.DeleteView):
    template_name = "forms/delete.html"
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
        return super(SendShipment, self).form_valid(form)


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
    list_columns = ['identity', 'name', 'comments', 'container', 'location']
    list_search = ['project__name', 'name', 'barcode', 'comments']
    link_url = 'sample-detail'
    ordering = ['-created', '-priority']
    ordering_proxies = {}
    list_transforms = {}


class SampleDetail(OwnerRequiredMixin, SuccessMessageMixin, AjaxableResponseMixin, edit.UpdateView):
    model = models.Sample
    form_class = forms.SampleForm
    template_name = "users/entries/sample.html"
    success_url = reverse_lazy('sample-list')
    success_message = "Sample has been updated"


class SampleEdit(OwnerRequiredMixin, SuccessMessageMixin, AjaxableResponseMixin, edit.UpdateView):
    form_class = forms.SampleForm
    template_name = "forms/modal.html"
    model = models.Sample
    success_url = reverse_lazy('sample-list')
    success_message = "Sample has been updated."


class SampleDone(SampleEdit):
    form_class = forms.SampleDoneForm

    def get_success_url(self):
        return reverse_lazy("shipment-protocol", kwargs={'pk': self.object.container.shipment.pk}) + '?q={}'.format(
            self.object.group.pk)


class SampleDelete(OwnerRequiredMixin, SuccessMessageMixin, AjaxableResponseMixin, edit.DeleteView):
    success_url = reverse_lazy('dashboard')
    template_name = "forms/delete.html"
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
    list_columns = ['identity', 'name', 'shipment', 'kind', 'capacity', 'num_samples', 'status']
    list_search = ['project__name', 'name', 'comments']
    link_url = 'container-detail'
    ordering = ['-created']
    ordering_proxies = {}
    list_transforms = {}


class ContainerDetail(DetailListMixin, SampleList):
    extra_model = models.Container
    template_name = "users/entries/container.html"
    list_columns = ['name', 'barcode', 'group__name', 'location', 'comments']
    link_url = 'sample-edit'
    link_data = True
    show_project = False
    detail_target = '#modal-form'

    def get_list_title(self):
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


class ContainerEdit(OwnerRequiredMixin, SuccessMessageMixin, AjaxableResponseMixin, edit.UpdateView):
    form_class = forms.ContainerForm
    template_name = "forms/modal.html"
    model = models.Container
    success_message = "Container has been updated."

    def get_initial(self):
        initial = super(ContainerEdit, self).get_initial()
        initial.update(project=self.request.user)
        return initial

    def get_success_url(self):
        return reverse_lazy("container-detail", kwargs={'pk': self.object.pk})


class ContainerLoad(AdminRequiredMixin, ContainerEdit):
    form_class = forms.ContainerLoadForm
    template_name = "users/forms/container_load.html"

    def form_valid(self, form):
        data = form.cleaned_data
        if data['parent']:
            models.LoadHistory.objects.create(child=self.object, parent=data['parent'], location=data['location'])
        else:
            models.LoadHistory.objects.filter(child=self.object).active().update(end=timezone.now())
        return super(ContainerLoad, self).form_valid(form)


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
        return super(LocationLoad, self).form_valid(form)


class EmptyContainers(AdminRequiredMixin, edit.UpdateView):
    form_class = forms.EmptyContainers
    template_name = "forms/modal.html"
    model = models.Project
    success_message = "Containers have been removed for {username}."
    success_url = reverse_lazy('dashboard')

    def get_object(self):
        return models.Project.objects.get(username=self.kwargs.get('username'))

    def get_initial(self):
        initial = super(EmptyContainers, self).get_initial()
        initial['parent'] = models.Container.objects.get(pk=self.kwargs.get('pk'))
        return initial

    def form_valid(self, form):
        data = form.cleaned_data
        containers = self.object.containers.filter(parent=data.get('parent'))
        models.LoadHistory.objects.filter(child__in=containers).active().update(end=timezone.now())
        containers.update(**{'location': None, 'parent': None})
        return HttpResponse()


class ContainerDelete(OwnerRequiredMixin, SuccessMessageMixin, AjaxableResponseMixin, edit.DeleteView):
    success_url = reverse_lazy('dashboard')
    template_name = "forms/delete.html"
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
    list_columns = ['identity', 'name', 'kind', 'plan', 'num_samples', 'status']
    list_search = ['project__name', 'comments', 'name']
    link_url = 'group-detail'
    ordering = ['-modified', '-priority']
    ordering_proxies = {}
    list_transforms = {}


def movable(val, record):
    return "<span class='cursor'><i class='movable fa fa-fw fa-1x fa-grip'></i> {}</span>".format(val or "")


class GroupDetail(DetailListMixin, SampleList):
    extra_model = models.Group
    template_name = "users/entries/group.html"
    list_columns = ['priority', 'name', 'barcode', 'container_and_location', 'comments']
    list_transforms = {
        'priority': movable,
    }
    link_url = 'sample-edit'
    link_data = True
    detail_target = '#modal-form'

    def get_list_title(self):
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


class GroupEdit(OwnerRequiredMixin, SuccessMessageMixin, AjaxableResponseMixin, edit.UpdateView):
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
        return resp


class GroupDelete(OwnerRequiredMixin, SuccessMessageMixin, AjaxableResponseMixin, edit.DeleteView):
    success_url = reverse_lazy('dashboard')
    template_name = "forms/delete.html"
    model = models.Group
    success_message = "Group has been deleted."

    def delete(self, request, *args, **kwargs):
        super(GroupDelete, self).delete(request, *args, **kwargs)
        models.ActivityLog.objects.log_activity(self.request, self.object, models.ActivityLog.TYPE.DELETE,
                                                self.success_message)
        return JsonResponse({'url': self.success_url})


class DataList(ListViewMixin, ItemListView):
    model = models.Data
    list_filters = ['modified', 'kind', 'beamline']
    list_columns = ['id', 'name', 'sample', 'frame_sets', 'session__name', 'energy', 'beamline', 'kind', 'modified']
    list_search = ['id', 'name', 'beamline__name', 'sample__name', 'frames', 'project__name', 'modified']
    link_url = 'data-detail'
    link_field = 'name'
    link_data = True
    detail_target = '#modal-form'
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
    list_filters = ['modified', ]
    list_columns = ['identity', 'id', 'kind', 'score', 'modified']
    list_search = ['project__username', 'name', 'data__name']
    link_field = 'identity'
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

    def get_list_title(self):
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

    def get_list_title(self):
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
    link_data = True
    detail_target = '#modal-form'


def format_total_time(val, record):
    return int(val) or ""


class SessionList(ListViewMixin, ItemListView):
    model = models.Session
    list_filters = ['created', 'beamline', ]
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


class BeamlineStatistics(BeamlineDetail):
    template_name = "users/entries/beamline-usage-yearly.html"

    def get_context_data(self, **kwargs):
        c = super(BeamlineStatistics, self).get_context_data(**kwargs)
        c['year'] = self.kwargs.get('year', timezone.now().year)
        return c


class BeamlineUsage(BeamlineDetail):
    template_name = "users/entries/beamline-usage.html"

    def get_context_data(self, **kwargs):
        c = super(BeamlineUsage, self).get_context_data(**kwargs)
        c['year'] = self.kwargs.get('year', timezone.now().year)
        return c


class DewarEdit(OwnerRequiredMixin, SuccessMessageMixin, AjaxableResponseMixin, edit.UpdateView):
    form_class = forms.DewarForm
    template_name = "forms/modal.html"
    model = models.Dewar
    success_url = reverse_lazy('dashboard')
    success_message = "Comments have been updated."


class ShipmentCreate(LoginRequiredMixin, SessionWizardView):
    form_list = [('shipment', forms.AddShipmentForm),
                 ('containers', forms.ShipmentContainerForm),
                 ('groups', forms.ShipmentGroupForm)]
    template_name = "forms/wizard.html"

    def get_form_initial(self, step):
        if step == 'shipment':
            return self.initial_dict.get(step, {'project': self.request.user})
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

        for label, form in kwargs['form_dict'].items():
            if label == 'shipment':
                data = form.cleaned_data
                project = self.request.user.is_superuser and data.get('project') or self.request.user
                data.update({'project': project})
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
                sample_locations = json.loads(form.cleaned_data['sample_locations'])
                for i, name in enumerate(form.cleaned_data['name_set']):
                    if name:
                        data = {field: form.cleaned_data['{}_set'.format(field)][i]
                                for field in ['name', 'kind', 'comments', 'plan', 'absorption_edge']}
                        data.update({
                            'resolution': form.cleaned_data.get('resolution_set') and
                                          form.cleaned_data['resolution_set'][i] and float(
                                form.cleaned_data['resolution_set'][i]) or None,
                            'sample_count': int(form.cleaned_data['sample_count_set'][i]),
                            'shipment': self.shipment,
                            'project': project,
                            'priority': i + 1
                        })
                        group, created = models.Group.objects.get_or_create(**data)
                        to_create = []
                        j = 1
                        slug_map = {slugify(c.name): c.name for c in self.shipment.containers.all()}
                        for c, locations in sample_locations.get(group.name, {}).items():
                            container = self.shipment.containers.get(name__iexact=slug_map.get(c, ''))
                            for sample in locations:
                                name = "{0}_{1:02d}".format(group.name, j)
                                to_create.append(models.Sample(group=group, container=container, location=sample,
                                                               name=name, project=project, priority=j))
                                j += 1
                        models.Sample.objects.bulk_create(to_create)
                        if group.sample_count < group.samples.count():
                            group.sample_count = group.samples.count()
                            group.save()
                if project != self.request.user and self.request.user.is_superuser:
                    self.shipment.send()
                    self.shipment.receive()

        return JsonResponse({'url': reverse('shipment-detail', kwargs={'pk': self.shipment.pk})})


class ShipmentAddContainer(LoginRequiredMixin, SuccessMessageMixin, AjaxableResponseMixin, edit.FormView):
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

        return JsonResponse({'url': reverse('shipment-add-groups', kwargs={'pk': self.kwargs.get('pk')}),
                             'target': '#modal-form'})


class ShipmentAddGroup(LoginRequiredMixin, SuccessMessageMixin, AjaxableResponseMixin, edit.CreateView):
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
        data['shipment'].groups.exclude(pk__in=[int(pk) for pk in data['id_set'] if pk]).delete()
        sample_locations = json.loads(data['sample_locations'])

        # Delete samples removed from containers
        for group, containers in sample_locations.items():
            for container, locations in containers.items():
                models.Sample.objects.filter(container__pk=int(container), group__name=group).exclude(
                    location__in=locations).delete()

        for i, name in enumerate(data['name_set']):
            info = {field: data['{}_set'.format(field)][i] for field in ['name', 'kind', 'plan',
                                                                         'comments', 'absorption_edge']}
            info.update({
                'resolution': data['resolution_set'][i] and float(data['resolution_set'][i]) or None,
                'sample_count': int(data['sample_count_set'][i]),
                'shipment': data['shipment'],
                'project': self.request.user,
                'priority': i + 1
            })
            if data['id_set'][i]:
                models.Group.objects.filter(pk=int(data['id_set'][i])).update(**info)
                group = models.Group.objects.get(pk=int(data['id_set'][i]))
            else:
                group, created = models.Group.objects.get_or_create(**info)
            to_create = []
            j = 1
            priority = max(group.samples.values_list('priority', flat=True) or [0]) + 1
            names = []
            for c, locations in sample_locations.get(group.name, {}).items():
                container = models.Container.objects.get(pk=c, project=self.request.user, shipment=data['shipment'])
                for location in locations:
                    if not models.Sample.objects.filter(container=container, location=location).exists():
                        while True:
                            name = "{0}_{1:02d}".format(group.name, j)
                            if models.Sample.objects.filter(group=group, name=name).exists() or name in names:
                                j += 1
                                continue
                            names.append(name)
                            break
                        to_create.append(
                            models.Sample(group=group, container=container, location=location, name=name,
                                          project=self.request.user, priority=priority))
                        priority += 1

            models.Sample.objects.bulk_create(to_create)
            if group.sample_count < group.samples.count():
                group.sample_count = group.samples.count()
                group.save()
        return JsonResponse({'url': reverse('shipment-detail', kwargs={'pk': data['shipment'].pk})})


class GroupSelect(OwnerRequiredMixin, SuccessMessageMixin, AjaxableResponseMixin, edit.UpdateView):
    form_class = forms.GroupSelectForm
    template_name = "users/forms/add-wizard.html"
    model = models.Group
    success_message = "Group has been updated."

    def get_initial(self):
        initial = super(GroupSelect, self).get_initial()
        initial['shipment'] = self.get_object().shipment
        initial['containers'] = [(c.pk, c.kind.pk, c.name) for c in initial['shipment'].containers.all()]
        initial['sample_locations'] = json.dumps(
            {g.name: {c.pk: list(c.samples.filter(group=g).values_list('location', flat=True))
                      for c in initial['shipment'].containers.all()}
             for g in initial['shipment'].groups.all()})
        initial['containers'] = initial['shipment'].containers.all()
        return initial

    @transaction.atomic
    def form_valid(self, form):
        data = form.cleaned_data
        sample_locations = json.loads(data['sample_locations'])
        group = self.object

        # Delete samples removed from containers
        for container, locations in sample_locations[group.name].items():
            models.Sample.objects.filter(container__pk=int(container), group__name=group).exclude(
                location__in=locations).delete()

        # group = models.Group.objects.get(pk=int(data['id']))
        to_create = []
        j = 1
        priority = max(group.samples.values_list('priority', flat=True) or [0]) + 1
        names = []
        for c, locations in sample_locations.get(group.name, {}).items():
            container = models.Container.objects.get(pk=c, project=self.request.user, shipment=data['shipment'])
            for location in locations:
                if not models.Sample.objects.filter(container=container, location=location).exists():
                    while True:
                        name = "{0}_{1:02d}".format(group.name, j)
                        if models.Sample.objects.filter(group=group, name=name).exists() or name in names:
                            j += 1
                            continue
                        names.append(name)
                        break
                    to_create.append(
                        models.Sample(group=group, container=container, location=location, name=name,
                                      project=self.request.user, priority=priority))
                    priority += 1

        models.Sample.objects.bulk_create(to_create)
        if group.sample_count < group.samples.count():
            group.sample_count = group.samples.count()
            group.save()
        return JsonResponse({'url': reverse('shipment-detail', kwargs={'pk': data['shipment'].pk})})


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
