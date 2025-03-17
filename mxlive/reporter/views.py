from collections import defaultdict
from django.conf import settings
from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from django.contrib.messages.views import SuccessMessageMixin
from django.http import JsonResponse, Http404
from django.urls import reverse, reverse_lazy
from django.utils import timezone
from django.views import View
from django.views.generic import DetailView, edit
from itemlist.views import ItemListView

from . import models, forms
from mxlive.utils.mixins import AsyncFormMixin


class AdminRequiredMixin(LoginRequiredMixin, UserPassesTestMixin):
    """
    Mixin to allow access through a view only if the user is a superuser.
    Can be used with any View.
    """
    def test_func(self):
        return self.request.user.is_superuser
    

class ReportView(LoginRequiredMixin, DetailView):
    template_name = 'reporter/report.html'
    model = models.Report

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['report'] = self.object
        context['data_url'] = reverse('report-data', kwargs={'slug': self.object.slug})
        return context


class ReportData(LoginRequiredMixin, View):
    @staticmethod
    def get_report(*args, slug='', **kwargs):

        report = models.Report.objects.filter(slug=slug).first()
        if not report:
            raise Http404('Report not found')

        return {
            'title': report.title,
            'description': report.description,
            'style': f"row {report.style}",
            'content': [block.generate(*args, **kwargs) for block in report.entries.all()],
            'notes': report.notes
        }

    def get(self, request, *args, **kwargs):
        info = self.get_report(*args, **kwargs)
        return JsonResponse({'details': [info]}, safe=False)


class ReportList(LoginRequiredMixin, ItemListView):
    model = models.Report
    list_filters = ['created', 'modified']
    list_columns = ['title', 'slug', 'description']
    list_search = ['slug', 'title', 'description', 'entries__title', 'notes']
    ordering = ['-created']
    paginate_by = 25
    template_name = 'reporter/index.html'
    link_url = 'report-view'
    link_kwarg = 'slug'
    page_title = 'Reports'


class DataSourceList(AdminRequiredMixin, ItemListView):
    model = models.DataSource
    list_filters = ['created', 'modified']
    list_columns = ['name', 'limit']
    list_search = ['fields__name', 'entries__title']
    ordering = ['-created']
    paginate_by = 25
    template_name = 'reporter/list.html'
    tool_template = 'reporter/source-list-tools.html'
    link_url = 'source-editor'
    page_title = 'Data Sources'


class SourceEditor(AdminRequiredMixin, DetailView):
    template_name = 'reporter/source-editor.html'
    model = models.DataSource

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        field_info = defaultdict(list)
        for field in self.object.fields.all().order_by('position'):
            field_info[field.model].append(field)
        context['source'] = self.object
        context['fields'] = dict(field_info)
        return context


class ReportEditor(AdminRequiredMixin, DetailView):
    template_name = 'reporter/report-editor.html'
    model = models.Report

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['report'] = self.object
        context['entries'] = self.object.entries.all()
        context['sources'] = models.DataSource.objects.all()
        context['used_sources'] = models.DataSource.objects.filter(entries__report=self.object).distinct()
        return context


class EditReport(AdminRequiredMixin, SuccessMessageMixin, AsyncFormMixin, edit.UpdateView):
    form_class = forms.ReportForm
    template_name = "modal/form.html"
    model = models.Report
    success_message = "Report has been updated"

    def get_success_url(self):
        return reverse('report-editor', kwargs={'pk': self.object.pk})


class CreateReport(AdminRequiredMixin, SuccessMessageMixin, AsyncFormMixin, edit.CreateView):
    form_class = forms.ReportForm
    template_name = "modal/form.html"
    model = models.Report
    success_message = "Report has been added"

    def get_success_url(self):
        return reverse('report-editor', kwargs={'pk': self.object.pk})


