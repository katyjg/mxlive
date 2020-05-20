Application Program Interfaces
==============================
MxLIVE relies on MxDC as a source of meta-data from data collection sessions on the beamline, and acts as a resource
from which MxDC can fetch sample information. While this close-coupling is tailored to MxDC, all connections are handled
through the use of APIs, so other data collection applications could also be modified to complement MxLIVE.

All API urls begin with `/api/v2/`.

MxDC Integration
----------------

Security
^^^^^^^^

For new project accounts, the UpdateUserKey API can be used to post a new key to the MxLIVE account. If a key already
exists in MxLIVE, this will fail.

.. automodule:: mxlive.remote.views
    :noindex: True
    :members: UpdateUserKey

The remaining APIs for integration with MxDC must be verified using the account's key through a ``VerificationMixin``.

.. automodule:: mxlive.remote.views
    :noindex: True
    :members: VerificationMixin

Sessions
^^^^^^^^
To start an MxLIVE session (when MxDC is opened), use the ``LaunchSession`` API. This will join an existing session if
there is one that has been active in the past seven days, or create a new session. To close a session, use
``CloseSession``. In cases where MxDC closes unexpectedly and the ``CloseSession`` call is not made, the next time any
user attempts to launch a new session on the beamline, existing active sessions are closed.

.. automodule:: mxlive.remote.views
    :noindex: True
    :members: LaunchSession, CloseSession

Samples
^^^^^^^
MxDC can fetch samples belonging to a project account through ``ProjectSamples``. This returns a list of any on-site
samples for the account that are NOT currently loaded in the automounter of a different beamline. For samples loaded in
the automounter of the active beamline, the location of the samples is also included.

.. automodule:: mxlive.remote.views
    :noindex: True
    :members: ProjectSamples

Datasets and Reports
^^^^^^^^^^^^^^^^^^^^
Datasets and Analysis Reports can be uploaded to MxLIVE through ``AddData`` and ``AddReport``. A minimum set of
information is required for each API, and the ID of the new object in MxLIVE is returned.

While the directory for the dataset or report is required for these APIs, that information is not stored in MxLIVE.
Rather, it is sent to the MxLIVE Data Proxy. The Data Proxy returns a secure key which is stored in MxLIVE and used to
fetch files and data through the Data Proxy, since MxLIVE has no direct access to dataset and report files on disk.

.. automodule:: mxlive.remote.views
    :noindex: True
    :members: AddData, AddReport

For details regarding the formatting of new MxLIVE reports, submitted as details to `AddReport`, see :ref:`formatting-reports`.


Remote Connection Access Lists
------------------------------
This is an API to provide a list of users who should have access to a specific remote connection.

``GET`` provides the list of users defined for the remote connection matching the IP address of the request.

``POST`` is used to create and maintain a history of remote connections. Data provided should be in the form of a list
of dictionaries including, at a minimum, the following information:

- ``project``: Should match a username for a project account in MxLIVE
- ``status``: One of the following strings: "Connected", "Disconnected", "Failed", "Finished"
- ``date``: Formatted to match "%Y-%m-%d %H:%M:%S"
- ``name``: A unique identifier for the connection

.. automodule:: mxlive.remote.views
    :noindex: True
    :members: AccessList


