#!/bin/bash

# Make sure we're not confused by old, incompletely-shutdown httpd
# context after restarting the container.  httpd won't start correctly
# if it thinks it is already running.
rm -rf /run/httpd/* /tmp/httpd*

# check of database exists and initialize it if not
if [ ! -f /website/local/.dbinit ]; then
    su -s /bin/bash apache -c "/website/manage.py syncdb --noinput"
    touch /website/local/.dbinit
else
    su -s /bin/bash apache -c "/website/manage.py migrate --noinput"
fi

exec /usr/sbin/httpd -D FOREGROUND
