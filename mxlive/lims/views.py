from django.contrib.auth.decorators import login_required, user_passes_test
from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from django.http import Http404, HttpResponseRedirect, JsonResponse
from django.core.urlresolvers import reverse
from django.contrib.auth import REDIRECT_FIELD_NAME
from django.shortcuts import render
from django.utils import timezone
from django.db.models import Q
from django.db import transaction
from formtools.wizard.views import SessionWizardView

from objlist.views import FilteredListView
from datetime import datetime, timedelta

from django.contrib.messages.views import SuccessMessageMixin
from django.views.generic import edit
from django.views.generic import detail
from django.views.generic.base import TemplateResponseMixin
from django.core.urlresolvers import reverse_lazy
from lims import forms, models
from itertools import chain
import json


class OwnerRequiredMixin(LoginRequiredMixin, UserPassesTestMixin):
    owner_field = 'project'

    def test_func(self):
        return self.request.user.is_superuser or getattr(self.get_object(), self.owner_field) == self.request.user


class AdminRequiredMixin(LoginRequiredMixin, UserPassesTestMixin):
    def test_func(self):
        return self.request.user.is_superuser


class AjaxableResponseMixin(object):
    """
    Mixin to add AJAX support to a form.
    Must be used with an object-based FormView (e.g. CreateView)
    """

    def form_valid(self, form):
        # We make sure to call the parent's form_valid() method because
        # it might do some processing (in the case of CreateView, it will
        # call form.save() for example).
        response = super(AjaxableResponseMixin, self).form_valid(form)
        if self.request.is_ajax():
            data = {
                'pk': self.object.pk,
            }
            return JsonResponse(data)
        else:
            return response


from django.template.loader import get_template
from django.http import HttpResponse
from django.conf import settings

from tempfile import mkdtemp
import subprocess
import os
import shutil

TEMP_PREFIX = getattr(settings, 'TEX_TEMP_PREFIX', 'render_tex-')
CACHE_PREFIX = getattr(settings, 'TEX_CACHE_PREFIX', 'render-tex')
CACHE_TIMEOUT = getattr(settings, 'TEX_CACHE_TIMEOUT', 30), # 86400)  # 1 day


class Tex2PdfMixin(object):

    def get_template_name(self):
        return "users/base.html"

    def get(self, request, *args, **kwargs):
        object = self.get_object()
        context = self.get_template_context()
        template = get_template(self.get_template_name())

        rendered_tpl = template.render(context).encode('utf-8')

        tmp = mkdtemp(prefix=TEMP_PREFIX)
        tex_file = os.path.join(tmp, '%s.tex' % object.name)
        f = open(tex_file, 'w')
        f.write(rendered_tpl)
        f.close()
        try:
            FNULL = open(os.devnull, 'w')
            process = subprocess.call(['xelatex', '-interaction=nonstopmode', tex_file], cwd=tmp, stdout=FNULL, stderr=subprocess.STDOUT)

            try:
                pdf = open("%s/%s.pdf" % (tmp, object.name))
            except:
                if request.user.is_superuser:
                    log = open("%s/%s.log" % (tmp, object.name)).read()
                    return HttpResponse(log, "text/plain")
                else:
                    raise RuntimeError("xelatex error (code %s) in %s/%s" % (process, tmp, object.name))

        finally:
            shutil.rmtree(tmp)

        res = HttpResponse(pdf, "application/pdf")

        return res


class BeamlineDetail(AdminRequiredMixin, detail.DetailView):
    model = models.Beamline
    template_name = "users/entries/beamline.html"
    allowed_roles = ['admin']