class CreateDataSource(AdminRequiredMixin, SuccessMessageMixin, AsyncFormMixin, edit.CreateView):
    form_class = forms.DataSourceForm
    template_name = "modal/form.html"
    model = models.DataSource
    success_message = "Data source has been added"

    def get_success_url(self):
        return reverse('source-editor', kwargs={'pk': self.object.pk})


class EditDataSource(AdminRequiredMixin, SuccessMessageMixin, AsyncFormMixin, edit.UpdateView):
    form_class = forms.DataSourceForm
    template_name = "modal/form.html"
    model = models.DataSource
    success_message = "Data source has been updated"

    def get_success_url(self):
        return reverse('source-editor', kwargs={'pk': self.object.pk})


class EditSourceField(AdminRequiredMixin, SuccessMessageMixin, AsyncFormMixin, edit.UpdateView):
    form_class = forms.DataFieldForm
    template_name = "modal/form.html"
    model = models.DataField
    success_message = "Field has been updated"

    def get_success_url(self):
        return reverse('source-editor', kwargs={'pk': self.object.source.pk})


class AddSourceField(AdminRequiredMixin, SuccessMessageMixin, AsyncFormMixin, edit.CreateView):
    form_class = forms.DataFieldForm
    template_name = "modal/form.html"
    model = models.DataField
    success_message = "Field has been added"

    def get_success_url(self):
        return reverse('source-editor', kwargs={'pk': self.object.source.pk})

    def get_initial(self):
        initial = super().get_initial()
        initial['source'] = self.kwargs.get('source')
        if 'group' in self.kwargs:
            initial['name'] = self.kwargs.get('group')
            initial['label'] = initial['name'].title()
        initial['position'] = models.DataField.objects.filter(source=initial['source']).count()
        return initial


class AddSourceModel(AdminRequiredMixin, SuccessMessageMixin, AsyncFormMixin, edit.CreateView):
    form_class = forms.DataModelForm
    template_name = "modal/form.html"
    model = models.DataField
    success_message = "Model has been added"

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs['source'] = models.DataSource.objects.filter(pk=self.kwargs.get('source')).first()
        return kwargs

    def get_success_url(self):
        return reverse('source-editor', kwargs={'pk': self.object.source.pk})

    def get_initial(self):
        initial = super().get_initial()
        initial['source'] = self.kwargs.get('source')
        return initial

    def form_valid(self, form):
        data = form.cleaned_data
        response = super().form_valid(form)
        groups = data.pop('groups')
        for i, (name, expression) in enumerate(groups.items()):
            group, created = models.DataField.objects.get_or_create(
                name=name, model=self.object, source=self.object.source
            )
            models.DataField.objects.filter(pk=group.pk).update(
                expression=expression,
                source=self.object.source,
                label=name.title(),
                position=i,
                modified=timezone.now(),
            )
        return response


class EditSourceModel(AdminRequiredMixin, SuccessMessageMixin, AsyncFormMixin, edit.UpdateView):
    form_class = forms.DataModelForm
    template_name = "modal/form.html"
    model = models.DataModel
    success_message = "Model has been updated"

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs['source'] = models.DataSource.objects.filter(pk=self.kwargs.get('source')).first()
        return kwargs

    def get_success_url(self):
        return reverse('source-editor', kwargs={'pk': self.object.source.pk})

    def form_valid(self, form):
        data = form.cleaned_data
        groups = data.pop('groups')
        for i, (name, expression) in enumerate(groups.items()):
            group, created = models.DataField.objects.get_or_create(
                name=name, model=self.object, source=self.object.source
            )
            models.DataField.objects.filter(pk=group.pk).update(
                expression=expression,
                source=self.object.source,
                label=name.title(),
                position=i,
                modified=timezone.now(),
            )
        return super().form_valid(form)


class DeleteSourceModel(AdminRequiredMixin, SuccessMessageMixin, AsyncFormMixin, edit.DeleteView):
    model = models.DataModel
    template_name = "modal/delete.html"
    success_message = "Model has been deleted"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['form_action'] = reverse_lazy(
            'delete-source-model', kwargs={'pk': self.object.pk, 'source': self.object.source.pk}
        )
        return context

    def get_success_url(self):
        return reverse('source-editor', kwargs={'pk': self.object.source.pk})


