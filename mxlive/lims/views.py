from django.contrib.auth.decorators import login_required, user_passes_test
from django.contrib.auth.mixins import LoginRequiredMixin
from django.http import Http404, HttpResponseRedirect, JsonResponse
from django.core.urlresolvers import reverse
from django.contrib.auth import REDIRECT_FIELD_NAME
from django.shortcuts import render
from django.utils import timezone
from django.db.models import Q

from objlist.views import FilteredListView
#from staff.models import *

from datetime import datetime, timedelta

from django.contrib.messages.views import SuccessMessageMixin
from django.views.generic import edit
from django.views.generic import detail
from django.core.urlresolvers import reverse_lazy
from lims import forms, models
from itertools import chain
import json

class AjaxableResponseMixin(object):
    """
    Mixin to add AJAX support to a form.
    Must be used with an object-based FormView (e.g. CreateView)
    """
    def form_invalid(self, form):
        response = super(AjaxableResponseMixin, self).form_invalid(form)
        if self.request.is_ajax():
            return JsonResponse(form.errors, status=400)
        else:
            return response

    def form_valid(self, form):
        # We make sure to call the parent's form_valid() method because
        # it might do some processing (in the case of CreateView, it will
        # call form.save() for example).
        response = super(AjaxableResponseMixin, self).form_valid(form)
        if self.request.is_ajax():
            print "ajax"
            data = {
                'pk': self.object.pk,
            }
            return JsonResponse(data)
        else:
            print "not ajax"
            return response


def admin_login_required(function=None, redirect_field_name=REDIRECT_FIELD_NAME):
    """
    Decorator for views that checks that the user is logged in, redirecting
    to the log-in page if necessary.
    """
    actual_decorator = user_passes_test(
        lambda u: u.is_authenticated() and u.is_superuser,
        redirect_field_name=redirect_field_name
    )
    if function:
        return actual_decorator(function)
    return actual_decorator


@login_required
def staff_home(request):
    if not request.user.is_superuser:
        return HttpResponseRedirect(reverse('project-home'))

    recent_start = timezone.now() - timedelta(days=7)
    last_login = ActivityLog.objects.last_login(request)
    if last_login is not None:
        if last_login.created < recent_start:
            recent_start = last_login.created

    statistics = {
        'shipments': {
            'outgoing': models.Shipment.objects.filter(status__exact=models.Shipment.STATES.SENT).count(),
            'incoming': models.Shipment.objects.filter(modified__gte=recent_start).filter(
                status__exact=models.Shipment.STATES.RETURNED).count(),
            'on_site': models.Shipment.objects.filter(status__exact=models.Shipment.STATES.ON_SITE).count(),
        },
        'experiments': {
            'active': Group.objects.filter(status__exact=Group.STATES.ACTIVE).filter(
                pk__in=Sample.objects.filter(status__in=[Sample.STATES.ON_SITE, Sample.STATES.LOADED]).values(
                    'experiment')).count(),
            'processing': Group.objects.filter(status__exact=Group.STATES.PROCESSING).filter(
                pk__in=Sample.objects.filter(status__exact=Sample.STATES.ON_SITE).values('experiment')).count(),
        },
        'samples': {
            'on_site': Sample.objects.filter(status__in=[Sample.STATES.ON_SITE, Sample.STATES.LOADED]).count(),
            'outgoing': Sample.objects.filter(status__exact=Sample.STATES.SENT).count(),
            'incoming': Sample.objects.filter(modified__gte=recent_start).filter(
                status__exact=Sample.STATES.RETURNED).count(),
        },
        'runlists': {
            'loaded': Runlist.objects.filter(status__exact=Runlist.STATES.LOADED).count(),
            'completed': Runlist.objects.filter(status__exact=Runlist.STATES.COMPLETED,
                                                modified__gte=recent_start).count(),
            'start_date': recent_start,
        },
    }

    return render(request, 'users/staff.html', {
        #'activity_log': FilteredListView(request, ActivityLog.objects),
        'feedback': models.Feedback.objects.all()[:5],
        'statistics': statistics,
        'handler': request.path,
    })

