#!/bin/bash

# Make sure we're not confused by old, incompletely-shutdown httpd
# context after restarting the container.  httpd won't start correctly
# if it thinks it is already running.
rm -rf /run/httpd/* /tmp/httpd*

# check of database exists and initialize it if not also copy custom apache config
# if one is available
if [ -f /mxlive/local/mxlive.conf ]; then
    /bin/cp /mxlive/local/mxlive.conf /etc/httpd/conf.d/
fi

if [ ! -f /mxlive/local/.dbinit ]; then
    su -s /bin/bash apache -c "/mxlive/manage.py syncdb --noinput"
    touch /mxlive/local/.dbinit
#else
#    su -s /bin/bash apache -c "/mxlive/manage.py migrate --noinput"
fi

exec /usr/sbin/httpd -D FOREGROUND
