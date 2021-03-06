.. title:: MxLIVE - MX Laboratory Information Virtual Environment

MxLIVE (Macromolecular Crystallography Laboratory Virtual Environment) is a development platform and web application for
managing synchrotron visits from experiment planning and organisation to shipment tracking to data and analysis access.

Source code can be found at https://github.com/katyjg/mxlive.

MxLIVE relies on MxDC as a source of meta-data from data collection sessions on the beamline, and acts as a resource
from which MxDC can fetch sample information. While this close-coupling is tailored to MxDC, all connections are handled
through the use of APIs, so other data collection applications could also be modified to complement MxLIVE.

The beginnings of MxLIVE were at CMCF, a suite of beamlines at the Canadian Light Source dedicated to Macromolecular
Crystallography. For that reason, many features have been developed in an MX context, but can easily be extended to
:ref:`new sample container layouts<new-layouts>` and :ref:`new data types or techniques<new-data-types>` at any beamline.

.. note::
    An earlier version of MxLIVE is described in the following publication:

    * MxDC and MxLIVE: software for data acquisition, information management and remote access to macromolecular
      crystallography beamlines. M. Fodje, K. Janzen, R. Berg, G. Black, S. Labiuk, J. Gorin and P. Grochulski
      J. Synchrotron Rad. (2012). 19, 274-280. https://doi.org/10.1107/S0909049511056305

.. toctree::
   :maxdepth: 2
   :caption: For MX Users:

   dashboard
   shipping
   sessions
   data

.. toctree::
   :maxdepth: 2
   :caption: For Beamline Staff:

   starting
   staff-dashboard
   staff-beamlines
   staff-shipments
   scheduling
   publications
   staff-support

.. toctree::
   :maxdepth: 2
   :caption: For Developers:

   apis
   reportsv2
   data-types
   layouts
   models
   views