class ProjectDetail(detail.DetailView):
    model = models.Project
    template_name = "users/project.html"
    slug_field = 'username'
    slug_url_kwarg = 'username'
    allowed_roles = ['owner','admin']

    def get_object(self, *args, **kwargs):
        # inject username in to kwargs if not already present
        if not self.kwargs.get('username'):
            self.kwargs['username'] = self.request.user
        return super(ProjectDetail, self).get_object(*args, **kwargs)

    def get_context_data(self, **kwargs):
        context = super(ProjectDetail, self).get_context_data(**kwargs)
        month = datetime.now() - timedelta(days=30)
        all = self.get_object().shipment_set.filter(status__lt=models.Shipment.STATES.ARCHIVED).order_by('modified')
        base_set = all.filter(Q(status__in=[models.Shipment.STATES.ON_SITE, models.Shipment.STATES.SENT]) | Q(modified__gte=month)).distinct()
        if base_set.count() < 7:
            pks = [s.pk for s in list(chain(base_set, list(all.exclude(pk__in=base_set.values_list('pk')))[0:10-base_set.count()]))]
        else:
            pks = base_set.values_list('pk')
        context['shipments'] = all.filter(pk__in=pks).order_by('status','-modified')
        return context



class ListViewMixin(object):
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


class DetailListMixin(object):
    add_url = None
    list_filter = []
    paginate_by = None

    def get_context_data(self, **kwargs):
        c = super(DetailListMixin, self).get_context_data(**kwargs)
        c['object'] = self.get_object()
        return c

    def get_object(self):
        return self.extra_model.objects.get(pk=self.kwargs['pk'])


class ShipmentList(ListViewMixin, FilteredListView):
    model = models.Shipment
    list_filter = ['created','status']
    list_display = ['identity','name', 'date_shipped', 'carrier', 'num_containers', 'status']
    search_fields = ['project__name','name', 'comments','status']
    detail_url = 'shipment-detail'
    add_url = 'shipment-new'
    order_by = ['status','-modified']
    grid_template = "users/grids/shipment_grid.html"

    def get_queryset(self):
        if self.request.user.is_superuser:
            recent = timezone.now() - timedelta(days=3)
            return super(ShipmentList, self).get_queryset().filter(Q(status__in=[models.Shipment.STATES.SENT,
                                                                               models.Shipment.STATES.ON_SITE]) |
                                                                   Q(status=models.Shipment.STATES.RETURNED, modified__gte=recent))
        return super(ShipmentList, self).get_queryset()

class ShipmentDetail(detail.DetailView):
    model = models.Shipment
    template_name = "users/entries/shipment.html"
    allowed_roles = ['owner','admin']
    admin_roles = ['admin']

class ShipmentEdit(SuccessMessageMixin, LoginRequiredMixin, AjaxableResponseMixin, edit.UpdateView):
    form_class = forms.ShipmentForm
    template_name = "forms/modal.html"
    model = models.Shipment
    success_url = reverse_lazy('shipment-list')
    success_message = "Shipment '%(name)s' has been updated."
    allowed_roles = ['owner', 'admin']
    admin_roles = ['admin']

    def get_initial(self):
        initial = super(ShipmentEdit, self).get_initial()
        initial.update(project=self.request.user)
        return initial

class ShipmentDelete(AjaxableResponseMixin, SuccessMessageMixin, edit.DeleteView):
    success_url = reverse_lazy('dashboard')
    template_name = "forms/delete.html"
    allowed_roles = ['owner','admin']
    model = models.Shipment
    success_message = "Shipment has been deleted."

    def delete(self, request, *args, **kwargs):
        super(ShipmentDelete, self).delete(request, *args, **kwargs)
        success_url = self.get_success_url()
        return JsonResponse({'url': success_url})



class SendShipment(ShipmentEdit):
    form_class = forms.ShipmentSendForm
    success_url = reverse_lazy('shipment-list')

    def form_valid(self, form):
        obj = form.instance
        if form.instance.status == models.Shipment.STATES.DRAFT:
            obj.status = models.Shipment.STATES.SENT
            obj.date_shipped = datetime.now()
            obj.save()
        return super(SendShipment, self).form_valid(form)