class ProjectDetail(UserPassesTestMixin, detail.DetailView):
    model = models.Project
    template_name = "users/project.html"
    slug_field = 'username'
    slug_url_kwarg = 'username'

    def test_func(self):
        """Allow access to admin or owner"""
        return self.request.user.is_superuser or self.get_object() == self.request.user

    def get_object(self, *args, **kwargs):
        # inject username in to kwargs if not already present
        if not self.kwargs.get('username'):
            self.kwargs['username'] = self.request.user
        if self.request.user.is_superuser:
            self.template_name = "users/staff.html"
        return super(ProjectDetail, self).get_object(*args, **kwargs)

    def get_context_data(self, **kwargs):
        context = super(ProjectDetail, self).get_context_data(**kwargs)

        if self.request.user.is_superuser:
            all = models.Shipment.objects.filter(status__in=[models.Shipment.STATES.ON_SITE,models.Shipment.STATES.SENT])
            context['shipments'] = all.order_by('status','-modified')
            context['automounters'] = models.Dewar.objects.filter(active=True).order_by('beamline__name')

        else:
            all = self.get_object().shipment_set.filter(status__lt=models.Shipment.STATES.ARCHIVED).order_by('modified')
            base_set = all.filter(status__lte=models.Shipment.STATES.ON_SITE).distinct()
            if base_set.count() < 7:
                pks = [s.pk for s in list(
                    chain(base_set, list(all.exclude(pk__in=base_set.values_list('pk')))[0:7 - base_set.count()]))]
            else:
                pks = base_set.values_list('pk')
            context['shipments'] = all.filter(pk__in=pks).order_by('status', '-modified')

        return context


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


class ListViewMixin(LoginRequiredMixin):
    paginate_by = 25
    owner_field = 'project__username'
    template_name = "users/list.html"
    add_ajax = True

    def get_filters(self, request):
        if request.user.is_superuser:
            self.list_display = ['project'] + self.list_display
            self.owner_field = None
        return super(ListViewMixin, self).get_filters(request)

    def get_queryset(self):
        if self.request.user.is_superuser:
            self.owner_field = None
        return super(ListViewMixin, self).get_queryset()


class DetailListMixin(OwnerRequiredMixin):
    add_url = None
    list_filter = []
    paginate_by = 25

    def get_context_data(self, **kwargs):
        c = super(DetailListMixin, self).get_context_data(**kwargs)
        c['object'] = self.get_object()
        return c

    def get_object(self):
        return self.extra_model.objects.get(pk=self.kwargs['pk'])


class ShipmentList(ListViewMixin, FilteredListView):
    model = models.Shipment
    list_filter = ['created', 'status']
    list_display = ['identity', 'name', 'date_shipped', 'carrier', 'num_containers', 'status']
    search_fields = ['project__username', 'project__name', 'name', 'comments', 'status']
    detail_url = 'shipment-detail'
    add_url = 'shipment-new'
    order_by = ['status', '-modified']
    # grid_template = "users/grids/shipment_grid.html"

    def get_queryset(self):
        if self.request.user.is_superuser:
            return super(ShipmentList, self).get_queryset().filter(
                status__gte=models.Shipment.STATES.SENT).filter(
                status__lt=models.Shipment.STATES.ARCHIVED)
        return super(ShipmentList, self).get_queryset()


class ShipmentDetail(OwnerRequiredMixin, detail.DetailView):
    model = models.Shipment
    template_name = "users/entries/shipment.html"


class ShipmentLabels(Tex2PdfMixin, ShipmentDetail):
    template_name = "users/labels-send.html"

    def get_template_name(self):
        if self.request.user.is_superuser:
            template = 'users/tex/return_labels.tex'
        else:
            template = 'users/tex/send_labels.tex'
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


class ShipmentDelete(OwnerRequiredMixin, SuccessMessageMixin, AjaxableResponseMixin, edit.DeleteView):
    template_name = "forms/delete.html"
    model = models.Shipment
    success_message = "Shipment has been deleted."
    success_url = reverse_lazy('dashboard')

    def delete(self, request, *args, **kwargs):
        super(ShipmentDelete, self).delete(request, *args, **kwargs)
        success_url = self.get_success_url()
        models.ActivityLog.objects.log_activity(self.request, self.object, models.ActivityLog.TYPE.DELETE, self.success_message)
        return JsonResponse({'url': success_url})


