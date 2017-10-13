from django.contrib.messages.views import SuccessMessageMixin
from django.views.generic import edit
from django.core.urlresolvers import reverse_lazy
from django.contrib.auth import get_user_model
import models
import forms
import slap

from objlist.views import FilteredListView
from mixins import AjaxableResponseMixin, AdminRequiredMixin
from lims.models import Project, ActivityLog
from lims.forms import NewProjectForm

User = get_user_model()


class AccessList(AdminRequiredMixin, FilteredListView):
    model = models.UserList
    list_filter = []
    list_display = ['name', 'description', 'current_users', 'address', 'active']
    detail_url = 'access-edit'
    detail_url_kwarg = 'address'
    detail_ajax = True
    detail_target = '#modal-form'
    order_by = ['name']
    template_name = "users/list.html"

    def get_context_data(self, **kwargs):
        context = super(AccessList, self).get_context_data(**kwargs)
        context['tool_template'] = "users/tools-staff.html"
        return context


class AccessEdit(AdminRequiredMixin, SuccessMessageMixin, AjaxableResponseMixin, edit.UpdateView):
    form_class = forms.AccessForm
    template_name = "forms/modal.html"
    model = models.UserList
    success_url = reverse_lazy('access-list')
    success_message = "Remote access list has been updated."
    allowed_roles = ['owner', 'admin']
    admin_roles = ['admin']

    def get_object(self):
        return self.model.objects.get(address=self.kwargs.get('address'))


class AnnouncementEdit(AdminRequiredMixin, SuccessMessageMixin, AjaxableResponseMixin, edit.UpdateView):
    form_class = forms.AnnouncementForm
    template_name = "forms/modal.html"
    model = models.Announcement
    success_url = reverse_lazy('dashboard')
    success_message = "Announcement has been updated"


class AnnouncementDelete(AdminRequiredMixin, SuccessMessageMixin, AjaxableResponseMixin, edit.DeleteView):
    template_name = "forms/delete.html"
    model = models.Announcement
    success_url = reverse_lazy('dashboard')
    success_message = "Announcement has been deleted"

    def get_context_data(self, **kwargs):
        context = super(AnnouncementDelete, self).get_context_data(**kwargs)
        context['form_action'] = reverse_lazy('announcement-delete', kwargs={'pk': self.object.pk})
        return context


class ProjectList(AdminRequiredMixin, FilteredListView):
    model = Project
    paginate_by = 25
    template_name = "users/list.html"
    list_filter = ['modified', ]
    list_display = ['username', 'contact_person', 'contact_phone', 'contact_email', 'shipment_count', 'forms']
    search_fields = ['username', 'contact_person', 'contact_phone', 'contact_email', 'city', 'province', 'country',
                     'department', 'organisation']
    detail_url = 'edit-profile'
    detail_url_kwarg = 'username'
    detail_ajax = True
    detail_target = '#modal-form'
    add_url = 'new-project'
    add_ajax = True
    order_by = ['name']
    ordering_proxies = {}
    list_transforms = {}

    def get_context_data(self, **kwargs):
        context = super(ProjectList, self).get_context_data(**kwargs)
        context['tool_template'] = "users/tools-staff.html"
        return context


class ProjectCreate(AdminRequiredMixin, SuccessMessageMixin, AjaxableResponseMixin, edit.CreateView):
    form_class = NewProjectForm
    template_name = "forms/modal.html"
    model = Project
    success_url = reverse_lazy('user-list')
    success_message = "New Account '%(username)s' has been created."

    def form_valid(self, form):
        data = form.cleaned_data
        user_info = {
            k: data.get(k, '')
            for k in ['username', 'password', 'first_name', 'last_name']
            if k in data
        }
        # Make sure user with username does not already exist
        if User.objects.filter(username=user_info.get('username')).exists():
            user_info.pop('username', '')

        info = slap.add_user(user_info)
        info['email'] = data.get('contact_email', '')
        info.pop('password')

        # create local user
        obj = User.objects.create(**info)
        data['user'] = obj
        data['name'] = obj.username

        proj = Project.objects.create(**data)

        info_msg = 'New Account {} added'.format(proj)

        ActivityLog.objects.log_activity(
            self.request, obj, ActivityLog.TYPE.CREATE, info_msg
        )
        # messages are simply passed down to the template via the request context
        return render_to_response("users/redirect.html", context_instance=RequestContext(self.request))
