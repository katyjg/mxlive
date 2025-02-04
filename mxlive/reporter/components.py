from __future__ import annotations

import abc

from typing import Any, Literal

from mxlive.reporter.sources import DataSource, regroup_data


class Component(abc.ABC):
    title: str = ""
    description: str = ""
    notes: list[str] = []
    style: str = ""
    kind: Literal["barchart", "columnchart", "lineplot", "table", "histogram", "pie", "scatterplot", "timeline"]
    sources: tuple[DataSource] = ()
    labels: dict            # Field labels

    def __init__(self, **kwargs):
        self.__dict__.update(kwargs)
        assert len(self.sources) > 0, f"{self.__class__.__name__} must have a data source."
        self.labels = {}
        for source in self.sources:
            self.labels.update(source.get_labels())

    def get_data(self, *args, **kwargs) -> list[dict]:
        """
        Prepare data for component generation
        """
        data = []
        for source in self.sources:
            data.extend(source.generate(*args, **kwargs))
        return data

    @abc.abstractmethod
    def generate(self, *args, **kwargs) -> dict:
        """
        Generate component from a list of dictionaries
        """
        ...


class Table(Component):

    columns: list[str] | str = ""   # Name of the column field, must be present in every item
    rows: list[str] | str = []      # List of row field names or a single field name to group by
    values: str | callable = ""     # Field name for values or a function which takes
    total_column: bool = False      # Include a total column
    total_row: bool = False         # Include a total row
    force_strings: bool = False     # Force all cells to be strings
    transpose: bool = False         # Transpose the table so rows become columns

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        assert not all(
            (isinstance(self.columns, list), isinstance(self.rows, list))
        ), "Only one of `rows` or `columns` can be a list."
        if isinstance(self.rows, str) and isinstance(self.columns, list):
            self.rows, self.columns = self.columns, self.rows
            self.transpose = True
        self.row_names = []
        self.num_columns = 0
        self.first_row_name = self.labels.get(self.columns, self.columns)

    def get_data(self, *args, **kwargs) -> list[dict]:
        """
        Prepare data for table generation
        """
        data = super().get_data(*args, **kwargs)

        self.num_columns = len(set(item[self.columns] for item in data))
        if isinstance(self.rows, str):
            self.row_names = list(sorted(set(item[self.rows] for item in data)))
        else:
            self.row_names = [self.labels.get(y, y) for y in self.rows]

        return regroup_data(
            data, x_axis=self.columns, y_axis=self.rows, y_value=self.values, labels=self.labels, default=0
        )

    def generate(self, *args, **kwargs) -> dict:
        """
        Generate table from a list of dictionaries
        """
        data = self.get_data(*args, **kwargs)

        # Now build table based on the reorganized data
        table_data: list[list[Any]] = [
            [key] + [item.get(key, 0) for item in data]
            for key in [self.first_row_name] + self.row_names
        ]

        if self.total_row:
            table_data.append(
                ['Total'] + [sum([row[i] for row in table_data[1:]]) for i in range(1, self.num_columns + 1)]
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
            'style': self.style,
            'header': "column row",
            'description': self.description,
            'notes': '\n'.join(self.notes)
        }


class List(Component):

    columns: list[str] = []  # List of field names to display
    limit: int = None       # Maximum number of items to display

    def generate(self, *args, **kwargs) -> dict:
        """
        Generate list from a list of dictionaries
        """
        data = self.get_data(*args, **kwargs)
        if self.limit:
            data = data[:self.limit]

        # Now build table based on the reorganized data
        table_data = [
            [self.labels.get(field, field) for field in self.columns]
        ] + [
            [item.get(field, '') for field in self.columns]
            for item in data
        ]

        info = {
            'title': self.title,
            'kind': 'table',
            'data': table_data,
            'style': self.style,
            'header': "row",
            'description': self.description,
            'notes': '\n'.join(self.notes)
        }
        return info