class SendShipment(ShipmentEdit):
    form_class = forms.ShipmentSendForm

    def get_initial(self):
        initial = super(SendShipment, self).get_initial()
        initial['components'] = models.ComponentType.objects.filter(pk__in=self.object.components.values_list('kind__pk'))
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

    def form_valid(self, form):
        obj = form.instance.returned()
        message = "Shipment returned"
        models.ActivityLog.objects.log_activity(self.request, obj, models.ActivityLog.TYPE.MODIFY, message)
        return super(ReturnShipment, self).form_valid(form)


class RecallSendShipment(ShipmentEdit):
    form_class = forms.ShipmentRecallSendForm

    def get_initial(self):
        initial = super(RecallSendShipment, self).get_initial()
        initial['components'] = models.ComponentType.objects.filter(pk__in=self.object.components.values_list('kind__pk'))
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


class SampleList(ListViewMixin, FilteredListView):
    model = models.Sample
    list_filter = ['modified']
    list_display = ['identity', 'name', 'comments', '_Container', 'container_location']
    search_fields = ['project__name', 'name', 'barcode', 'comments']
    detail_url = 'sample-detail'
    detail_ajax = True
    detail_target = '#modal-form'
    order_by = ['-created', '-priority']
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
        return reverse_lazy("shipment-protocol", kwargs={'pk': self.object.container.shipment.pk})


class SampleDelete(OwnerRequiredMixin, SuccessMessageMixin, AjaxableResponseMixin, edit.DeleteView):
    success_url = reverse_lazy('dashboard')
    template_name = "forms/delete.html"
    model = models.Sample
    success_message = "Sample has been deleted."

    def delete(self, request, *args, **kwargs):
        super(SampleDelete, self).delete(request, *args, **kwargs)
        models.ActivityLog.objects.log_activity(self.request, self.object, models.ActivityLog.TYPE.DELETE, self.success_message)
        return JsonResponse({'url': self.success_url})

    def get_context_data(self, **kwargs):
        context = super(SampleDelete, self).get_context_data(**kwargs)
        context['form_action'] = reverse_lazy('sample-delete', kwargs={'pk': self.object.pk})
        return context


class ContainerList(ListViewMixin, FilteredListView):
    model = models.Container
    list_filter = ['modified', 'kind', 'status']
    list_display = ['identity', 'name', 'shipment', 'kind', 'capacity', 'num_samples', 'status']
    search_fields = ['project__name', 'name', 'comments']
    detail_url = 'container-detail'
    order_by = ['-created']
    ordering_proxies = {}
    list_transforms = {}


class ContainerDetail(DetailListMixin, SampleList):
    extra_model = models.Container
    template_name = "users/entries/container.html"
    list_display = ['identity', 'name', 'container_location', 'comments']

    def get_list_title(self):
        object = self.get_object()
        return 'Samples in {}'.format(object.name)

    def get_filters(self, request):
        filters = super(ContainerDetail, self).get_filters(request)
        if self.get_object().has_children():
            self.list_display.append('container')
        return filters


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


class LocationLoad(AdminRequiredMixin, ContainerEdit):
    form_class = forms.LocationLoadForm
    success_message = "Container has been loaded"
    allowed_roles = ['admin']

    def get_initial(self):
        initial = super(LocationLoad, self).get_initial()
        initial.update(container_location=self.object.kind.container_locations.filter(
            name__iexact=self.kwargs.get('location')).first())
        return initial

    def form_valid(self, form):
        data = form.cleaned_data
        data['child'].update(parent=self.object, location=data['container_location'])
        return super(LocationLoad, self).form_valid(form)


