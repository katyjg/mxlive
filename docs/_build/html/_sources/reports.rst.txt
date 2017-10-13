=======
Reports
=======

.. contents:: Table of contents
    :depth: 1
    :local:

Analysis Reports are built dynamically based on information in the `details` JSONField, which is stored as a list of dictionaries.

Each dictionary in the list is treated as a Section in the report, with optional parameters. Sections are displayed in
order, and can be provided with a title, description (to go below the title), a list of dictionaries containing the
content (tables and/or plots) to display in the section, and notes to go after the content.

Section Options
^^^^^^^^^^^^^^^

.. code-block:: html

    'title': '',
    'description': '',
    'notes': '',
    'style': '',
    'content': []

**content**: list of dictionaries, each one describing a table or plot to display

**style**: CSS class to be applied to the section

Content Options
^^^^^^^^^^^^^^^

.. code-block:: html

    'title': '',
    'description': '',
    'notes': '',
    'style': '',
    'kind': ,
    'header': 'row',
    'annotations': [],
    'data': {} (for plots) or [] (for tables)

**kind**: Supported types are 'scatterplot', 'lineplot', or 'table'

**header** (tables): Used if kind='table'. If 'row', the first list in the list of data contains the headers; if 'column', the first item in each list is a header.

**annotations** (plots): list of dictionaries used to draw vertical lines and text on a plot.

**data** (tables): list of lists to arrange in rows

**data** (plots): dictionary containing the data to display

**style**: CSS class to be applied to the content

Annotation Options (Plots)
^^^^^^^^^^^^^^^^^^^^^^^^^^

.. code-block:: html

    'x': ,
    'y-start': ,
    'y-end': ,
    'label': ,
    'color': ,
    'display': True


Data Options (Plots)
^^^^^^^^^^^^^^^^^^^^

.. code-block:: html

    'x': [],
    'y1': [],
    'y2': [],
    'x-label': '',
    'y1-label': '',
    'y2-label': '',
    'x-scale': 'linear'

**x**: List of x-axis data, with a label in the first entry. If **x-label** is not specified, this will be used to label the x-axis.

**y1**: List of lists of data to plot on the left y-axis. Each list should be the same length as the list defined in `x`. The first entry in each list is a label for the data.

**y2**: List of lists of data to plot on the right y-axis. Each list should be the same length as the list defined in `x`. The first entry in each list is a label for the data.

**x-scale**: Supported scaling includes 'linear', 'pow', 'log', 'identity', 'time', and 'inv-square' (power with exponent -0.5)


Model
^^^^^

.. automodule:: lims.models
    :members: AnalysisReport
