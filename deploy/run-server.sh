#!/bin/bash

export SERVER_NAME=${SERVER_NAME:-$(hostname --fqdn)}
export CERT_PATH=${CERT_PATH:-/etc/letsencrypt/live/${SERVER_NAME}}

CERT_KEY=${CERT_PATH}/privkey.pem
if [ ! -f $CERT_KEY ]; then
    openssl req -x509 -nodes -newkey rsa:2048 -keyout ${CERT_KEY} -out ${CERT_PATH}/fullchain.pem -subj '/CN=${SERVER_NAME}'
fi

# Make sure we're not confused by old, incompletely-shutdown httpd
# context after restarting the container.  httpd won't start correctly
# if it thinks it is already running.
rm -rf /run/httpd/* /tmp/httpd*

./wait-for-it.sh mxlive-db:5432 -t 60 &&

if [ ! -f /mxlive/local/.dbinit ]; then
    /mxlive/manage.py migrate --noinput &&
    touch /mxlive/local/.dbinit
    chown -R apache:apache /mxlive/local/media /mxlive/local/cache
else
    /mxlive/manage.py migrate --noinput
fi

exec /usr/sbin/httpd -DFOREGROUND -e debug
