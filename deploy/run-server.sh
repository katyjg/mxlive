#!/bin/bash

export SERVER_NAME=${SERVER_NAME:-$(hostname --fqdn)}
export CERT_PATH=${CERT_PATH:-/etc/letsencrypt/live/${SERVER_NAME}}

# create key if none present
CERT_KEY=${CERT_PATH}/privkey.pem
if [ ! -f $CERT_KEY ]; then
    export CERT_PATH = '/certs'
    CERT_KEY=${CERT_PATH}/privkey.pem
    mkdir -p ${CERT_PATH}
    openssl req -x509 -nodes -newkey rsa:2048 -keyout ${CERT_KEY} -out ${CERT_PATH}/fullchain.pem -subj '/CN=${SERVER_NAME}'
fi

# Make sure we're not confused by old, incompletely-shutdown httpd
# context after restarting the container.  httpd won't start correctly
# if it thinks it is already running.
rm -rf /run/httpd/* /tmp/httpd*

# Configure Apache
if [ -f /usonline/local/certs/server.key ] && [ -f /usonline/local/certs/server.crt ]; then
    # Disable chain cert if no ca.crt file available
    if [ -f /usonline/local/certs/ca.crt ]; then
        /bin/cp /usonline/deploy/usonline-ssl-chain.conf /etc/apache2/conf.d/99-usonline.conf
    else
        /bin/cp /usonline/deploy/usonline-ssl.conf /etc/apache2/conf.d/99-usonline.conf
    fi
else
    /bin/cp /usonline/deploy/usonline.conf /etc/apache2/conf.d/99-usonline.conf
fi

./wait-for-it.sh mxlive-db:5432 -t 60 &&

# Make sure the local directory is a Python package
if [ ! -f /mxlive/local/__init__.py ]; then
    touch /mxlive/local/__init__.py
fi

if [ ! -f /mxlive/local/.dbinit ]; then
    /usr/bin/python3 /mxlive/manage.py migrate --noinput &&
    touch /mxlive/local/.dbinit
    chown -R apache:apache /mxlive/local/media
else
    /usr/bin/python3 /mxlive/manage.py migrate --noinput
fi

# create log directory if missing
if [ ! -d /mxlive/local/logs ]; then
    mkdir -p /mxlive/local/logs
fi


exec /usr/sbin/httpd -DFOREGROUND -e debug
