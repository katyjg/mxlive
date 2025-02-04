from __future__ import annotations


from typing import Any
from django.apps import apps
from django.db.models import QuerySet


class DataField:
    model: None

    def __init__(self, name, source=None, label=None, default=None):
        self.name = name
        self.source = source
        self.label = label or name
        self.default = default


class Annotation:
    def __init__(self, expression):
        self.expression = expression


class Aggregation:
    def __init__(self, expression):
        self.expression = expression


class DataSource:
    model = None
    fields = []
    filters = {}
    group_by = []

    groupable = []  # Define which fields can be used for user-defined grouping
    filterable = {}  # Define dynamic filters allowed for this report
    sortable = []  # Define dynamic sorting allowed for this report
    limit = None    # Limit the number of results
    order_by = []   # Default sorting order

    @classmethod
    def get_labels(cls) -> dict[str, str]:
        """
        Get field labels for this data source
        """
        return {field.name: field.label for field in cls.fields}

    @classmethod
    def get_queryset(cls, filters: dict = None, group_by: list[str] = None, order_by: list[str] = None) -> QuerySet:
        """
        Get the queryset for this data source
        :param filters: dynamic filters
        :param group_by: group by fields
        :param order_by: order by fields
        """
        model = apps.get_model(cls.model) if isinstance(cls.model, str) else cls.model
        queryset = model.objects.all()

        # Apply static filters
        if cls.filters:
            queryset = queryset.filter(**cls.filters)

        # Apply dynamic filters
        if filters:
            queryset = queryset.filter(**filters)

        # Add annotations
        annotations = {
            field.name: field.source.expression
            for field in cls.fields
            if isinstance(field.source, Annotation)
        }
        if annotations:
            queryset = queryset.annotate(**annotations)

        # Add aggregations and handle grouping
        group_fields = group_by or cls.group_by
        if group_fields:
            aggregations = {
                field.name: field.source.expression
                for field in cls.fields
                if isinstance(field.source, Aggregation)
            }
            queryset = queryset.values(*group_fields).annotate(**aggregations)

        # Apply sorting
        order_by = order_by or cls.order_by
        if order_by:
            queryset = queryset.order_by(*order_by)

        # Apply limit
        if cls.limit:
            queryset = queryset[:cls.limit]

        return queryset

    @classmethod
    def generate(cls, filters: dict = None, group_by: list[str] = None, order_by: list[str] = None) -> list[dict]:
        """
        Generate data for this data source
        :param filters: dynamic filters
        :param group_by: group by fields
        :param order_by: order by fields

        """
        queryset = cls.get_queryset(filters, group_by, order_by)
        data = queryset.values(*(field.name for field in cls.fields))
        return list(data)

    @classmethod
    def validate_filters(cls, request_params) -> dict:
        """
        Validate dynamic filters from request parameters
        """
        valid_filters = {}
        for key, filter_type in cls.filterable.items():
            if key in request_params:
                try:
                    value = request_params.get(key)
                    if filter_type == int:
                        valid_filters[key] = int(value)
                    elif filter_type == float:
                        valid_filters[key] = float(value)
                    elif filter_type == str:
                        valid_filters[key] = value
                except ValueError:
                    # Ignore invalid values
                    pass
        return valid_filters

    @classmethod
    def validate_grouping(cls, request_params) -> list[str]:
        """
        Validate grouping fields from request parameters
        """
        group_by = request_params.getlist("group_by")
        valid_grouping = [field for field in group_by if field in cls.groupable]
        return valid_grouping

    @classmethod
    def validate_sorting(cls, request_params) -> list[str]:
        """
        Validate sorting fields from request parameters
        """
        sort_fields = request_params.getlist("sort_by")
        valid_sorting = [field for field in sort_fields if field.lstrip("-") in cls.sortable]
        return valid_sorting


def regroup_data(
        data: list[dict],
        x_axis: str = '',
        y_axis: list[str] | str = '',
        y_value: str = '',
        labels: dict = None,
        default: Any = None
) -> list[dict]:
    """
    Regroup data into neat key-value pairs translating keys to labels according to labels dictionary

    :param data: list of dictionaries
    :param x_axis: Name of the x-axis field
    :param y_axis: List of y-axis field names or a single field name to group by
    :param y_value: Field name for y-axis if a single field is used for y-axis
    :param labels: Field labels
    :param default: Default value for missing fields
    """

    labels = labels or {}
    x_label = labels.get(x_axis, x_axis)
    all_x_values = set(item[x_axis] for item in data)
    x_values = sorted(filter(None, all_x_values))
    raw_data = {value: {x_label: value} for value in x_values}

    # reorganize data into dictionary of dictionaries with appropriate fields
    for item in data:
        x_value = item[x_axis]
        if x_value not in x_values:
            continue
        if isinstance(y_axis, str):
            raw_data[x_value][item[y_axis]] = item.get(y_value, 0)
        elif isinstance(y_axis, list):
            for y_field in y_axis:
                y_label = labels.get(y_field, y_field)
                if y_field in item:
                    raw_data[x_value][y_label] = item.get(y_field, 0)
                elif y_label not in raw_data[x_value]:
                    raw_data[x_value][y_label] = default
    return list(raw_data.values())


