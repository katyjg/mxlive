Getting Started
===============
Deploying MxLIVE on your beamline requires some initial work setting up basic information in your database.

Some basic requirements for deploying MxLIVE in development or production are:

- LDAP authentication: See the instructions at `minkwe/389ds <https://hub.docker.com/r/minkwe/389ds>`_ to set up your own
  389 Directory Server.
- Docker: You will need to build docker images and run them using docker-compose.

Deploying for Development
^^^^^^^^^^^^^^^^^^^^^^^^^
**To deploy the test environment do the following:**

1. Set up your database. Either create a PostGreSQL database on your local machine, or to create a dockerized postgresql
   database (https://hub.docker.com/_/postgres), extract ``deploy/skel-db.tar.gz`` to a working directory and run::

       sudo docker-compose up -d

.. warning:: If you plan to run with Docker and a database other than postgresql, be sure to modify the imports
     in the Dockerfile (eg. for MySQL, you will need to add python-mysql). Sqlite databases are not supported.

2. Copy ``local/settings.py.example`` to ``local/settings.py`` and customize it according to your environment, being
   sure to point to the database you set up in the previous step, and to update your LDAP settings.

.. note:: If you are using the included postgresql docker setup to create your database, use the following command to
     obtain the IP address you should use to update ``DATABASES['default']['HOST']``::

       sudo docker inspect -f '{{range .NetworkSettings.Networks}}{{.IPAddress}}{{end}}' skel-db_database_1

3. Set up a virtual environment and install all requirements::

    python3 -m venv venv
    source venv/bin/activate
    pip install requirements.txt

  - If using PyCharm, set a Project Interpreter to prepare your virtual environment, install all requirements, and
    install minifiers for SCSS and JS files::

        sudo dnf -y install sassc
        sudo npm install babel-minify --global --save-dev

4. To test the server run the following commands in your virtual environment::

    ./manage.py migrate
    ./manage.py runserver 0:8000

   If you are starting with an empty database, it will be pre-populated with a standard sets of ``Container Type``,
   ``Project Type``, ``Data Type``, and if you are using the optional scheduling app, ``Access Type`` and ``Facility Mode``.

5. Connect your browser to http://localhost:8000 and login when prompted. Make sure your LDAP server is running first.

.. note:: After you login on a fresh installation, you will notice that you are directed to the user dashboard, even if
     you are staff. To assign an account as staff, first create a temporary superuser account::

       ./manage.py createsuperuser

     Login to http://localhost:8000/admin with the new superuser account. Select the Project Account that should be
     marked as staff and check the boxes beside "Superuser status" AND "Staff status". After you have logged out, log
     back in with your staff account. The temporary superuser account can be deleted.


Deploying for Production
^^^^^^^^^^^^^^^^^^^^^^^^
**To deploy a full production environment including MxLIVE, the MxLIVE data proxy, a mail server, and databases:**

1. Build the docker image with the command::

    sudo docker build --rm -t mxlive:latest .

2. Create a directory called MxLIVE somewhere, preferably where you place your other persistent docker files
   (e.g. /apps/docker/mxlive), then create the following directory structure within it::

    ├── docker-compose.yml     # Docker compose configuration file
    ├── app-local/             # Local directory for MxLIVE Container
    │   ├── settings.py        # MxLIVE local settings file
    │   ├── logs/              # Log directory for MxLIVE Web Server
    │   └── media/             # Media files for MxLIVE
    ├── certs/                 # Server certificates for the MxLIVE Web Server
    ├── data-local/            # Local directory for mxlive-dataproxy
    │   ├── settings_local.py  # mxlive-dataproxy local settings file
    │   └── logs/              # Logs directory for mxlive-dataproxy
    └── data-cache/            # Cache directory for mxlive-dataproxy

.. note:: A tar archive containing an empty directory structure like this can be found in ``deploy/skel.tar.gz``. Find
          more information about:
          - MxLIVE data proxy - https://github.com/katyjg/mxlive-dataproxy
          - PostGreSQL - https://hub.docker.com/_/postgres/
          - Memcached - https://hub.docker.com/_/memcached

3. Self-signed certificates will be generated in the /certs directory if certificates do not already exist, using the
following command::

   openssl req -x509 -nodes -newkey rsa:2048 -keyout ${CERT_KEY} -out ${CERT_PATH}/fullchain.pem -subj '/CN=${SERVER_NAME}'

4. Customize docker-compose.yml according to your environment. If using external database, mail, or directory servers,
   remove the corresponding entries, and also delete the corresponding links within the app entry.

5. Update app-local/settings.py according to your environment.

6. Change to the top level directory which contains docker-compose.yml. Launch the services using the following
   command::

       sudo docker-compose up -d

7. Done! After a few seconds all your services should be up and ready. You can then connect to mxlive on
   https://localhost/

.. note:: - To monitor logs, use ``sudo docker-compose logs -f``
          - To open a bash console inside the MxLIVE container, use ``sudo docker-compose exec app /bin/bash``
