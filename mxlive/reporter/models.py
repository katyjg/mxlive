from collections import defaultdict

from IPython.lib.pretty import Printable
from django.apps import apps
from django.db import models
from django.db.models import Case, When, Value, CharField, QuerySet
from django.db.models.functions import Round, Abs, Sign
from django.utils.text import gettext_lazy as _
from model_utils.models import TimeStampedModel
from typing import Any

from . import utils
from .utils import regroup_data

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


class DataModel(TimeStampedModel):
    """
    Model definition for DataModel. This model is used to define allowed data models
    and corresponding fields for the reporter app.
    """
    name = models.CharField(max_length=150)
    fields = models.JSONField(default=list, blank=True, null=True)

    def __str__(self):
        return self.name


class DataSource(TimeStampedModel):
    name = models.CharField(max_length=50)
    filters = models.JSONField(default=dict, blank=True)
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

        # Add aggregations and handle grouping
        group_fields: list = (
            group_by or list(self.fields.filter(grouped=True).values_list('name', flat=True).distinct())
        )
        aggregations = {}
        if group_fields:
            aggregations = {
                field.name: field.get_expression()
                for field in self.fields.filter(model__name=model_name, kind=DataField.FieldType.AGGREGATION)
            }

        if annotations and not group_fields:
            queryset = queryset.annotate(**annotations)
        elif annotations and group_fields:
            queryset = queryset.annotate(**annotations).values(*group_fields).annotate(**aggregations)
        elif group_fields:
            queryset.values(*group_fields).annotate(**aggregations)

        # Apply sorting
        order_fields = self.fields.annotate(
            order_by=Abs('ordering')
        ).filter(ordering__isnull=False).order_by('order_by').values_list(Sign('ordering'), 'name', )
        order_by: list = order_by or [f'-{name}' if sign < 0 else name for sign, name in order_fields]
        if order_by:
            queryset = queryset.order_by(*order_by)

        # Apply limit
        if self.limit:
            queryset = queryset[:self.limit]

        return queryset

    @utils.cached_model_method(duration=1)
    def get_data(self, filters=None, group_by=None, order_by=None) -> list[dict]:
        """
        Generate data for this data source
        :param filters: dynamic filters
        :param group_by: group by fields
        :param order_by: order by fields

        """

        data = []
        model_names = set(self.fields.values_list('model__name', flat=True))
        for model_name in model_names:
            queryset = self.get_queryset(model_name, filters=filters, group_by=group_by, order_by=order_by)
            field_names = [field.name for field in self.fields.filter(model__name=model_name).all()]
            data.extend(list(queryset.values(*field_names)))

        return data


class DataField(TimeStampedModel):
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
    position = models.IntegerField(default=0)
    grouped = models.BooleanField(default=False)
    ordering = models.IntegerField(null=True, blank=True)
    filterable = models.BooleanField(default=False)
    source = models.ForeignKey(DataSource, on_delete=models.CASCADE, related_name='fields')

    class Meta:
        unique_together = ['name', 'source', 'model']
        ordering = ['source', 'position', 'pk']

    def __str__(self):
        return self.label

    def get_expression(self) -> models.Expression:
        parser = utils.ExpressionParser()
        if self.expression:
            db_expression = parser.parse(self.expression)
            if self.precision is not None:
                db_expression = Round(db_expression, self.precision)
            return db_expression


class Report(TimeStampedModel):
    slug = models.SlugField(max_length=128, unique=True)
    title = models.TextField()
    description = models.TextField(default='', blank=True)
    style = models.CharField(max_length=100, default='', blank=True)
    notes = models.TextField(default='', blank=True)

    def __str__(self):
        return self.title