class EditEntry(AdminRequiredMixin, SuccessMessageMixin, AsyncFormMixin, edit.UpdateView):
    form_class = forms.EntryForm
    template_name = "modal/form.html"
    model = models.Entry
    success_message = "Entry has been updated"

    def get_success_url(self):
        return reverse('report-editor', kwargs={'pk': self.object.report.pk})

    def get_initial(self):
        initial = super().get_initial()
        initial['report'] = self.kwargs.get('report')
        return initial


class DeleteReport(AdminRequiredMixin, SuccessMessageMixin, AsyncFormMixin, edit.DeleteView):
    model = models.Report
    template_name = "modal/delete.html"
    success_message = "Report has been deleted"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['form_action'] = reverse_lazy('delete-report', kwargs={'pk': self.object.pk})
        return context

    def get_success_url(self):
        return reverse('report-list')


class DeleteDataSource(AdminRequiredMixin, SuccessMessageMixin, AsyncFormMixin, edit.DeleteView):
    model = models.DataSource
    template_name = "modal/delete.html"
    success_message = "Data source has been deleted"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['form_action'] = reverse_lazy('delete-data-source', kwargs={'pk': self.object.pk})
        return context

    def get_success_url(self):
        return reverse('data-source-list')


class DeleteEntry(AdminRequiredMixin, SuccessMessageMixin, AsyncFormMixin, edit.DeleteView):
    model = models.Entry
    template_name = "modal/delete.html"
    success_message = "Entry has been deleted"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['form_action'] = reverse_lazy(
            'delete-report-entry', kwargs={'pk': self.object.pk, 'report': self.object.report.pk}
        )
        return context

    def get_success_url(self):
        return reverse('report-editor', kwargs={'pk': self.object.report.pk})


class DeleteSourceField(AdminRequiredMixin, SuccessMessageMixin, AsyncFormMixin, edit.DeleteView):
    model = models.DataField
    template_name = "modal/delete.html"
    success_message = "Field has been deleted"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['form_action'] = reverse_lazy(
            'delete-source-field', kwargs={'pk': self.object.pk, 'source': self.object.source.pk}
        )
        return context

    def get_success_url(self):
        return reverse('source-editor', kwargs={'pk': self.object.source.pk})


class ConfigureEntry(AdminRequiredMixin, SuccessMessageMixin, AsyncFormMixin, edit.UpdateView):
    template_name = "modal/form.html"
    model = models.Entry
    success_message = "Entry has been updated"

    def get_form_class(self):
        return {
            models.Entry.Types.TABLE: forms.TableForm,
            models.Entry.Types.BARS: forms.BarsForm,
            models.Entry.Types.PIE: forms.PieForm,
            models.Entry.Types.PLOT: forms.PlotForm,
            models.Entry.Types.LIST: forms.ListForm,
            models.Entry.Types.TIMELINE: forms.TimelineForm,
            models.Entry.Types.TEXT: forms.RichTextForm,
        }.get(self.object.kind, forms.EntryForm)

    def get_success_url(self):
        return reverse('report-editor', kwargs={'pk': self.object.report.pk})


class CreateEntry(AdminRequiredMixin, SuccessMessageMixin, AsyncFormMixin, edit.CreateView):
    form_class = forms.EntryForm
    template_name = "modal/form.html"
    model = models.Entry
    success_message = "Entry has been added"

    def get_success_url(self):
        return reverse('report-editor', kwargs={'pk': self.object.report.pk})

    def get_initial(self):
        report = models.Report.objects.filter(pk=self.kwargs.get('report')).first()
        if not report:
            raise Http404('Report not found')
        initial = super().get_initial()
        initial['report'] = self.kwargs.get('report')
        initial['position'] = report.entries.count()
        return initial