def update_locations(request):
    container = models.Container.objects.get(pk=request.GET.get('pk', None))
    locations = list(container.kind.container_locations.values_list('pk', 'name'))
    return JsonResponse(locations, safe=False)


class ContainerDelete(OwnerRequiredMixin, SuccessMessageMixin, AjaxableResponseMixin, edit.DeleteView):
    success_url = reverse_lazy('dashboard')
    template_name = "forms/delete.html"
    model = models.Container
    success_message = "Container has been deleted."

    def delete(self, request, *args, **kwargs):
        super(ContainerDelete, self).delete(request, *args, **kwargs)
        models.ActivityLog.objects.log_activity(self.request, self.object, models.ActivityLog.TYPE.DELETE, self.success_message)
        return JsonResponse({'url': self.success_url})


class GroupList(ListViewMixin, FilteredListView):
    model = models.Group
    list_filter = ['modified', 'status']
    list_display = ['identity', 'name', 'kind', 'plan', 'num_samples', 'status']
    search_fields = ['project__name', 'comments', 'name']
    detail_url = 'group-detail'
    order_by = ['-modified', '-priority']
    ordering_proxies = {}
    list_transforms = {}


class GroupDetail(DetailListMixin, SampleList):
    extra_model = models.Group
    template_name = "users/entries/experiment.html"
    list_display = ['identity', 'name', 'container_location', 'comments']
    detail_url = 'sample-edit'
    detail_ajax = True
    detail_target = '#modal-form'

    def get_list_title(self):
        object = self.get_object()
        return 'Samples in {}'.format(object.name)


class GroupEdit(OwnerRequiredMixin, SuccessMessageMixin, AjaxableResponseMixin, edit.UpdateView):
    form_class = forms.GroupForm
    template_name = "forms/modal.html"
    model = models.Group
    success_message = "Group has been updated."
    success_url = reverse_lazy('group-list')

    def get_initial(self):
        self.original_name = self.object.name
        return super(GroupEdit, self).get_initial()

    def form_valid(self, form):
        resp = super(GroupEdit, self).form_valid(form)
        for s in self.object.sample_set.all():
            if self.original_name in s.name.split('-'):
                models.Sample.objects.filter(pk=s.pk).update(name=s.name.replace(self.original_name, self.object.name))
        return resp


class GroupDelete(OwnerRequiredMixin, SuccessMessageMixin, AjaxableResponseMixin, edit.DeleteView):
    success_url = reverse_lazy('dashboard')
    template_name = "forms/delete.html"
    model = models.Group
    success_message = "Group has been deleted."

    def delete(self, request, *args, **kwargs):
        super(GroupDelete, self).delete(request, *args, **kwargs)
        models.ActivityLog.objects.log_activity(self.request, self.object, models.ActivityLog.TYPE.DELETE, self.success_message)
        return JsonResponse({'url': self.success_url})


class DataList(ListViewMixin, FilteredListView):
    model = models.Data
    list_filter = ['modified', 'kind', 'beamline']
    list_display = ['id', 'name', 'sample', 'frame_sets', 'delta_angle', 'exposure_time', 'total_angle', 'wavelength', 'beamline', 'kind']
    search_fields = ['id', 'name', 'beamline__name', 'delta_angle', 'sample__name', 'frame_sets', 'project__name']
    detail_url = 'data-detail'
    detail_ajax = True
    detail_target = '#modal-form'
    order_by = ['-modified']
    ordering_proxies = {}
    list_transforms = {}


class DataDetail(OwnerRequiredMixin, detail.DetailView):
    model = models.Data
    template_name = "users/entries/data.html"


class DataEdit(AdminRequiredMixin, SuccessMessageMixin, AjaxableResponseMixin, edit.UpdateView):
    form_class = forms.DataForm
    template_name = "forms/modal.html"
    model = models.Data
    success_message = "Data has been updated."

    def get_success_url(self):
        return reverse_lazy("shipment-protocol", kwargs={'pk': self.object.sample.container.shipment.pk})


