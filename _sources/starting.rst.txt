Getting Started
===============

Deploying MxLIVE on your beamline requires some initial work setting up basic information in your database.

Deploying for Development
^^^^^^^^^^^^^^^^^^^^^^^^^

**To deploy the test environment do the following:**

1. Copy settings.py.example in the "local/" folder to settings.py and customize it according to your
environment

.. note:: If you plan to run with Docker and a database other than postgresql, be sure to modify the imports
     in the Dockerfile (eg. for MySQL, you will need to add python-mysql)

2. If using PyCharm, prepare your virtual environment and install all requirements::

    pip install requirements.txt
    sudo dnf -y install sassc
    sudo npm install babel-minify --global --save-dev

3. To test the server run the following commands in your virtual environment::

    ./manage.py migrate
    ./manage.py runserver 0:8000

4. Connect your browser to http://localhost:8000 and log when prompted. Make sure your LDAP server is running first.

Deploying for Production
^^^^^^^^^^^^^^^^^^^^^^^^

**To deploy a full production production environment including docker, mail-relay, ldap, database:**

1. Build the docker image with the command


    sudo docker build --rm -t mxlive:latest .


2. Create a directory called MxLIVE somewhere else, preferably where you place your other persistent docker files
   (e.g. /apps/docker/mxlive), then create the following directory structure within it::

    ├── docker-compose.yml       # The docker compose configuration file for the deployment copy from deploy/ and customize
    ├── app-local/               # The top local directory level directory for MxLIVE Container
    │   ├── settings.py          # MxLIVE local settings file copy from local/ and customize it
    │   ├── cache/               # Cache directory for MxLIVE
    │   ├── logs/                # Log files for MxLIVE Web Server will be placed here
    │   └── media/               # Media files for MxLIVE
    ├── db-backups/              # Data directory for database container (Omit this if you are using and external database server)
    ├── certs/                   # Server certificates for the MxLIVE Web Server
    ├── data-local/              # The top local directory for the mxlive-dataproxy container
    │   ├── settings_local.py    # mxlive-dataproxy local settings file
    │   └── logs/                # Logs directory for mxlive-dataproxy
    ├── data-cache/              # Cache directory for mxlive-dataproxy
    └── ldap/                    # Data directory for 389ds Container (Omit this if you are using and external directory server)
        ├── certs/               # Server certificates for the 389ds Server
        ├── config/              # Config directory for 389ds
        ├── data/                # Data directory for 389ds
        └── logs/                # Logs directory for 389ds


.. note:: - You can find more information about MySQL at https://hub.docker.com/_/mariadb/
          - You can find more information about 389ds at https://hub.docker.com/r/minkwe/389ds/
          - A tar archive containing an empty directory structure like this can be found in "deploy/skel.tar.gz"

3. Generate self-signed certificates in the /certs directory by running the following command inside your mxlive
container (update accordingly)::

   certbot certonly --agree-tos --webroot -w /mxlive/local -d 'example.com'

4. Customize docker-compose.yml according to your environment. If using external database, mail and directory servers,
   remove the corresponding entries, and also delete the corresponding links within the app entry.

5. Update app-local/settings.py according to your environment.

6. Change to the top level directory which contains docker-compose.yml. Launch the services using the following
command::

   sudo docker-compose up -d

   To monitor the logs use the command:

        docker-compose logs -f

7. Done! After a few seconds all your services should be up and ready. You can then connect to mxlive on

   https://localhost/

   Your local host will also be serving as an ldap server for authentication by other hosts at this time if you configured
   the local LDAP option above.