class ReturnShipment(ShipmentEdit):
    form_class = forms.ShipmentReturnForm
    success_url = reverse_lazy('shipment-list')

    def form_valid(self, form):
        obj = form.instance
        if form.instance.status == models.Shipment.STATES.ON_SITE:
            obj.status = models.Shipment.STATES.RETURNED
            obj.date_returned = datetime.now()
            obj.save()
        return super(ReturnShipment, self).form_valid(form)

class ArchiveShipment(ShipmentEdit):
    form_class = forms.ShipmentArchiveForm
    success_url = reverse_lazy('shipment-list')

    def form_valid(self, form):
        obj = form.instance
        obj.archive()

class ReceiveShipment(ShipmentEdit):
    form_class = forms.ShipmentReceiveForm
    success_url = reverse_lazy('shipment-list')

    def form_valid(self, form):
        obj = form.instance
        obj.date_received = datetime.now()
        obj.save()
        obj.receive()
        return super(ReceiveShipment, self).form_valid(form)


class SampleList(ListViewMixin, FilteredListView):
    model = models.Sample
    list_filter = ['modified','status']
    list_display = ['identity', 'name', 'comments', '_Container', 'container_location', 'status']
    search_fields = ['project__name','name', 'barcode', 'comments']
    detail_url = 'sample-detail'
    add_url = 'sample-new'
    order_by = ['-created', '-priority']
    ordering_proxies = {}
    list_transforms = {}

class SampleDetail(detail.DetailView):
    model = models.Sample
    template_name = "users/entries/crystal.html"
    allowed_roles = ['owner','admin']
    admin_roles = ['admin']

class SampleCreate(SuccessMessageMixin, LoginRequiredMixin, AjaxableResponseMixin, edit.CreateView):
    form_class = forms.SampleForm
    template_name = "forms/modal.html"
    model = models.Sample
    success_url = reverse_lazy('sample-list')
    success_message = "Sample '%(name)s' has been created."

    def get_initial(self):
        initial = super(SampleCreate, self).get_initial()
        initial.update(project=self.request.user.project)
        return initial

class SampleEdit(SuccessMessageMixin, LoginRequiredMixin, AjaxableResponseMixin, edit.UpdateView):
    form_class = forms.SampleForm
    template_name = "forms/modal.html"
    model = models.Sample
    success_message = "Sample has been updated."
    allowed_roles = ['owner', 'admin']
    admin_roles = ['admin']

class SampleDelete(edit.DeleteView):
    success_url = reverse_lazy('sample-list')
    template_name = "forms/delete.html"
    allowed_roles = ['owner','admin']
    model = models.Sample
    success_message = "Sample has been deleted."

class ContainerList(ListViewMixin, FilteredListView):
    model = models.Container
    list_filter = ['modified','kind','status']
    list_display = ['identity', 'name', 'shipment', 'kind', 'capacity', 'num_samples', 'status']
    search_fields = ['project__name','name', 'comments']
    detail_url = 'container-detail'
    add_url = 'container-new'
    order_by = ['-created']
    ordering_proxies = {}
    list_transforms = {}


class ContainerDetail(DetailListMixin, SampleList):
    extra_model = models.Container
    template_name = "users/entries/container.html"
    list_display = ['identity', 'name', 'container_location', 'comments']
    allowed_roles = ['owner','admin']
    admin_roles = ['admin']

    def get_list_title(self):
        object = self.get_object()
        return 'Samples in {}'.format(object.name)

class ContainerCreate(SuccessMessageMixin, LoginRequiredMixin, AjaxableResponseMixin, edit.CreateView):
    form_class = forms.ContainerForm
    template_name = "forms/modal.html"
    model = models.Container
    success_url = reverse_lazy('container-list')
    success_message = "Container '%(name)s' has been created."

    def get_initial(self):
        initial = super(ContainerCreate, self).get_initial()
        initial.update(project=self.request.user)
        return initial

class ContainerEdit(SuccessMessageMixin, LoginRequiredMixin, AjaxableResponseMixin, edit.UpdateView):
    form_class = forms.ContainerForm
    template_name = "forms/modal.html"
    model = models.Container
    success_message = "Container has been updated."
    allowed_roles = ['owner', 'admin']
    admin_roles = ['admin']

    def get_initial(self):
        initial = super(ContainerEdit, self).get_initial()
        initial.update(project=self.request.user)
        return initial