class ReportList(ListViewMixin, FilteredListView):
    model = models.AnalysisReport
    list_filter = ['modified']
    list_display = ['id', 'data__name', 'sample', 'score']
    search_fields = ['project', 'name', 'sample__name']
    detail_url = 'report-detail'
    order_by = ['-modified']
    ordering_proxies = {}
    list_transforms = {}


class ReportDetail(OwnerRequiredMixin, detail.DetailView):
    model = models.AnalysisReport
    template_name = "users/entries/report.html"


class ResultDetail(OwnerRequiredMixin, detail.DetailView):
    model = models.Result
    template_name = "users/entries/result.html"


class ScanResultList(ListViewMixin, FilteredListView):
    model = models.ScanResult
    list_filter = ['modified', 'kind']
    list_display = ['id', 'name', 'sample', 'edge', 'kind', 'created']
    search_fields = ['project__name', 'name', 'sample__name', 'beamline__name']
    # detail_url = 'data-detail'
    # detail_ajax = True
    # detail_target = '#modal-form'
    order_by = ['-modified']
    ordering_proxies = {}
    list_transforms = {}


class ActivityLogList(ListViewMixin, FilteredListView):
    model = models.ActivityLog
    list_filter = ['created', 'action_type']
    list_display = ['created', 'action_type', 'user_description', 'ip_number', 'object_repr', 'description']
    search_fields = ['description', 'ip_number', 'content_type__name', 'action_type']
    owner_field = "project__username"
    order_by = ['-created']
    ordering_proxies = {}
    list_transforms = {}
    detail_url = 'activitylog-detail'
    detail_ajax = True
    detail_target = '#modal-form'


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
        project = self.request.user

        for label, form in kwargs['form_dict'].items():
            if label == 'shipment':
                data = form.cleaned_data
                data.update({'project': project})
                self.shipment, created = models.Shipment.objects.get_or_create(**data)
            elif label == 'containers':
                for i, name in enumerate(form.cleaned_data['name_set']):
                    data = {
                        'kind': models.ContainerType.objects.get(pk=form.cleaned_data['kind_set'][i]),
                        'name': name,
                        'shipment': self.shipment,
                        'project': project
                    }
                    container, created = models.Container.objects.get_or_create(**data)
            elif label == 'groups':
                sample_locations = json.loads(form.cleaned_data['sample_locations'])
                for i, name in enumerate(form.cleaned_data['name_set']):
                    data = {field: form.cleaned_data['{}_set'.format(field)][i] for field in ['name','kind','comments',
                                                                                              'plan','absorption_edge']}
                    data.update({
                        'energy': data.get('energy_set',[]) and float(data['energy_set'][i]) or None,
                        'sample_count': int(form.cleaned_data['sample_count_set'][i]),
                        'shipment': self.shipment,
                        'project': project,
                        'priority': i + 1
                    })
                    group, created = models.Group.objects.get_or_create(**data)
                    to_create = []

                    for c, locations in sample_locations.get(group.name, {}).items():
                        container = models.Container.objects.get(name=c, project=project, shipment=self.shipment)
                        for j, sample in enumerate(locations):
                            name = "{0}-{1:02d}".format(group.name, j+1)
                            to_create.append(models.Sample(group=group, container=container, container_location=sample,
                                                           name=name, project=project))
                    models.Sample.objects.bulk_create(to_create)
                    if group.sample_count < group.sample_set.count():
                        group.sample_count = group.sample_set.count()
                        group.save()

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
        data['shipment'].container_set.exclude(pk__in=[int(pk) for pk in data['id_set'] if pk]).delete()
        for i, name in enumerate(data['name_set']):
            if data['id_set'][i]:
                models.Container.objects.filter(pk=int(data['id_set'][i])).update(name=data['name_set'][i])
            else:
                info = {
                    'kind': models.ContainerType.objects.get(pk=form.cleaned_data['kind_set'][i]),
                    'name': name,
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
        initial['containers'] = [(c.pk, c.kind.pk) for c in initial['shipment'].container_set.all()]
        initial['sample_locations'] = json.dumps({g.name: {c.pk: list(c.sample_set.filter(group=g).values_list('container_location', flat=True))
                                                for c in initial['shipment'].container_set.all()}
                                       for g in initial['shipment'].group_set.all()})
        if initial['shipment']:
            initial['containers'] = initial['shipment'].container_set.all()
        return initial

    @transaction.atomic
    def form_valid(self, form):
        data = form.cleaned_data
        data['shipment'].group_set.exclude(pk__in=[int(pk) for pk in data['id_set'] if pk]).delete()
        sample_locations = json.loads(data['sample_locations'])

        # Delete samples removed from containers
        for group, containers in sample_locations.items():
            for container, locations in containers.items():
                models.Sample.objects.filter(container__pk=int(container), group__name=group).exclude(container_location__in=locations).delete()

        for i, name in enumerate(data['name_set']):
            info = {field: data['{}_set'.format(field)][i] for field in ['name', 'kind', 'plan',
                                                                         'comments', 'absorption_edge']}
            info.update({
                'energy': data['energy_set'][i] and float(data['energy_set'][i]) or None,
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
            for c, locations in sample_locations.get(group.name, {}).items():
                container = models.Container.objects.get(pk=c, project=self.request.user, shipment=data['shipment'])
                j = 1
                names = []
                for location in locations:
                    if not models.Sample.objects.filter(container=container, container_location=location).exists():
                        while True:
                            name = "{0}-{1:02d}".format(group.name, j)
                            if models.Sample.objects.filter(group=group, name=name).exists() or name in names:
                                j += 1
                                continue
                            names.append(name)
                            break
                        to_create.append(
                            models.Sample(group=group, container=container, container_location=location, name=name,
                                          project=self.request.user))

            models.Sample.objects.bulk_create(to_create)
            if group.sample_count < group.sample_set.count():
                group.sample_count = group.sample_set.count()
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
        initial['containers'] = [(c.pk, c.kind.pk, c.name) for c in initial['shipment'].container_set.all()]
        initial['sample_locations'] = json.dumps({g.name: {c.pk: list(c.sample_set.filter(group=g).values_list('container_location', flat=True))
                                                for c in initial['shipment'].container_set.all()}
                                       for g in initial['shipment'].group_set.all()})
        initial['containers'] = initial['shipment'].container_set.all()
        return initial

    @transaction.atomic
    def form_valid(self, form):
        data = form.cleaned_data
        sample_locations = json.loads(data['sample_locations'])
        group = self.object

        # Delete samples removed from containers
        for container, locations in sample_locations[group.name].items():
            models.Sample.objects.filter(container__pk=int(container), group__name=group).exclude(container_location__in=locations).delete()

        group = models.Group.objects.get(pk=int(data['id']))
        to_create = []
        for c, locations in sample_locations.get(group.name, {}).items():
            container = models.Container.objects.get(pk=c, project=self.request.user, shipment=data['shipment'])
            j = 1
            names = []
            for location in locations:
                if not models.Sample.objects.filter(container=container, container_location=location).exists():
                    while True:
                        name = "{0}-{1:02d}".format(group.name, j)
                        if models.Sample.objects.filter(group=group, name=name).exists() or name in names:
                            j += 1
                            continue
                        names.append(name)
                        break
                    to_create.append(
                        models.Sample(group=group, container=container, container_location=location, name=name,
                                      project=self.request.user))

        models.Sample.objects.bulk_create(to_create)
        if group.sample_count < group.sample_set.count():
            group.sample_count = group.sample_set.count()
            group.save()
        return JsonResponse({'url': reverse('shipment-detail', kwargs={'pk': data['shipment'].pk})})