#!/bin/bash

export SERVER_NAME=${SERVER_NAME:-$(hostname --fqdn)}

# Make sure we're not confused by old, incompletely-shutdown httpd
# context after restarting the container.  httpd won't start correctly
# if it thinks it is already running.
rm -rf /run/httpd/* /tmp/httpd*

# Disable chain cert if no ca.crt file available
if [ ! -f /mxlive/local/certs/ca.crt ]; then
    sed -i 's/    SSLCertificateChainFile/#   SSLCertificateChainFile/' /etc/httpd/conf.d/mxlive.conf
else
    sed -i 's/#   SSLCertificateChainFile/    SSLCertificateChainFile/' /etc/httpd/conf.d/mxlive.conf
fi


if [ ! -f /mxlive/local/.dbinit ]; then
    ./wait-for-it.sh mxlive-db:3306 -t 60 &&
    /mxlive/manage.py syncdb --noinput &&
    touch /mxlive/local/.dbinit
    chown -R apache:apache /mxlive/local/media /mxlive/local/cache
fi

exec /usr/sbin/httpd -DFOREGROUND -e debug