class ContainerDelete(edit.DeleteView):
    success_url = reverse_lazy('container-list')
    template_name = "forms/delete.html"
    allowed_roles = ['owner','admin']
    model = models.Container
    success_message = "Container has been deleted."
    


class GroupList(ListViewMixin, FilteredListView):
    model = models.Group
    list_filter = ['modified','status']
    list_display = ['identity','name','kind','plan','num_samples','status']
    search_fields = ['project__name','comments','name']
    detail_url = 'group-detail'
    add_url = 'group-new'
    order_by = ['-modified', '-priority']
    ordering_proxies = {}
    list_transforms = {}

class GroupDetail(DetailListMixin, SampleList):
    extra_model = models.Group
    template_name = "users/entries/experiment.html"
    list_display = ['identity', 'name', 'container_location', 'comments']
    allowed_roles = ['owner','admin']
    admin_roles = ['admin']
    detail_url = 'sample-edit'
    detail_ajax = True
    detail_target = '#modal-form'

    def get_list_title(self):
        object = self.get_object()
        return 'Samples in {}'.format(object.name)


class GroupCreate(SuccessMessageMixin, LoginRequiredMixin, AjaxableResponseMixin, edit.CreateView):
    form_class = forms.GroupForm
    template_name = "forms/modal.html"
    model = models.Group
    success_url = reverse_lazy('group-list')
    success_message = "Group '%(name)s' has been created."

    def get_initial(self):
        initial = super(GroupCreate, self).get_initial()
        initial.update(project=self.request.user.project)
        return initial

class GroupEdit(edit.UpdateView):
    form_class = forms.GroupForm
    template_name = "forms/modal.html"
    model = models.Group
    success_message = "Group has been updated."
    allowed_roles = ['owner', 'admin']
    admin_roles = ['admin']

class GroupDelete(edit.DeleteView):
    success_url = reverse_lazy('group-list')
    template_name = "forms/delete.html"
    allowed_roles = ['owner','admin']
    model = models.Group
    success_message = "Group has been deleted."

class DataList(ListViewMixin, FilteredListView):
    model = models.Data
    list_filter = ['modified','kind']
    list_display = ['id', 'name', 'sample', 'frame_sets', 'delta_angle', 'exposure_time', 'total_angle', 'wavelength', 'beamline', 'kind']
    search_fields = ['id', 'name', 'beamline__name', 'delta_angle', 'sample__name', 'frame_sets', 'project__name']
    detail_url = 'data-detail'
    detail_ajax = True
    detail_target = '#modal-form'
    order_by = ['-modified']
    ordering_proxies = {}
    list_transforms = {}

class DataDetail(detail.DetailView):
    model = models.Data
    template_name = "users/entries/data.html"
    allowed_roles = ['owner','admin']
    admin_roles = ['admin']

class ResultList(ListViewMixin, FilteredListView):
    model = models.Result
    list_filter = ['modified','kind']
    list_display = ['id', 'name', 'frames', 'space_group', 'resolution', 'r_meas', 'completeness', 'score', 'kind']
    search_fields = ['project__name','name','sample__name','space_group__name']
    #detail_url = 'data-detail'
    #detail_ajax = True
    #detail_target = '#modal-form'
    order_by = ['-modified']
    ordering_proxies = {}
    list_transforms = {}

class ScanResultList(ListViewMixin, FilteredListView):
    model = models.ScanResult
    list_filter = ['modified','kind']
    list_display = ['id', 'name', 'sample', 'edge', 'kind', 'created']
    search_fields = ['project__name','name','sample__name','beamline__name']
    #detail_url = 'data-detail'
    #detail_ajax = True
    #detail_target = '#modal-form'
    order_by = ['-modified']
    ordering_proxies = {}
    list_transforms = {}

class ActivityLogList(ListViewMixin, FilteredListView):
    model = models.ActivityLog
    list_filter = ['created','action_type']
    list_display = ['created', 'action_type','user_description','ip_number','object_repr','description']
    search_fields = ['description','ip_number', 'content_type__name', 'action_type']
    owner_field = "user__username"
    order_by = ['-created']
    ordering_proxies = {}
    list_transforms = {}
    detail_url = 'activitylog-detail'
    detail_ajax = True
    detail_target = '#modal-form'

