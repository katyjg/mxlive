from __future__ import annotations

from collections import defaultdict

from typing import Any

from django.db.models import QuerySet


class DataField:
    def __init__(self, name, source, label=None, default=None):
        self.name = name
        self.source = source
        self.label = label or name
        self.default = default


class Annotation:
    def __init__(self, name, expression):
        self.name = name
        self.expression = expression


class Aggregation:
    def __init__(self, name, expression):
        self.name = name
        self.expression = expression


class DataSource:
    model = None
    fields = []
    filters = {}
    group_by = []

    groupable = []  # Define which fields can be used for user-defined grouping
    filterable = {}  # Define dynamic filters allowed for this report
    sortable = []  # Define dynamic sorting allowed for this report

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
        queryset = cls.model.objects.all()

        # Apply static filters
        if cls.filters:
            queryset = queryset.filter(**cls.filters)

        # Apply dynamic filters
        if filters:
            queryset = queryset.filter(**filters)

        # Add annotations
        annotations = {
            field.source.name: field.source.expression
            for field in cls.fields
            if isinstance(field.source, Annotation)
        }
        if annotations:
            queryset = queryset.annotate(**annotations)

        # Add aggregations and handle grouping
        group_fields = group_by or cls.group_by
        if group_fields:
            aggregations = {
                field.source.name: field.source.expression
                for field in cls.fields
                if isinstance(field.source, Aggregation)
            }
            queryset = queryset.values(*group_fields).annotate(**aggregations)

        # Apply sorting
        if order_by:
            queryset = queryset.order_by(*order_by)

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


class Table:
    title: str = ""
    description: str = ""
    notes: list[str] = []
    style: str = ""

    source: DataSource = None

    labels: dict[str, str] = {}
    columns: list[str] | str = ""   # Name of the column field, must be present in every item
    rows: list[str] | str = []      # List of row field names or a single field name to group by
    values: str | callable = ""     # Field name for values or a function which takes
    total_column: bool = False      # Include a total column
    total_row: bool = False         # Include a total row
    force_strings: bool = False     # Force all cells to be strings
    transpose: bool = False         # Transpose the table so rows become columns

    def __init__(self, **kwargs):
        self.__dict__.update(kwargs)
        assert self.source is not None, "Table must have a data source."
        assert not all((isinstance(self.columns, list), isinstance(self.rows, list))), "Only one of `rows` or `columns` can be a list."
        if isinstance(self.rows, str) and isinstance(self.columns, list):
            self.rows, self.columns = self.columns, self.rows
            self.transpose = True

    def generate(self, *args, **kwargs) -> dict:
        """
        Generate table from a list of dictionaries
        """
        data = self.source.generate(*args, **kwargs)
        column_headers = sorted(set(item[self.columns] for item in data))
        first_row_name = self.labels.get(self.columns, self.columns)

        if isinstance(self.rows, str):
            row_names = [first_row_name] + list(sorted(set(item[self.rows] for item in data)))
        else:
            row_names = [first_row_name] + [self.labels.get(y, y) for y in self.rows]

        # reorganize data into dictionary of dictionaries with appropriate fields
        raw_data = {
            value: defaultdict(int)
            for value in column_headers
        }
        for value in column_headers:
            raw_data[value][first_row_name] = value

        for item in data:
            if isinstance(self.rows, str):
                raw_data[item[self.columns]][item[self.rows]] += item.get(self.values, 0)
            elif isinstance(self.rows, list):
                for x in self.rows:
                    raw_data[item[self.columns]][self.labels.get(x, x)] = item.get(x, 0)

        # Now build table based on the reorganized data
        table_data: list[list[Any]] = [
            [key] + [item.get(key, 0) for item in raw_data.values()]
            for key in row_names
        ]

        if self.total_row:
            table_data.append(
                ['Total'] + [sum([row[i] for row in table_data[1:]]) for i in range(1, len(column_headers))]
            )

        if self.total_column:
            table_data[0].append('All')
            for row in table_data[1:]:
                row.append(sum(row[1:]))

        if self.force_strings:
            table_data = [
                [f'{item}' for item in row] for row in table_data
            ]

        if self.transpose:
            table_data = list(map(list, zip(*table_data)))

        return {
            'title': self.title,
            'kind': 'table',
            'data': table_data,
            'style': 'col-12',
            'header': "column row",
            'description': self.description,
            'notes': '\n'.join(self.notes)
        }