class Entry(TimeStampedModel):
    class Types(models.TextChoices):
        BARS = 'bars', _('Bar Chart')
        TABLE = 'table', _('Table')
        LIST = 'list', _('List')
        PLOT = 'plot', _('XY Plot')
        PIE = 'pie', _('Pie Chart')
        HISTOGRAM = 'histogram', _('Histogram')
        TIMELINE = 'timeline', _('Timeline')
        TEXT = 'text', _('Rich Text')

    class Widths(models.TextChoices):
        QUARTER = "col-md-3", _("One Quarter")
        THIRD = "col-md-4", _("One Third")
        HALF = "col-md-6", _("Half")
        TWO_THIRDS = "col-md-8", _("Two Thirds")
        THREE_QUARTERS = "col-md-9", _("Three Quarters")
        FULL = "col-md-12", _("Full Width")

    title = models.TextField(default='', blank=True)
    description = models.TextField(default='', blank=True)
    notes = models.TextField(default='', blank=True)
    style = models.CharField(_("Width"), max_length=100, choices=Widths.choices, default=Widths.FULL, blank=True)
    kind = models.CharField(_("Type"), max_length=50, choices=Types.choices, default=Types.TABLE)
    source = models.ForeignKey(DataSource, on_delete=models.CASCADE, related_name='entries', null=True, blank=True)
    report = models.ForeignKey(Report, on_delete=models.CASCADE, related_name='entries')
    position = models.IntegerField(default=0)
    attrs = models.JSONField(default=dict, blank=True)

    class Meta:
        verbose_name_plural = 'Entries'
        ordering = ['report', 'position']

    def __str__(self):
        return self.title

    def generate(self, *args, **kwargs):
        if not self.attrs:
            info = {}
        elif self.kind == self.Types.BARS:
            info = self.generate_bars(*args, **kwargs)
        elif self.kind == self.Types.TABLE:
            info = self.generate_table(*args, **kwargs)
        elif self.kind == self.Types.LIST:
            info = self.generate_list(*args, **kwargs)
        elif self.kind == self.Types.PLOT:
            info = self.generate_plot(*args, **kwargs)
        elif self.kind == self.Types.PIE:
            info = self.generate_pie(*args, **kwargs)
        elif self.kind == self.Types.HISTOGRAM:
            info = self.generate_histogram(*args, **kwargs)
        elif self.kind == self.Types.TIMELINE:
            info = self.generate_timeline(*args, **kwargs)
        elif self.kind == self.Types.TEXT:
            info = self.generate_text(*args, **kwargs)
        else:
            info = {}

        return info

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

        if not columns or not rows:
            return {}

        if isinstance(rows, str) and isinstance(columns, list):
            rows, columns = columns, rows
            transpose = True
        first_row_name = labels.get(columns, columns)

        raw_data = self.source.get_data(*args, **kwargs)
        num_columns = len(set(item[columns] for item in raw_data))
        if len(rows) == 1 and values:
            rows = rows[0]
            row_names = list(dict.fromkeys(item[rows] for item in raw_data))
        else:
            row_names = [labels.get(y, y) for y in rows]
        data = regroup_data(
            raw_data, x_axis=columns, y_axis=rows, y_value=values, labels=labels, default=0, sort=columns
        )

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
        sort_by = self.attrs.get('sort_by', None)
        sort_desc = self.attrs.get('sort_desc', False)
        stack = self.attrs.get('stack', [])
        y_value = self.attrs.get('y_value', '')
        colors = self.attrs.get('colors', 'Live16')
        color_field = self.attrs.get('color_field', None)
        line = self.attrs.get('line', None)
        line_limits = self.attrs.get('line_limits', None)
        aspect_ratio = self.attrs.get('aspect_ratio', None)
        wrap_x_labels = self.attrs.get('wrap_x_labels', False)
        x_culling = self.attrs.get('x_culling', 15)
        limit = self.attrs.get('limit', None)

        if not x_axis or not y_axis:
            return {}

        x_label = labels.get(x_axis, x_axis)
        raw_data = self.source.get_data(*args, **kwargs)
        if len(y_axis) == 1 and y_value:
            y_axis = y_axis[0]
            y_labels = list(dict.fromkeys(item[y_axis] for item in raw_data))
            y_stack = [y_labels for group in stack for y in group if y == y_axis]
        else:
            y_stack = [[labels.get(y, y) for y in group] for group in stack]

        data = regroup_data(
            raw_data, x_axis=x_axis, y_axis=y_axis, y_value=y_value, labels=labels,
            sort=sort_by, sort_desc=sort_desc, default=0,
        )

        info = {
            'title': self.title,
            'description': self.description,
            'kind': 'columnchart' if vertical else "barchart",
            'y-ticks': None if vertical else 5,
            'style': self.style,
            'notes': self.notes,
            'x-label': x_label,
        }

        if line:
            info['line'] = line
        if line_limits:
            info['line-limits'] = line_limits
        if aspect_ratio:
            info['aspect-ratio'] = aspect_ratio
        if y_stack:
            info['stack'] = y_stack
        if color_field:
            color_key = labels.get(color_field)
            info['color-by'] = color_key
            color_keys = list(dict.fromkeys([item.get(color_field) for item in raw_data if color_field in item]))
            info['colors'] = utils.map_colors(color_keys, colors)
        elif colors:
            info['colors'] = colors
        if x_culling:
            info['x-culling'] = x_culling
        if wrap_x_labels:
            info['wrap-x-labels'] = wrap_x_labels

        if limit:
            data = data[limit:] if limit < 0 else data[:limit]
        info['data'] = data
        return info

    def generate_list(self, *args, **kwargs):
        """
        Generate a list from the data source
        """
        columns = self.attrs.get('columns', [])
        order_by = self.attrs.get('order_by', None)
        limit = self.attrs.get('limit', None)

        if not columns:
            return {}

        data = self.source.get_data(*args, **kwargs)
        labels = self.source.get_labels()

        if order_by:
            sort_key, reverse = (order_by[1:], True) if order_by.startswith('-') else (order_by, False)
            data = list(sorted(data, key=lambda x: x.get(sort_key, 0), reverse=reverse))

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
            'style': f"{self.style} first-col-left",
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
        colors = self.attrs.get('colors', 'Live16')
        tick_precision = self.attrs.get('tick_precision', 0)

        if not x_axis or not y_axis:
            return {}

        x_label = labels.get(x_axis, x_axis)
        y_groups = [[labels.get(y, y) for y in group] for group in y_axis]
        raw_data = self.source.get_data(*args, **kwargs)

        y_fields = [y for group in y_axis for y in group]

        data = regroup_data(raw_data, x_axis=x_axis, y_axis=y_fields, labels=labels)

        data.sort(key=lambda x: x[x_label])

        report_data = [
            [x_label] + [item[x_label] for item in data]
        ]
        series = {}
        for i, group in enumerate(y_groups):
            series[i] = group
            report_data.extend([
                [group_name] + [item.get(group_name, 0) for item in data]
                for group_name in group
            ])

        return {
            'title': self.title,
            'description': self.description,
            'kind': 'scatterplot' if scatter else 'lineplot',
            'style': self.style,
            'x-label': x_label,
            'aspect-ratio': aspect_ratio,
            'colors': colors,
            'x-tick-precision': tick_precision,
            'x': x_label,
            'y1': series.get(0, []),
            'y2': series.get(1, []),
            'y1-label': y1_label,
            'y2-label': y2_label,
            'data': report_data,
            'notes': self.notes
        }

    def generate_pie(self, *args, **kwargs):
        """
        Generate a pie chart from the data source
        """

        colors = self.attrs.get('colors', None)
        value_field = self.attrs.get('value', '')
        label_field = self.attrs.get('label', '')

        raw_data = self.source.get_data(*args, **kwargs)
        data = defaultdict(int)
        for item in raw_data:
            data[item.get(label_field)] += item.get(value_field, 0)

        return {
            'title': self.title,
            'description': self.description,
            'kind': 'pie',
            'style': self.style,
            'colors': colors,
            'data': [{'label': label, 'value': value} for label, value in data.items()],
            'notes': self.notes
        }

    def generate_histogram(self, *args, **kwargs):
        """
        Generate a histogram from the data source
        """

        bins = self.attrs.get('bins', None)
        value_field = self.attrs.get('value_field', '')
        colors = self.attrs.get('colors', None)
        if not value_field:
            return {}

        raw_data = self.source.get_data(*args, **kwargs)
        labels = self.source.get_labels()
        values = [float(item.get(value_field)) for item in raw_data if item.get(value_field) is not None]

        return {
            'title': self.title,
            'description': self.description,
            'kind': 'histogram',
            'style': self.style,
            'colors': colors,
            'x-label': labels.get(value_field, value_field.title()),
            'data': utils.get_histogram_points(values, bins=bins),
            'notes': self.notes
        }

    def generate_timeline(self, *args, **kwargs):
        """
        Generate a timeline from the data source
        """

        type_field = self.attrs.get('type_field', '')
        start_field = self.attrs.get('start_field', [])
        end_field = self.attrs.get('end_field', '')
        label_field = self.attrs.get('label_field', '')
        colors = self.attrs.get('colors', None)

        if not type_field or not start_field or not end_field:
            return {}

        min_max = utils.MinMax()
        raw_data = self.source.get_data(*args, **kwargs)
        data = [
            {
                'type': item.get(type_field, ''),
                'start': min_max.check(utils.epoch(item[start_field])),
                'end': min_max.check(utils.epoch(item[end_field])),
                'label': item.get(label_field, '')
            } for item in raw_data if start_field in item and end_field in item
        ]

        min_time = self.attrs.get('min_time', min_max.min)
        max_time = self.attrs.get('max_time', min_max.max)

        return {
            'title': self.title,
            'description': self.description,
            'kind': 'timeline',
            'colors': colors,
            'start': min_time,
            'end': max_time,
            'style': self.style,
            'notes': self.notes,
            'data': data
        }

    def generate_text(self, *args, **kwargs):
        """
        Generate a rich text entry
        """
        rich_text = self.attrs.get('rich_text', '')
        return {
            'title': self.title,
            'description': self.description,
            'kind': 'richtext',
            'style': self.style,
            'text': rich_text,
            'notes': self.notes
        }
