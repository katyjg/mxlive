from typing import Any

from django.apps import apps
from django.db import models
from django.db.models import Case, When, Value, CharField, QuerySet
from django.db.models.functions import Round
from django.utils.text import gettext_lazy as _
from . import utils
from .sources import regroup_data

VALUE_TYPES = {
    'STRING': str,
    'INTEGER': int,
    'FLOAT': float,
}


# Create your models here.
class WithChoices(Case):
    """Queries display names for a Django choices field"""

    def __init__(self, model, field_ref, condition=None, then=None, **lookups):
        field_name = field_ref.split('__')[-1]
        choices = dict(model._meta.get_field(field_name).flatchoices)
        whens = [When(**{field_ref: k, 'then': Value(v)}) for k, v in choices.items()]
        super().__init__(*whens, output_field=CharField())


class DataModel(models.Model):
    """
    Model definition for DataModel. This model is used to define allowed data models
    and corresponding fields for the reporter app.
    """
    name = models.CharField(max_length=150)
    fields = models.JSONField(default=list)

    def __str__(self):
        return self.name


class DataSource(models.Model):
    name = models.CharField(max_length=50)
    group_by = models.JSONField(default=list, blank=True)
    order_by = models.JSONField(default=list, blank=True)
    filters = models.JSONField(default=dict, blank=True)
    order_fields = models.JSONField(default=list, blank=True)
    group_fields = models.JSONField(default=list, blank=True)
    filter_fields = models.JSONField(default=dict, blank=True)
    limit = models.IntegerField(null=True, blank=True)

    def __str__(self):
        return self.name

    def get_labels(self):
        return {field.name: field.label for field in self.fields.all()}

    def get_queryset(self, model_name, filters=None, group_by=None, order_by=None) -> QuerySet:

        model: Any = apps.get_model(model_name)
        queryset = model.objects.all()

        # Apply static filters
        if self.filters:
            queryset = queryset.filter(**self.filters)

        # Apply dynamic filters
        if filters:
            queryset = queryset.filter(**filters)

        # Add annotations
        annotations = {
            field.name: field.get_expression()
            for field in self.fields.filter(model__name=model_name, kind=DataField.FieldType.ANNOTATION)
        }
        if annotations:
            queryset = queryset.annotate(**annotations)

        # Add aggregations and handle grouping
        group_fields: list = group_by or self.group_by
        if group_fields:
            aggregations = {
                field.name: field.get_expression()
                for field in self.fields.filter(model__name=model_name, kind=DataField.FieldType.AGGREGATION)
            }
            queryset = queryset.values(*group_fields).annotate(**aggregations)

        # Apply sorting
        order_by: list = order_by or self.order_by
        if order_by:
            queryset = queryset.order_by(*order_by)

        # Apply limit
        if self.limit:
            queryset = queryset[:self.limit]

        return queryset

    def validate_filters(self, params) -> dict:
        """
        Validate dynamic filters from request parameters
        """

        valid_filters = {}
        for key, value_type in self.filter_fields.items():
            if key in params:
                try:
                    value = params.get(key)
                    filter_type = VALUE_TYPES[value_type]
                    valid_filters[key] = filter_type(value)
                except (ValueError, KeyError):
                    pass    # Ignore invalid values
        return valid_filters

    def validate_grouping(self, params) -> list[str]:
        """
        Validate grouping fields from request parameters
        """
        group_by = params.getlist("group_by")
        valid_grouping = [field for field in group_by if field in self.group_fields]
        return valid_grouping

    def validate_ordering(self, params) -> list[str]:
        """
        Validate ordering fields from request parameters
        """
        order_by = params.getlist("order_by")
        valid_ordering = [field for field in order_by if field.lstrip('-') in self.order_fields]
        return valid_ordering

    def get_data(self, filters=None, group_by=None, order_by=None) -> list[dict]:
        """
        Generate data for this data source
        :param filters: dynamic filters
        :param group_by: group by fields
        :param order_by: order by fields

        """

        data = []
        for model_name in self.fields.values_list('model__name', flat=True).distinct():
            queryset = self.get_queryset(model_name, filters=filters, group_by=group_by, order_by=order_by)
            data.extend(
                list(queryset.values(*(field.name for field in self.fields.filter(model__name=model_name).all())))
            )
        return data


class DataField(models.Model):
    class FieldType(models.TextChoices):
        ANNOTATION = 'annotation', _('Annotation')
        AGGREGATION = 'aggregation', _('Aggregation')

    name = models.SlugField(max_length=50)
    kind = models.CharField(max_length=50, choices=FieldType.choices, default=FieldType.ANNOTATION)
    model = models.ForeignKey(DataModel, on_delete=models.CASCADE)
    label = models.CharField(max_length=100, null=True)
    default = models.JSONField(null=True, blank=True)
    expression = models.TextField(default="", blank=True)
    precision = models.IntegerField(null=True, blank=True)
    source = models.ForeignKey(DataSource, on_delete=models.CASCADE, related_name='fields')

    class Meta:
        unique_together = ['name', 'source', 'model']

    def __str__(self):
        return self.label

    def get_expression(self) -> models.Expression:
        if self.expression:
            db_expression = utils.expr.parse(self.expression)
            print(db_expression, self.expression)
            if self.precision is not None:
                db_expression = Round(db_expression, self.precision)
            return db_expression