class Bars(Component):
    vertical: bool = True                   # Column or bar chart
    x_axis: str = ""                        # Name of the x-axis field
    y_axis: list[str] | str = []            # List of y-axis field names or a single field name to group by
    stack:  list[list[str] | str] = []      # List of lists of y-axis field names, or a single field name to stack by
    y_value: str = ""                       # Field name for y-axis if a single field is used for y-axis
    colors: dict = {}                       # Color mapping for y-axis fields
    color_field: str = None                 # Field name to use for color mapping
    line: str = None                        # Line field name if any
    line_limits: tuple[int, int] = None     # Line limits if any
    aspect_ratio: float = None              # Aspect ratio of the chart
    x_culling: int = None                   # Maximum number of x-axis labels to display
    wrap_x_labels: bool = True             # Whether to wrap x-axis labels

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.x_label = self.labels.get(self.x_axis, self.x_axis)
        self.y_labels = []
        self.y_stack = []

    def get_data(self, *args, **kwargs):
        """
        Prepare data for chart generation
        """
        data = super().get_data(*args, **kwargs)

        if isinstance(self.y_axis, str):
            self.y_labels = list(sorted(set(item[self.y_axis] for item in data)))
            self.y_stack = [self.y_labels for y in self.stack if y == self.y_axis]
        else:
            self.y_labels = [self.labels.get(y, y) for y in self.y_axis]
            self.y_stack = [[self.labels.get(y, y) for y in group] for group in self.stack]

        return regroup_data(data, x_axis=self.x_axis, y_axis=self.y_axis, y_value=self.y_value, labels=self.labels)

    def generate(self, *args, **kwargs) -> dict:
        """
        Generate chart from a list of dictionaries
        """
        details = {'x-label': self.x_label}
        if self.line:
            details['line'] = self.line
        if self.line_limits:
            details['line-limits'] = self.line_limits
        if self.aspect_ratio:
            details['aspect-ratio'] = self.aspect_ratio
        if self.y_stack:
            details['stack'] = self.y_stack
        if self.color_field:
            details['color-by'] = self.labels.get(self.color_field)
        if self.colors:
            details['colors'] = self.colors
        if self.x_culling:
            details['x-culling'] = self.x_culling
        if self.wrap_x_labels:
            details['wrap-x-labels'] = self.wrap_x_labels

        details['data'] = self.get_data(*args, **kwargs)
        return {
            'title': self.title,
            'description': self.description,
            'kind': 'columnchart' if self.vertical else "barchart",
            'style': self.style,
            'data': details,
            'notes': '\n'.join(self.notes)
        }


class XYPlot(Component):
    scatter: bool = False                       # Scatter plot otherwise line plot
    x_axis: str = ""                            # Name of the x-axis field
    y_axis: tuple[list[str], list[str]] = ()    # List of y-axis field names or a single field name to group by
    y1_label: str = None                        # List of y-axis labels
    y2_label: str = None                        # List of y-axis labels
    tick_precision: int = None                  # Precision for y-axis ticks
    y_value: str = ""                       # Field name for y-axis if a single field is used for y-axis
    colors: dict = {}                       # Color mapping for y-axis fields
    aspect_ratio: float = None              # Aspect ratio of the chart

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.x_label = self.labels.get(self.x_axis, self.x_axis)
        self.y_groups = [[self.labels.get(y, y) for y in group] for group in self.y_axis]

    def get_data(self, *args, **kwargs):
        """
        Prepare data for chart generation
        """
        data = super().get_data(*args, **kwargs)
        y_fields = [y for group in self.y_axis for y in group]
        return regroup_data(data, x_axis=self.x_axis, y_axis=y_fields, labels=self.labels)

    def generate(self, *args, **kwargs) -> dict:
        """
        Generate chart from a list of dictionaries
        """
        data = self.get_data(*args, **kwargs)
        details = {
            'x-label': self.x_label,
            'aspect-ratio': self.aspect_ratio,
            'colors': self.colors,
            'x-tick-precision': self.tick_precision,
            'x': [self.x_label] + [item[self.x_label] for item in data]
        }

        y_labels = {
            'y1': self.y1_label,
            'y2': self.y2_label
        }
        for i, group in enumerate(self.y_groups):
            details[f'y{i + 1}-label'] = y_labels.get(f'y{i + 1}', group)
            details[f'y{i + 1}'] = [
                [group_name] + [item.get(group_name, 0) for item in data]
                for group_name in group
            ]

        return {
            'title': self.title,
            'description': self.description,
            'kind': 'scatterplot' if self.scatter else 'lineplot',
            'style': self.style,
            'data': details,
            'notes': '\n'.join(self.notes)
        }


class Histogram(Component):
    values: str = ""        # Field name for values
    bins: Any = None        # Number of bins or method to calculate bins

    @staticmethod
    def get_histogram_points(data: list[float], bins: Any = None) -> list[dict]:
        """
        Generate histogram points
        """
        import numpy as np
        bins = 'doane' if bins is None else int(bins)
        hist, edges = np.histogram(data, bins=bins)
        centers = edges[:-1] + np.diff(edges) / 2
        return [{'x': x, 'y': y} for x, y in zip(centers, hist)]

    def generate(self, *args, **kwargs) -> dict:
        """
        Generate histogram from a list of dictionaries
        """
        data = self.get_data(*args, **kwargs)
        histo = self.get_histogram_points(
            [float(datum[self.values]) for datum in data if datum.get(self.values) is not None],
            bins=self.bins
        )
        return {
            'title': self.title,
            'description': self.description,
            'kind': 'histogram',
            'style': self.style,
            'data': {
                'x-label': self.labels.get(self.values, self.values.title()),
                'data': histo
            },
            'notes': '\n'.join(self.notes)
        }


class Pie(Component):
    colors: dict | str = None              # Color mapping for y-axis fields
    value_field: str = ""                   # Field to extract values
    label_field: str = ""

    def generate(self, *args, **kwargs) -> dict:
        """
        Generate chart from a list of dictionaries
        """
        data = self.get_data(*args, **kwargs)
        details = {}
        if self.colors:
            details['colors'] = self.colors
        details['data'] = [
            {'label': item.get(self.label_field), 'value': item.get(self.value_field)}
            for item in data
        ]

        return {
            'title': self.title,
            'description': self.description,
            'kind': 'pie',
            'style': self.style,
            'data': details,
            'notes': '\n'.join(self.notes)
        }