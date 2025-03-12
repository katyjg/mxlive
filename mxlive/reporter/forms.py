from datetime import datetime
from crispy_forms.bootstrap import StrictButton
from crispy_forms.helper import FormHelper
from crispy_forms.layout import Div, Field, Layout
from django import forms
from django.urls import reverse_lazy
from django.utils.translation import gettext as _

from . import models
from .utils import COLOR_CHOICES


class BodyHelper(FormHelper):
    def __init__(self, form):
        super().__init__(form)
        self.form_tag = False
        self.use_custom_control = True
        self.form_show_errors = False


class FooterHelper(FormHelper):
    def __init__(self, form):
        super().__init__(form)
        self.form_tag = False
        self.disable_csrf = True
        self.form_show_errors = False


disabled_widget = forms.HiddenInput(attrs={'readonly': True})


class ReportForm(forms.ModelForm):
    class Meta:
        model = models.Report
        fields = ('title', 'slug', 'description', 'style', 'notes')
        widgets = {
            'title': forms.Textarea(attrs={'rows': "2"}),
            'description': forms.Textarea(attrs={'rows': "4"}),
            'notes': forms.Textarea(attrs={'rows': "6"}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        pk = self.instance.pk

        self.body = BodyHelper(self)
        self.footer = FooterHelper(self)
        if pk:
            self.body.title = _("Edit Report")
            self.body.form_action = reverse_lazy('edit-report', kwargs={'pk': pk})
        else:
            self.body.title = _("Create Report")
            self.body.form_action = reverse_lazy('new-report')

        self.body.layout = Layout(
            Div(
                Div('title', css_class='col-12'),
                css_class='row'
            ),
            Div(
                Div('slug', css_class='col-6'),
                Div('style', css_class='col-6'),
                css_class='row'
            ),
            Div(
                Div('description', css_class='col-12'),
                Div('notes', css_class='col-12'),
                css_class='row'
            ),
        )
        self.footer.layout = Layout(
            StrictButton('Revert', type='reset', value='Reset', css_class="btn btn-secondary"),
            StrictButton('Save', type='submit', name="submit", value='submit', css_class='btn btn-primary'),
        )


class DataFieldForm(forms.ModelForm):
    class Meta:
        model = models.DataField
        fields = (
            'name', 'kind', 'model', 'label', 'default', 'expression', 'precision',
            'source', 'position', 'grouped', 'filterable', 'ordering',
        )
        widgets = {
            'default': forms.TextInput(),
            'expression': forms.Textarea(attrs={'rows': "2"}),
            'source': forms.HiddenInput(),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self.body = BodyHelper(self)
        self.footer = FooterHelper(self)
        pk = self.instance.pk
        self.fields['source'].widget = forms.HiddenInput()

        if pk:
            self.body.title = _("Edit Field")
            self.body.form_action = reverse_lazy(
                'edit-source-field', kwargs={'pk': pk, 'source': self.instance.source.pk}
            )
        else:
            self.body.title = _("Add Field")
            self.body.form_action = reverse_lazy(
                'add-source-field', kwargs={'source': self.initial['source']}
            )

        self.footer.layout = Layout()
        self.body.layout = Layout(
            Div(
                Div('name', css_class='col-6'),
                Div('label', css_class="col-6"),
                css_class='row'
            ),
            Div(
                Div('kind', css_class='col-4'),
                Div(Field('model', css_class='select'), css_class="col-4"),
                Div('ordering', css_class='col-4'),
                css_class='row'
            ),
            Div(
                Div('default', css_class='col-4'),
                Div('precision', css_class='col-4'),
                Div('position', css_class='col-4'),
                css_class='row'
            ),
            Div(
                Div('expression', css_class='col-12'),
                Field('source'),
                css_class='row'
            ),
            Div(
                Div(
                    Div('grouped', css_class='col-4'),
                    Div('filterable', css_class='col-4'),
                    css_class='row'
                ),
            ),
        )
        self.footer.layout = Layout(
            StrictButton('Save', type='submit', name="submit", value='submit', css_class='btn btn-primary'),
        )


class DataSourceForm(forms.ModelForm):
    class Meta:
        model = models.DataSource
        fields = (
            'name', 'limit'
        )
        help_texts = {
            'limit': _("Maximum number of records"),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        pk = self.instance.pk

        self.body = BodyHelper(self)
        self.footer = FooterHelper(self)

        if pk:
            self.body.title = u"Edit Data Source"
            self.body.form_action = reverse_lazy('edit-data-source', kwargs={'pk': pk})
        else:
            self.body.title = u"Add Data Source"
            self.body.form_action = reverse_lazy('new-data-source')

        self.body.layout = Layout(
            Div(
                Div('name', css_class='col-8'),
                Div('limit', css_class='col-4'),
                css_class='row'
            ),
        )
        self.footer.layout = Layout(
            StrictButton('Revert', type='reset', value='Reset', css_class="btn btn-secondary"),
            StrictButton('Save', type='submit', name="submit", value='save', css_class='btn btn-primary'),
        )


class EntryForm(forms.ModelForm):
    class Meta:
        model = models.Entry
        fields = (
            'title', 'description', 'notes', 'style', 'kind', 'source', 'report', 'position'
        )
        widgets = {
            'title': forms.TextInput(),
            'description': forms.TextInput(),
            'notes': forms.Textarea(attrs={'rows': "4"}),
            'report': forms.HiddenInput(),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        pk = self.instance.pk

        self.body = BodyHelper(self)
        self.footer = FooterHelper(self)

        if pk:
            self.body.title = _("Edit Entry")
            self.body.form_action = reverse_lazy(
                'edit-report-entry', kwargs={'pk': pk, 'report': self.instance.report.pk}
            )
        else:
            if 'report' in self.initial:
                self.body.title = _("Add Entry to {}".format(self.initial['report']))
                self.body.form_action = reverse_lazy(
                    'add-report-entry', kwargs={'report': self.initial['report']}
                )
            self.body.title = _("Add Entry")

        self.body.layout = Layout(
            Div(
                Div('title', css_class='col-10'),
                Div('position', css_class='col-2'),
                css_class='row'
            ),
            Div(
                Div('description', css_class='col-12'),
                css_class='row'
            ),
            Div(
                Div('kind', css_class='col-4'),
                Div('source', css_class='col-4'),
                Div('style', css_class='col-4'),
                css_class='row'
            ),
            Div(
                Div('notes', css_class='col-12'),
                Field('report'),
                css_class='row'
            ),
        )
        self.footer.layout = Layout(
            StrictButton('Revert', type='reset', value='Reset', css_class="btn btn-secondary"),
            StrictButton('Save', type='submit', name="submit", value='submit', css_class='btn btn-primary'),
        )

    def clean(self):
        cleaned_data = super().clean()
        kind = cleaned_data.get('kind')
        source = cleaned_data.get('source')
        if kind != models.Entry.Types.TEXT and not source:
            self.add_error('source', _("This field is required for the selected entry type"))
        return cleaned_data


class TableForm(forms.ModelForm):
    columns = forms.ModelChoiceField(label='Columns', required=True, queryset=models.DataField.objects.none())
    rows = forms.ModelMultipleChoiceField(label='Rows', required=True, queryset=models.DataField.objects.none())
    values = forms.ModelChoiceField(label='Values', required=False, queryset=models.DataField.objects.none())
    total_column = forms.BooleanField(label="Row Totals", required=False)
    total_row = forms.BooleanField(label="Column Totals", required=False)
    force_strings = forms.BooleanField(label="Force Strings", required=False)
    transpose = forms.BooleanField(label="Transpose", required=False)

    class Meta:
        model = models.Entry
        fields = (
            'attrs', 'columns', 'rows', 'values', 'total_row', 'total_column', 'force_strings', 'transpose',
        )
        widgets = {
            'attrs': forms.HiddenInput(),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self.body = BodyHelper(self)
        self.footer = FooterHelper(self)

        self.body.title = _("Configure Table")
        self.body.form_action = reverse_lazy(
            'configure-report-entry', kwargs={'pk': self.instance.pk, 'report': self.instance.report.pk}
        )
        self.update_initial()
        self.body.layout = Layout(
            Div(
                Div(Field('rows', css_class='select'), css_class='col-12'),
                Div(Field('columns', css_class='select'), css_class='col-6'),
                Div(Field('values', css_class='select'), css_class='col-6'),
                css_class='row'
            ),
            Div(
                Div('total_row', css_class='col-6'),
                Div('total_column', css_class='col-6'),
                Div('force_strings', css_class='col-6'),
                Div('transpose', css_class='col-6'),
                css_class='row'
            ),
            Div(

                Field('attrs'),
                css_class='row'
            ),
        )
        self.footer.layout = Layout(
            StrictButton('Revert', type='reset', value='Reset', css_class="btn btn-secondary"),
            StrictButton('Save', type='submit', name="submit", value='submit', css_class='btn btn-primary'),
        )

    def update_initial(self):
        attrs = self.instance.attrs
        for field in ['columns', 'values', 'rows']:
            self.fields[field].queryset = self.instance.source.fields.all()

        for field in ['columns', 'values']:
            if field in attrs:
                self.fields[field].initial = self.instance.source.fields.filter(name=attrs[field]).first()
        if 'rows' in attrs:
            self.fields['rows'].initial = self.instance.source.fields.filter(name__in=attrs['rows'])

        for field in ['total_row', 'total_column', 'force_strings', 'transpose']:
            if field in attrs:
                self.fields[field].initial = attrs[field]

    def clean(self):
        cleaned_data = super().clean()
        new_attrs = {}
        for field in ['columns', 'values']:
            if field in cleaned_data and cleaned_data[field] is not None:
                new_attrs[field] = cleaned_data[field].name

        if 'rows' in cleaned_data:
            new_attrs['rows'] = [y.name for y in cleaned_data['rows'].order_by('position')]

        for field in ['total_row', 'total_column', 'force_strings', 'transpose']:
            if field in cleaned_data and cleaned_data[field] is not None:
                new_attrs[field] = cleaned_data[field]

        cleaned_data['attrs'] = {k: v for k, v in new_attrs.items() if v not in [None, []]}
        return cleaned_data


class BarsForm(forms.ModelForm):
    x_axis = forms.ModelChoiceField(label='X-axis', required=True, queryset=models.DataField.objects.none())
    y_axis = forms.ModelMultipleChoiceField(label='Y-axis', required=True, queryset=models.DataField.objects.none())
    y_value = forms.ModelChoiceField(label='Values', required=False, queryset=models.DataField.objects.none())

    stack_0 = forms.ModelMultipleChoiceField(label='Stack', required=False, queryset=models.DataField.objects.none())
    stack_1 = forms.ModelMultipleChoiceField(label='Stack', required=False, queryset=models.DataField.objects.none())
    stack_2 = forms.ModelMultipleChoiceField(label='Stack', required=False, queryset=models.DataField.objects.none())

    color_field = forms.ModelChoiceField(label='Color By', required=False, queryset=models.DataField.objects.none())
    colors = forms.ChoiceField(label='Color Scheme', required=False, choices=COLOR_CHOICES, initial='Live8')
    line = forms.ModelChoiceField(label='Line', required=False, queryset=models.DataField.objects.none())
    x_culling = forms.IntegerField(label="Culling", required=False)
    wrap_x_labels = forms.BooleanField(label="Wrap Labels", required=False)
    aspect_ratio = forms.FloatField(label="Bar Width", required=False, help_text="Aspect ratio of the bars")
    vertical = forms.BooleanField(label="Vertical Bars", required=False)

    sort_by = forms.ModelChoiceField(label='Sort By', required=False, queryset=models.DataField.objects.none())
    sort_desc = forms.BooleanField(label="Sort Descending", required=False)
    limit = forms.IntegerField(label="Limit", required=False)

    class Meta:
        model = models.Entry
        fields = (
            'attrs', 'x_axis', 'y_axis', 'y_value', 'stack_0', 'stack_1', 'stack_2', 'color_field', 'line',
            'x_culling', 'wrap_x_labels', 'aspect_ratio', 'sort_by', 'sort_desc', 'vertical', 'limit',
            'colors'
        )
        widgets = {
            'attrs': forms.HiddenInput(),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self.body = BodyHelper(self)
        self.footer = FooterHelper(self)

        self.body.title = _("Configure Barchart")
        self.body.form_action = reverse_lazy(
            'configure-report-entry', kwargs={'pk': self.instance.pk, 'report': self.instance.report.pk}
        )
        self.update_initial()
        self.body.layout = Layout(
            Div(
                Div(Field('x_axis', css_class='select'), css_class='col-4'),
                Div(Field('y_axis', css_class='select'), css_class='col-8'),
                css_class='row'
            ),
            Div(
                Div(Field('y_value', css_class='select'), css_class='col-3'),
                Div(Field('sort_by', css_class='select'), css_class='col-3'),
                Div(Field('color_field', css_class='select'), css_class='col-3'),
                Div(Field('colors', css_class='select'), css_class='col-3'),
                css_class='row'
            ),
            Div(
                Div('aspect_ratio', css_class='col-3'),
                Div('x_culling', css_class='col-3'),
                Div('limit', css_class='col-3'),
                Div(Field('line', css_class='select'), css_class='col-3'),
                css_class='row'
            ),
            Div(
                Div(Field('stack_0', css_class='select'), css_class='col-12'),
                Div(Field('stack_1', css_class='select'), css_class='col-12'),
                Div(Field('stack_2', css_class='select'), css_class='col-12'),
                css_class='row'
            ),
            Div(
                Div(
                    Div('wrap_x_labels', css_class='col-4'),
                    Div('vertical', css_class='col-4'),
                    Div('sort_desc', css_class='col-4'),
                    css_class='row'
                ),
                Field('attrs'),
            ),
        )
        self.footer.layout = Layout(
            StrictButton('Revert', type='reset', value='Reset', css_class="btn btn-secondary"),
            StrictButton('Save', type='submit', name="submit", value='submit', css_class='btn btn-primary'),
        )

    def update_initial(self):
        attrs = self.instance.attrs
        for field in ['x_axis', 'y_axis', 'y_value', 'stack_0', 'stack_1', 'stack_2', 'color_field', 'line', 'sort_by']:
            self.fields[field].queryset = self.instance.source.fields.all()

        for field in ['x_axis', 'y_value', 'line', 'color_field', 'sort_by']:
            if field in attrs:
                self.fields[field].initial = self.instance.source.fields.filter(name=attrs[field]).first()
        if 'y_axis' in attrs:
            self.fields['y_axis'].initial = self.instance.source.fields.filter(name__in=attrs['y_axis'])

        if 'stack' in attrs:
            for i, stack in enumerate(attrs['stack']):
                self.fields[f'stack_{i}'].initial = self.instance.source.fields.filter(name__in=stack)

        for field in ['x_culling', 'wrap_x_labels', 'aspect_ratio', 'sort_desc', 'limit', 'colors']:
            if field in attrs:
                self.fields[field].initial = attrs[field]

        self.fields['vertical'].initial = attrs.get('vertical', True)

    def clean(self):
        cleaned_data = super().clean()
        new_attrs = {}

        for field in ['x_axis', 'y_value', 'line', 'color_field', 'sort_by']:
            if field in cleaned_data and cleaned_data[field] is not None:
                new_attrs[field] = cleaned_data[field].name

        if 'y_axis' in cleaned_data and cleaned_data['y_axis'].exists():
            new_attrs['y_axis'] = [y.name for y in cleaned_data['y_axis'].order_by('position')]

        stack = []
        for i in range(3):
            if f'stack_{i}' in cleaned_data and cleaned_data[f'stack_{i}'].exists():
                stack.append([y.name for y in cleaned_data[f'stack_{i}'].order_by('position')])

        if stack:
            new_attrs['stack'] = stack

        for field in ['x_culling', 'wrap_x_labels', 'aspect_ratio', 'vertical', 'sort_desc', 'limit', 'colors']:
            if field in cleaned_data and cleaned_data[field] is not None:
                new_attrs[field] = cleaned_data[field]

        cleaned_data['attrs'] = {k: v for k, v in new_attrs.items() if v not in [None, []]}
        return cleaned_data


class PlotForm(forms.ModelForm):
    x_axis = forms.ModelChoiceField(label='X-axis', required=True, queryset=models.DataField.objects.none())
    y1_axis = forms.ModelMultipleChoiceField(label='Y1-axis', required=True, queryset=models.DataField.objects.none())
    y2_axis = forms.ModelMultipleChoiceField(label='Y2-axis', required=False, queryset=models.DataField.objects.none())
    y1_label = forms.CharField(label='Y1 Label', required=False)
    y2_label = forms.CharField(label='Y2 Label', required=False)
    colors = forms.ChoiceField(label='Color Scheme', required=False, choices=COLOR_CHOICES, initial='Live8')

    tick_precision = forms.IntegerField(label="Precision", required=False)
    scatter = forms.BooleanField(label="Scatter Plot", required=False)

    class Meta:
        model = models.Entry
        fields = (
            'attrs', 'x_axis', 'y1_axis', 'y1_axis', 'y2_axis', 'y2_label', 'tick_precision', 'scatter', 'colors'
        )
        widgets = {
            'attrs': forms.HiddenInput(),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self.body = BodyHelper(self)
        self.footer = FooterHelper(self)

        self.body.title = _("Configure Plot")
        self.body.form_action = reverse_lazy(
            'configure-report-entry', kwargs={'pk': self.instance.pk, 'report': self.instance.report.pk}
        )
        self.update_initial()
        self.body.layout = Layout(
            Div(
                Div(Field('x_axis', css_class='select'), css_class='col-6'),
                Div('tick_precision', css_class='col-3'),
                Div(Field('colors', css_class='select'), css_class='col-3'),
                css_class='row'
            ),
            Div(
                Div('y1_label', css_class='col-3'),
                Div(Field('y1_axis', css_class='select'), css_class='col-9'),
                css_class='row'
            ),
            Div(
                Div('y2_label', css_class='col-3'),
                Div(Field('y2_axis', css_class='select'), css_class='col-9'),
                css_class='row'
            ),
            Div(
                Div(
                    Div('scatter', css_class='col-4'),
                    css_class='row'
                ),
                Field('attrs'),
            ),
        )
        self.footer.layout = Layout(
            StrictButton('Revert', type='reset', value='Reset', css_class="btn btn-secondary"),
            StrictButton('Save', type='submit', name="submit", value='submit', css_class='btn btn-primary'),
        )

    def update_initial(self):
        attrs = self.instance.attrs
        for field in ['x_axis', 'y1_axis', 'y2_axis']:
            self.fields[field].queryset = self.instance.source.fields.all()

        if 'x_axis' in attrs:
            self.fields['x_axis'].initial = self.instance.source.fields.filter(name=attrs['x_axis']).first()

        if 'y_axis' in attrs:
            for i, y_group in enumerate(attrs['y_axis']):
                self.fields[f'y{i + 1}_axis'].initial = self.instance.source.fields.filter(name__in=y_group)

        for field in ['y1_label', 'y2_label', 'tick_precision', 'scatter', 'aspect_ratio', 'colors']:
            if field in attrs:
                self.fields[field].initial = attrs[field]

    def clean(self):
        cleaned_data = super().clean()
        new_attrs = {
            'y_axis': []
        }

        for field in ['x_axis']:
            if field in cleaned_data and cleaned_data[field] is not None:
                new_attrs[field] = cleaned_data[field].name

        for i in range(2):
            if f'y{i + 1}_axis' in cleaned_data and cleaned_data[f'y{i + 1}_axis'].exists():
                new_attrs[f'y_axis'].append([y.name for y in cleaned_data[f'y{i + 1}_axis']])

        for field in ['y1_label', 'y2_label', 'tick_precision', 'scatter', 'colors']:
            if field in cleaned_data:
                new_attrs[field] = cleaned_data[field]

        cleaned_data['attrs'] = {k: v for k, v in new_attrs.items() if v not in [None, []]}
        return cleaned_data


class ListForm(forms.ModelForm):
    columns = forms.ModelMultipleChoiceField(label='Columns', required=True, queryset=models.DataField.objects.none())
    order_by = forms.ModelChoiceField(label='Order By', required=False, queryset=models.DataField.objects.none())
    order_desc = forms.BooleanField(label='Descending Order', required=False)
    limit = forms.IntegerField(label='Limit', required=False)

    class Meta:
        model = models.Entry
        fields = (
            'attrs', 'columns', 'limit', 'order_by', 'order_desc'
        )
        widgets = {
            'attrs': forms.HiddenInput(),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self.body = BodyHelper(self)
        self.footer = FooterHelper(self)

        self.body.title = _("Configure List")
        self.body.form_action = reverse_lazy(
            'configure-report-entry', kwargs={'pk': self.instance.pk, 'report': self.instance.report.pk}
        )
        self.update_initial()
        self.body.layout = Layout(
            Div(
                Div(Field('columns', css_class='select'), css_class='col-12'),
                css_class='row'
            ),
            Div(
                Div(Field('order_by', css_class='select'), css_class='col-6'),
                Div('limit', css_class='col-6'),
                css_class='row'
            ),
            Div(
                Div('order_desc', css_class='col-4'),
                css_class='row'
            ),
            Div(
                Field('attrs'),
            ),
        )
        self.footer.layout = Layout(
            StrictButton('Revert', type='reset', value='Reset', css_class="btn btn-secondary"),
            StrictButton('Save', type='submit', name="submit", value='submit', css_class='btn btn-primary'),
        )

    def update_initial(self):
        attrs = self.instance.attrs
        for field in ['columns', 'order_by']:
            self.fields[field].queryset = self.instance.source.fields.all()

        if 'columns' in attrs:
            self.fields['columns'].initial = self.instance.source.fields.filter(name__in=attrs['columns'])

        if 'order_by' in attrs:
            order_by, order_desc = (attrs['order_by'][1:], True) if attrs['order_by'][0] == '-' else (attrs['order_by'], False)
            self.fields['order_by'].initial = self.instance.source.fields.filter(name=order_by).first()
            self.fields['order_desc'].initial = order_desc

        if 'limit' in attrs:
            self.fields['limit'].initial = attrs['limit']

    def clean(self):
        cleaned_data = super().clean()
        new_attrs = {}

        if 'columns' in cleaned_data and cleaned_data['columns'].exists():
            new_attrs['columns'] = [
                y.name for y in cleaned_data['columns'].order_by('position')
            ]
        if 'order_by' in cleaned_data and cleaned_data['order_by'] is not None:
            prefix = '-' if cleaned_data.get('order_desc') else ''
            new_attrs['order_by'] = f"{prefix}{cleaned_data['order_by'].name}"

        for field in ['limit']:
            if field in cleaned_data and cleaned_data[field] is not None:
                new_attrs[field] = cleaned_data[field]

        cleaned_data['attrs'] = {k: v for k, v in new_attrs.items() if v not in [None, []]}
        return cleaned_data


class PieForm(forms.ModelForm):
    value = forms.ModelChoiceField(label='Value', required=True, queryset=models.DataField.objects.none())
    label = forms.ModelChoiceField(label='Label', required=True, queryset=models.DataField.objects.none())
    colors = forms.ChoiceField(label='Color Scheme', required=False, choices=COLOR_CHOICES, initial='Live8')

    class Meta:
        model = models.Entry
        fields = (
            'attrs', 'value', 'label', 'colors',
        )
        widgets = {
            'attrs': forms.HiddenInput(),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self.body = BodyHelper(self)
        self.footer = FooterHelper(self)

        self.body.title = _("Configure Pie")
        self.body.form_action = reverse_lazy(
            'configure-report-entry', kwargs={'pk': self.instance.pk, 'report': self.instance.report.pk}
        )
        self.update_initial()
        self.body.layout = Layout(
            Div(
                Div(Field('value', css_class='select'), css_class='col-4'),
                Div(Field('label', css_class='select'), css_class='col-4'),
                Div(Field('colors', css_class='select'), css_class='col-4'),
                css_class='row'
            ),
            Div(
                Field('attrs'),
            ),
        )
        self.footer.layout = Layout(
            StrictButton('Revert', type='reset', value='Reset', css_class="btn btn-secondary"),
            StrictButton('Save', type='submit', name="submit", value='submit', css_class='btn btn-primary'),
        )

    def update_initial(self):
        attrs = self.instance.attrs
        for field in ['value', 'label']:
            self.fields[field].queryset = self.instance.source.fields.all()

        for field in ['value', 'label']:
            if field in attrs:
                self.fields[field].initial = self.instance.source.fields.filter(name=attrs[field]).first()
        for field in ['colors']:
            if field in attrs:
                self.fields[field].initial = attrs[field]

    def clean(self):
        cleaned_data = super().clean()
        new_attrs = {}

        for field in ['value', 'label']:
            if field in cleaned_data and cleaned_data[field] is not None:
                new_attrs[field] = cleaned_data[field].name
        for field in ['colors']:
            if field in cleaned_data:
                new_attrs[field] = cleaned_data[field]

        cleaned_data['attrs'] = {k: v for k, v in new_attrs.items() if v not in [None, []]}
        return cleaned_data


class TimelineForm(forms.ModelForm):
    min_time = forms.DateTimeField(label='Start Time', required=False)
    max_time = forms.DateTimeField(label='End Time', required=False)
    start_field = forms.ModelChoiceField(label='Event Start', required=True, queryset=models.DataField.objects.none())
    end_field = forms.ModelChoiceField(label='Event End', required=True, queryset=models.DataField.objects.none())
    label_field = forms.ModelChoiceField(label='Event Label', required=False, queryset=models.DataField.objects.none())
    type_field = forms.ModelChoiceField(label='Event Type', required=False, queryset=models.DataField.objects.none())
    colors = forms.ChoiceField(label='Color Scheme', required=False, choices=COLOR_CHOICES, initial='Live8')

    class Meta:
        model = models.Entry
        fields = (
            'attrs', 'min_time', 'max_time', 'start_field', 'end_field', 'label_field', 'type_field', 'colors',
        )
        widgets = {
            'attrs': forms.HiddenInput(),
            'min_time': forms.DateTimeInput(attrs={'placeholder': 'YYYY-MM-DD HH:MM:SS'}),
            'max_time': forms.DateTimeInput(attrs={'placeholder': 'YYYY-MM-DD HH:MM:SS'}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self.body = BodyHelper(self)
        self.footer = FooterHelper(self)

        self.body.title = _("Configure Timeline")
        self.body.form_action = reverse_lazy(
            'configure-report-entry', kwargs={'pk': self.instance.pk, 'report': self.instance.report.pk}
        )
        self.update_initial()
        self.body.layout = Layout(
            Div(
                Div(Field('start_field', css_class='select'), css_class='col-3'),
                Div(Field('end_field', css_class='select'), css_class='col-3'),
                Div(Field('label_field', css_class='select'), css_class='col-3'),
                Div(Field('type_field', css_class='select'), css_class='col-3'),
                css_class='row'
            ),
            Div(
                Div(Field('min_time', css_class='datetime'), css_class='col-4'),
                Div(Field('max_time', css_class='datetime'), css_class='col-4'),
                Div(Field('colors', css_class='select'), css_class='col-4'),
                css_class='row'
            ),
        )
        self.footer.layout = Layout(
            StrictButton('Revert', type='reset', value='Reset', css_class="btn btn-secondary"),
            StrictButton('Save', type='submit', name="submit", value='submit', css_class='btn btn-primary'),
        )

    def update_initial(self):
        attrs = self.instance.attrs
        for field in ['start_field', 'end_field', 'label_field', 'type_field']:
            self.fields[field].queryset = self.instance.source.fields.all()

        for field in ['start_field', 'end_field', 'label_field', 'type_field']:
            if field in attrs:
                self.fields[field].initial = self.instance.source.fields.filter(name=attrs[field]).first()
        for field in ['colors']:
            if field in attrs:
                self.fields[field].initial = attrs[field]
        for field in ['min_time', 'max_time']:
            if field in attrs:
                self.fields[field].initial = datetime.fromtimestamp(attrs[field]/1000)

    def clean(self):
        cleaned_data = super().clean()
        new_attrs = {}

        for field in ['start_field', 'end_field', 'label_field', 'type_field']:
            if field in cleaned_data and cleaned_data[field] is not None:
                new_attrs[field] = cleaned_data[field].name

        for field in ['min_time', 'max_time']:
            if field in cleaned_data and cleaned_data[field] is not None:
                new_attrs[field] = int(cleaned_data[field].timestamp()*1000)

        for field in ['colors']:
            if field in cleaned_data:
                new_attrs[field] = cleaned_data[field]

        cleaned_data['attrs'] = {k: v for k, v in new_attrs.items() if v not in [None, []]}
        return cleaned_data


class RichTextForm(forms.ModelForm):
    rich_text = forms.CharField(
        label='Rich Text', required=True, widget=forms.Textarea(attrs={'rows': 15}),
        help_text=_("Use markdown syntax to format the text")
    )

    class Meta:
        model = models.Entry
        fields = (
            'attrs', 'rich_text',
        )
        widgets = {
            'attrs': forms.HiddenInput(),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self.body = BodyHelper(self)
        self.footer = FooterHelper(self)

        self.body.title = _("Configure Rich Text")
        self.body.form_action = reverse_lazy(
            'configure-report-entry', kwargs={'pk': self.instance.pk, 'report': self.instance.report.pk}
        )
        self.update_initial()
        self.body.layout = Layout(
            Div(
                Div('rich_text', css_class='col-12'),
                css_class='row'
            ),
        )
        self.footer.layout = Layout(
            StrictButton('Revert', type='reset', value='Reset', css_class="btn btn-secondary"),
            StrictButton('Save', type='submit', name="submit", value='submit', css_class='btn btn-primary'),
        )

    def update_initial(self):
        attrs = self.instance.attrs
        for field in ['rich_text']:
            if field in attrs:
                self.fields[field].initial = attrs[field]

    def clean(self):
        cleaned_data = super().clean()
        new_attrs = {}

        for field in ['rich_text']:
            if field in cleaned_data and cleaned_data[field] is not None:
                new_attrs[field] = cleaned_data[field]

        cleaned_data['attrs'] = {k: v for k, v in new_attrs.items() if v not in [None, []]}
        return cleaned_data