class Report(models.Model):
    slug = models.SlugField(max_length=128, unique=True)
    title = models.TextField()
    description = models.TextField(default='', blank=True)
    style = models.CharField(max_length=100, default='', blank=True)
    notes = models.TextField(default='', blank=True)

    def __str__(self):
        return self.title


class Entry(models.Model):
    class Types(models.TextChoices):
        BARS = 'bars', _('Bar Chart')
        TABLE = 'table', _('Table')
        LIST = 'list', _('List')
        PLOT = 'plot', _('XY Plot')
        PIE = 'pie', _('Pie Chart')
        HISTOGRAM = 'histogram', _('Histogram')
        TIMELINE = 'timeline', _('Timeline')

    title = models.TextField(default='', blank=True)
    description = models.TextField(default='', blank=True)
    notes = models.TextField(default='', blank=True)
    style = models.CharField(max_length=100, default='', blank=True)
    kind = models.CharField(max_length=50, choices=Types.choices, default=Types.TABLE)
    source = models.ForeignKey(DataSource, on_delete=models.CASCADE)
    report = models.ForeignKey(Report, on_delete=models.CASCADE, related_name='entries')
    order = models.IntegerField(default=0)
    attrs = models.JSONField(default=dict, blank=True)

    class Meta:
        verbose_name_plural = 'Entries'

    def __str__(self):
        return self.title

    def generate(self, *args, **kwargs):
        if self.kind == self.Types.BARS:
            return self.generate_bars(*args, **kwargs)
        elif self.kind == self.Types.TABLE:
            return self.generate_table(*args, **kwargs)
        elif self.kind == self.Types.LIST:
            return self.generate_list(*args, **kwargs)
        elif self.kind == self.Types.PLOT:
            return self.generate_plot(*args, **kwargs)
        elif self.kind == self.Types.PIE:
            return self.generate_pie(*args, **kwargs)
        elif self.kind == self.Types.HISTOGRAM:
            return self.generate_histogram(*args, **kwargs)
        else:
            return {}

    def generate_table(self, *args, **kwargs):
        """
        Generate a table from the data source
        """

        rows = self.attrs.get('rows', [])
        columns = self.attrs.get('columns', [])
        values = self.attrs.get('values', '')
        total_column = self.attrs.get('total_column', False)
        total_row = self.attrs.get('total_row', False)
        force_strings = self.attrs.get('force_strings', False)
        transpose = self.attrs.get('transpose', False)
        labels = self.source.get_labels()

        if isinstance(rows, str) and isinstance(columns, list):
            rows, columns = columns, rows
            transpose = True
        first_row_name = labels.get(columns, columns)

        raw_data = self.source.get_data(*args, **kwargs)
        num_columns = len(set(item[columns] for item in raw_data))
        if isinstance(rows, str):
            row_names = list(sorted(set(item[rows] for item in raw_data)))
        else:
            row_names = [labels.get(y, y) for y in rows]
        data = regroup_data(raw_data, x_axis=columns, y_axis=rows, y_value=values, labels=labels, default=0)

        # Now build table based on the reorganized data
        table_data: list[list[Any]] = [
            [key] + [item.get(key, 0) for item in data]
            for key in [first_row_name] + row_names
        ]

        if total_row:
            table_data.append(
                ['Total'] + [sum([row[i] for row in table_data[1:]]) for i in range(1, num_columns + 1)]
            )

        if total_column:
            table_data[0].append('All')
            for row in table_data[1:]:
                row.append(sum(row[1:]))

        if force_strings:
            table_data = [
                [f'{item}' for item in row] for row in table_data
            ]

        if transpose:
            table_data = list(map(list, zip(*table_data)))

        return {
            'title': self.title,
            'kind': 'table',
            'data': table_data,
            'style': self.style,
            'header': "column row",
            'description': self.description,
            'notes': self.notes
        }

    def generate_bars(self, *args, **kwargs):
        """
        Generate a bar chart from the data source
        """

        labels = self.source.get_labels()
        vertical = self.attrs.get('vertical', True)
        x_axis = self.attrs.get('x_axis', '')
        y_axis = self.attrs.get('y_axis', [])
        stack = self.attrs.get('stack', [])
        y_value = self.attrs.get('y_value', '')
        colors = self.attrs.get('colors', {})
        color_field = self.attrs.get('color_field', None)
        line = self.attrs.get('line', None)
        line_limits = self.attrs.get('line_limits', None)
        aspect_ratio = self.attrs.get('aspect_ratio', None)
        wrap_x_labels = self.attrs.get('wrap_x_labels', False)
        x_culling = self.attrs.get('x_culling', 15)

        x_label = labels.get(x_axis, x_axis)
        raw_data = self.source.get_data(*args, **kwargs)
        if isinstance(y_axis, str):
            y_labels = list(sorted(set(item[y_axis] for item in raw_data)))
            y_stack = [y_labels for y in stack if y == y_axis]
        else:
            y_stack = [[labels.get(y, y) for y in group] for group in stack]

        data = regroup_data(raw_data, x_axis=x_axis, y_axis=y_axis, y_value=y_value, labels=labels)

        details = {'x-label': x_label}
        if line:
            details['line'] = line
        if line_limits:
            details['line-limits'] = line_limits
        if aspect_ratio:
            details['aspect-ratio'] = aspect_ratio
        if y_stack:
            details['stack'] = y_stack
        if color_field:
            details['color-by'] = labels.get(color_field)
        if colors:
            details['colors'] = colors
        if x_culling:
            details['x-culling'] = x_culling
        if wrap_x_labels:
            details['wrap-x-labels'] = wrap_x_labels

        details['data'] = data
        return {
            'title': self.title,
            'description': self.description,
            'kind': 'columnchart' if vertical else "barchart",
            'style': self.style,
            'data': details,
            'notes': self.notes
        }

    def generate_list(self, *args, **kwargs):
        """
        Generate a list from the data source
        """
        columns = self.attrs.get('columns', [])
        limit = self.attrs.get('limit', None)
        data = self.source.get_data(*args, **kwargs)
        labels = self.source.get_labels()

        if limit:
            data = data[:limit]

        table_data = [
             [labels.get(field, field) for field in columns]
         ] + [
             [item.get(field, '') for field in columns]
             for item in data
         ]

        return {
            'title': self.title,
            'kind': 'table',
            'data': table_data,
            'style': self.style,
            'header': "row",
            'description': self.description,
            'notes': self.notes
        }

    def generate_plot(self, *args, **kwargs):
        """
        Generate a XY plot from the data source
        """
        labels = self.source.get_labels()

        x_axis = self.attrs.get('x_axis', '')
        y_axis = self.attrs.get('y_axis', [])
        y1_label = self.attrs.get('y1_label', '')
        y2_label = self.attrs.get('y2_label', '')
        scatter = self.attrs.get('scatter', False)
        aspect_ratio = self.attrs.get('aspect_ratio', None)
        colors = self.attrs.get('colors', {})
        tick_precision = self.attrs.get('tick_precision', 0)

        x_label = labels.get(x_axis, x_axis)
        y_groups = [[labels.get(y, y) for y in group] for group in y_axis]
        raw_data = self.source.get_data(*args, **kwargs)
        y_fields = [y for group in y_axis for y in group]

        data = regroup_data(raw_data, x_axis=x_axis, y_axis=y_fields, labels=labels)
        details = {
            'x-label': x_label,
            'aspect-ratio': aspect_ratio,
            'colors': colors,
            'x-tick-precision': tick_precision,
            'x': [x_label] + [item[x_label] for item in data]
        }

        y_labels = {
            'y1': y1_label,
            'y2': y2_label
        }
        for i, group in enumerate(y_groups):
            details[f'y{i + 1}-label'] = y_labels.get(f'y{i + 1}', group)
            details[f'y{i + 1}'] = [
                [group_name] + [item.get(group_name, 0) for item in data]
                for group_name in group
            ]

        return {
            'title': self.title,
            'description': self.description,
            'kind': 'scatterplot' if scatter else 'lineplot',
            'style': self.style,
            'data': details,
            'notes': self.notes
        }

    def generate_pie(self, *args, **kwargs):
        """
        Generate a pie chart from the data source
        """

        colors = self.attrs.get('colors', {})
        value_field = self.attrs.get('value_field', '')
        label_field = self.attrs.get('label_field', '')

        raw_data = self.source.get_data(*args, **kwargs)
        details = {}
        if colors:
            details['colors'] = colors
        details['data'] = [
            {
                'label': item.get(label_field),
                'value': item.get(value_field)
            } for item in raw_data
        ]
        return {
            'title': self.title,
            'description': self.description,
            'kind': 'pie',
            'style': self.style,
            'data': details,
            'notes': self.notes
        }

    def generate_histogram(self, *args, **kwargs):
        """
        Generate a histogram from the data source
        """

        bins = self.attrs.get('bins', None)
        value_field = self.attrs.get('value_field', '')

        raw_data = self.source.get_data(*args, **kwargs)
        labels = self.source.get_labels()
        values = [float(item.get(value_field)) for item in raw_data if item.get(value_field) is not None]
        histo = utils.get_histogram_points(values, bins=bins)
        return {
            'title': self.title,
            'description': self.description,
            'kind': 'histogram',
            'style': self.style,
            'data': {
                'x-label': labels.get(value_field, value_field.title()),
                'data': histo
            },
            'notes': self.notes
        }

