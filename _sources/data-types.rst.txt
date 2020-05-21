New Data Types
==============
Data types included by default with MxLIVE are **MX Screening**, **MX Dataset**, **XRD Dataset**, **Rastering**,
**XAS Dataset**, **XRF Dataset**, and **MAD Scan**.

Creating a new data type is a three-pronged process.

1. Create a new Data Type
-------------------------
Go to the Django administration site and create a new Data Type. The **Name** and **Description** are used for display,
**Acronym** is the ``type`` referenced when :ref:`uploading new datasets<adding-data-reports>` from the beamline,
**Template** is the HTML template file in the MxLIVE project that should be used to display datasets of this data type,
and **Metadata** is a list of fields that are expected to be uploaded along with new datasets of this data type.

.. image:: images/data-type.png
   :align: center
   :alt: Data Type

2. Create the HTML Template
---------------------------
For consistency, template files for new data types should be placed in `mxlive/lims/templates/users/entries/`, and can
be referenced by the file path under `templates/`. At a minimum, the template should extend `users/entries/data.html`,
and define a ``data_content`` block.

.. code-block:: html

    {% extends "users/entries/data.html" %}

    {% block data_content %}{% endblock %}      # Main area for data viewing

.. image:: images/data-content.png
   :align: center
   :alt: Data Content


Using the Report Format
^^^^^^^^^^^^^^^^^^^^^^^
To use the :ref:`MxLIVE report format<formatting-reports>`, include the following assets in the ``modal_assets`` block,
and add an empty element with an ``id`` that can be referenced in the ``modal_scripts`` block:

.. code-block:: html

    {% block data_content %}
        <div class="row">
            <div class="col-12 pr-0">
                <div id="data-display" class="w-100 p-0"></div>
                <script>
                    // create variables for reports
                    var report{{ data.pk }}={{ mad.report | jsonify }};
                </script>
            </div>
        </div>
    {% endblock %}

    {% block modal_assets %}
        <link href="{% static "css/c3.min.css" %}" rel="stylesheet">
        <link href="{% static "css/reports.min.css" %}" rel="stylesheet">
        <script type="text/javascript" src="{% static "js/d3/d3.v5.min.js" %}"></script>
        <script type="text/javascript" src="{% static "js/d3/d3.legend.js" %}"></script>
        <script type="text/javascript" src="{% static 'js/d3/d3.timeline.min.js' %}"></script>
        <script type="text/javascript" src="{% static "js/misc/showdown.min.js" %}"></script>
        <script type="text/javascript" src="{% static "js/misc/c3.min.js" %}"></script>
        <script type="text/javascript" src="{% static "js/mxlive-reports.v2.min.js" %}"></script>
    {% endblock %}

    {% block modal_scripts %}
        <script type="text/javascript">
            $('#modal').on('shown.bs.modal', function () {
                $('#data-display').liveReport({
                    data: report{{ data.pk }}
                });
            });
        </script>
    {% endblock %}

You will also need to define a custom tag in `templatetags/data_server.py` to add your formatted report to the context,
in which you may need to request files from the data proxy to get all the information needed to build the report. Helper
functions already exist for fetching JSON or XDI data (``get_json_info`` and ``get_xdi_info``).

.. code-block:: python

    @register.simple_tag(takes_context=True)
    def sample_report(context):
        data = context['data']
        if not data.url:
            return {}

        report = {'details': [
            {
                'title': '',
                'style': "row",
                'content': [
                    {
                        ...
                    },
                ]
            },
        ]}

        return { 'report': report }