from formtools.wizard.views import SessionWizardView

class ShipmentGroupCreate(edit.CreateView):
    model = models.Group
    form_class = forms.AddGroupForm
    success_url = reverse_lazy('shipment-list')
    template_name = "forms/modal.html"

    def form_valid(self, form):
        context = self.get_context_data()
        containers = context['containers']
        with transaction.atomic():
            self.object = form.save()
            if containers.is_valid():
                containers.shipment = self.object
                containers.save()
        return super(ShipmentContainerCreate, self).form_valid(form)


class ShipmentContainerCreate(AjaxableResponseMixin, edit.CreateView):
    model = models.Container
    form_class = forms.AddContainerForm
    success_url = reverse_lazy('shipment-list')
    template_name = "forms/modal.html"

    def form_valid(self, form):
        context = self.get_context_data()
        containers = context['containers']
        with transaction.atomic():
            self.object = form.save()
            if containers.is_valid():
                containers.shipment = self.object
                containers.save()
        return super(ShipmentContainerCreate, self).form_valid(form)


class ShipmentCreate(SessionWizardView):
    form_list = [('shipment', forms.AddShipmentForm),
                 ('containers', forms.ContainerFormSet),
                 ('groups', forms.GroupFormSet)]
    template_name = "forms/wizard.html"

    def get_form_initial(self, step):
        if step == 'shipment':
            return self.initial_dict.get(step, {'project': self.request.user})
        elif step == 'groups':
            # on SECOND step get data of first step
            containers_data = self.storage.get_step_data('containers')
            if containers_data:
                names = containers_data.getlist('containers-0-name')
                kinds = containers_data.getlist('containers-0-kind')
                containers = [(names[i], kinds[i]) for i in range(len(names))]
                return self.initial_dict.get(step, [{'containers': containers}])
        return self.initial_dict.get(step, {})

    def done(self, form_list, **kwargs):
        project = self.request.user
        for label, form in kwargs['form_dict'].items():
            if label == 'shipment':
                data = form.cleaned_data
                data.update({'project': project})
                self.shipment, created = models.Shipment.objects.get_or_create(**data)
            elif label == 'containers':
                for i, name in enumerate(form.cleaned_data[0]['name_set']):
                    data = {}
                    data['kind'] = models.ContainerType.objects.get(pk=form.cleaned_data[0]['kind_set'][i])
                    data['name'] = name
                    data['shipment'] = self.shipment
                    data['project'] = project
                    container, created = models.Container.objects.get_or_create(**data)
            elif label == 'groups':
                sample_locations = json.loads(form.cleaned_data[0]['sample_locations'])
                for i, name in enumerate(form.cleaned_data[0]['name_set']):
                    data = {field: form.cleaned_data[0]['{}_set'.format(field)][i] for field in ['name','kind','plan','comments']}
                    data['sample_count'] = int(form.cleaned_data[0]['sample_count_set'][i])
                    data.update({field: float(form.cleaned_data[0]['{}_set'.format(field)][i])
                                for field in ['energy','absorption_edge'] if form.cleaned_data[0]['{}_set'.format(field)][i]})
                    data['shipment'] = self.shipment
                    data['project'] = self.request.user
                    data['priority'] = i + 1
                    group, created = models.Group.objects.get_or_create(**data)
                    to_create = []
                    for c, locations in sample_locations.get(group.name,{}).items():
                        container = models.Container.objects.get(name=c, project=project, shipment=self.shipment)
                        for i, sample in enumerate(locations):
                            name = "{0}-{1:02d}".format(group.name, i)
                            to_create.append(Sample(experiment=group, container=container, container_location=sample, name=name, project=project))
                    Sample.objects.bulk_create(to_create)
                    if group.sample_count < group.sample_set.count():
                        group.sample_count = group.sample_set.count()
                        group.save()

        return JsonResponse({'url': reverse('shipment-detail', kwargs={'pk': self.shipment.pk})})
