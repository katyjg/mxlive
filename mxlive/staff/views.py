from django.contrib import messages
from django.contrib.auth import get_user_model
from django.contrib.auth.signals import user_logged_in, user_logged_out
from django.contrib.messages.views import SuccessMessageMixin
from django.http import JsonResponse
from django.shortcuts import render
from django.urls import reverse_lazy
from django.utils import dateformat, timezone
from django.views.generic import edit, detail
from itemlist.views import ItemListView

from mxlive.lims.forms import NewProjectForm
from mxlive.lims.models import Project, ActivityLog
from mxlive.utils import slap
from mxlive.utils.mixins import AsyncFormMixin, AdminRequiredMixin
from . import models, forms

User = get_user_model()


class AccessList(AdminRequiredMixin, ItemListView):
    model = models.UserList
    list_filter = []
    list_display = ['name', 'description', 'current_users', 'allowed_users', 'address', 'active']
    tool_template = "users/tools-access.html"
    detail_url = 'access-edit'
    detail_url_kwarg = 'address'
    detail_ajax = True
    detail_target = '#modal-target'
    order_by = ['name']
    template_name = "users/list.html"

    def get_context_data(self, **kwargs):
        ctx = super(AccessList, self).get_context_data(**kwargs)
        ctx['tool_template'] = self.tool_template
        return ctx


class AccessEdit(AdminRequiredMixin, SuccessMessageMixin, AsyncFormMixin, edit.UpdateView):
    form_class = forms.AccessForm
    template_name = "modal/form.html"
    model = models.UserList
    success_url = reverse_lazy('access-list')
    success_message = "Remote access list has been updated."
    allowed_roles = ['owner', 'admin']
    admin_roles = ['admin']

    def get_object(self):
        return self.model.objects.get(address=self.kwargs.get('address'))


class RemoteConnectionList(AdminRequiredMixin, ItemListView):
    model = models.RemoteConnection
    list_display = ['user', 'name', 'list', 'status', 'created', 'end']
    list_filter = ['created', 'list']
    search_fields = ['user__username', 'name', 'status', 'list__name', 'created']
    order_by = ['-created']
    template_name = "users/list.html"
    detail_url = 'connection-detail'
    detail_ajax = True
    detail_target = '#modal-target'


class RemoteConnectionDetail(AdminRequiredMixin, detail.DetailView):
    model = models.RemoteConnection
    template_name = "users/entries/connection.html"


class CategoryList(AdminRequiredMixin, ItemListView):
    model = models.UserCategory
    list_filter = []
    list_display = ['name', 'current_users', 'num_users']
    detail_url = 'category-edit'
    detail_ajax = True
    detail_target = '#modal-target'
    order_by = ['name']
    template_name = "users/list.html"


class CategoryEdit(AdminRequiredMixin, SuccessMessageMixin, AsyncFormMixin, edit.UpdateView):
    form_class = forms.CategoryForm
    template_name = "modal/form.html"
    model = models.UserCategory
    success_url = reverse_lazy('category-list')
    success_message = "User category has been updated."
    allowed_roles = ['owner', 'admin']
    admin_roles = ['admin']


class AnnouncementCreate(AdminRequiredMixin, SuccessMessageMixin, AsyncFormMixin, edit.CreateView):
    form_class = forms.AnnouncementForm
    template_name = "modal/form.html"
    model = models.Announcement
    success_url = reverse_lazy('dashboard')
    success_message = "Announcement has been created"


class AnnouncementEdit(AdminRequiredMixin, SuccessMessageMixin, AsyncFormMixin, edit.UpdateView):
    form_class = forms.AnnouncementForm
    template_name = "modal/form.html"
    model = models.Announcement
    success_url = reverse_lazy('dashboard')
    success_message = "Announcement has been updated"


class AnnouncementDelete(AdminRequiredMixin, SuccessMessageMixin, AsyncFormMixin, edit.DeleteView):
    template_name = "modal/delete.html"
    model = models.Announcement
    success_url = reverse_lazy('dashboard')
    success_message = "Announcement has been deleted"

    def get_context_data(self, **kwargs):
        context = super(AnnouncementDelete, self).get_context_data(**kwargs)
        context['form_action'] = reverse_lazy('announcement-delete', kwargs={'pk': self.object.pk})
        return context


class ProjectList(AdminRequiredMixin, ItemListView):
    model = Project
    paginate_by = 25
    template_name = "users/list.html"
    tools_template = "users/tools-user.html"
    list_filters = ['modified', ]
    list_columns = ['username', 'contact_person', 'contact_phone', 'contact_email']
    list_search = ['username', 'contact_person', 'contact_phone', 'contact_email', 'city', 'province', 'country',
                   'department', 'organisation']
    link_url = 'user-detail'
    link_kwarg = 'username'
    add_url = 'new-project'
    add_ajax = True
    order_by = ['name']
    ordering_proxies = {}
    list_transforms = {}


class UserDetail(AdminRequiredMixin, detail.DetailView):
    model = Project
    template_name = "users/entries/user.html"

    def get_object(self):
        return Project.objects.get(username=self.kwargs.get('username'))


class ProjectCreate(AdminRequiredMixin, SuccessMessageMixin, AsyncFormMixin, edit.CreateView):
    form_class = NewProjectForm
    template_name = "modal/form.html"
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
        info['name'] = info.get('username')
        for k in ['contact_email', 'contact_person', 'contact_phone']:
            info[k] = data.get(k, '')
        info.pop('password')

        # create local user
        proj = Project.objects.create(**info)

        info_msg = 'New Account {} added'.format(proj)

        ActivityLog.objects.log_activity(
            self.request, proj, ActivityLog.TYPE.CREATE, info_msg
        )
        # messages are simply passed down to the template via the request context
        return render(self.request, "users/redirect.html")


class ProjectDelete(AdminRequiredMixin, SuccessMessageMixin, AsyncFormMixin, edit.DeleteView):
    template_name = "modal/delete.html"
    model = User
    success_url = reverse_lazy('user-list')
    success_message = "Account has been deleted"

    def get_object(self):
        obj = self.model.objects.get(username=self.kwargs.get('username'))
        return obj

    def get_context_data(self, **kwargs):
        context = super(ProjectDelete, self).get_context_data(**kwargs)
        context['form_action'] = reverse_lazy('user-delete', kwargs={'username': self.object.username})
        return context

    def delete(self, *args, **kwargs):
        obj = self.get_object()
        info = slap.del_user(obj.username)
        obj.delete()
        self.success_message = "{} account has been deleted".format(kwargs.get('username'))
        return JsonResponse({'url': self.success_url}, safe=False)


def record_logout(sender, user, request, **kwargs):
    """ user logged outof the system """
    ActivityLog.objects.log_activity(request, user, ActivityLog.TYPE.LOGOUT, '{} logged-out'.format(user.username))


def record_login(sender, user, request, **kwargs):
    """ Login a user into the system """
    if user.is_authenticated:
        ActivityLog.objects.log_activity(request, user, ActivityLog.TYPE.LOGIN, '{} logged-in'.format(user.username))
        last_login = ActivityLog.objects.last_login(request)
        if last_login is not None:
            last_host = last_login.ip_number
            message = 'Your previous login was on {date} from {ip}.'.format(
                date=dateformat.format(timezone.localtime(last_login.created), 'M jS @ P'),
                ip=last_host)
            messages.info(request, message)
        elif not request.user.is_staff:
            message = 'You are logging in for the first time. Please make sure your profile is updated.'
            messages.info(request, message)


user_logged_in.connect(record_login)
user_logged_out.connect(record_logout)
