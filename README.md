MxLIVE
======

MxLIVE (Macromolecular Crystallography Laboratory Information Virtual Environment) is an organizational tool for Mx
synchrotron users allowing easy management of shipments for visits to the CLS, remote monitoring of data collection
sessions at the beamlines with easy viewing of data and analysis reports, as well as convenient options for on demand
data transfer. MxLIVE is fully integrated with MxDC, and, when coupled with the mxlive-dataproxy, provides secure access 
to users' data and results.

Some of the Features:
- Create a Shipment to send to the lab following the steps right from your MxLIVE dashboard - no specially formatted spreadsheets required!
- Manage groups of samples and shipments
- Prioritize samples or groups of samples
- Check shipment status
- Inspect and download data and results from anywhere in the world
- Integrate with existing LDAP user accounts
- Create custom reports using JSON file inputs
- MxLIVE is fully integrated with MxDC


Deploying for Development
=========================

To deploy the test environment do the following:
------------------------------------------------
1. Copy settings_local.py.example in the "local/" folder to settings_local.py and customize it according to your
   environment 
   * Note: if you plan to run with Docker and a database other than postgresql, be sure to modify the imports 
     in the Dockerfile (eg. for MySQL, you will need to add python-mysql)
2. Run ./manage.py collectstatic from the top-level directory (not needed with Docker)
3. Run ./manage.py migrate
4. Run ./manage.py runserver 0:8000
5. Connect your browser to http://localhost:8000 and log when prompted. Make sure your LDAP server is running first.

To deploy a full production production environment including docker, mail-relay, ldap, database:
------------------------------------------------------------------------------------------------
1. Build the docker image with the command

    sudo docker build --rm -t mxlive:latest .

2. Create a directory called MxLIVE somewhere else, preferably where you place your other persistent docker files
   (e.g. /apps/docker/mxlive), then create the following directory structure within it:

        ├── docker-compose.yml       # The docker compose configuration file for the deployment copy from deploy/ and customize
        ├── app/                     # The top local directory level directory for MxLIVE Container
        │   ├── settings_local.py    # MxLIVE local settings file copy from local/ and customize it
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


    NOTE: 
    - You can find more information about MySQL at https://hub.docker.com/_/mariadb/
    - You can find more information about 389ds at https://hub.docker.com/r/minkwe/389ds/    
    - A tar archive containing an empty directory structure like this can be found in "deploy/skel.tar.gz"

3. Generate self-signed certificates in the /certs directory by running the following command inside your mxlive container (update accordingly)

   certbot certonly --agree-tos --webroot -w /mxlive/local -d 'example.com'

4. Customize docker-compose.yml according to your environment. If using external database, mail and directory servers,
   remove the corresponding entries, and also delete the corresponding links within the app entry.

5. Update settings_local.py according to your environment

6. Change to the top level directory which contains docker-compose.yml Launch the services using the following command:

        sudo docker-compose up -d

   To monitor the logs use the command:

        docker-compose logs -f 

7. Done! After a few seconds all your services should be up and ready. You can then connect to mxlive on

   https://localhost/

   Your local host will also be serving as an ldap server for authentication by other hosts at this time if you configured
   the local LDAP option above.

