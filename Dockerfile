FROM fedora:21
MAINTAINER Michel Fodje <michel.fodje@lightsource.ca>

RUN yum -y update && yum clean all
RUN yum -y install httpd python-django mod_wsgi python-ipaddr python-pillow  python-dateutil python-markdown && yum clean all
RUN yum -y install MySQL-python && yum clean all

EXPOSE 80

# Simple startup script to avoid some issues observed with container restart 
ADD . /mxlive
ADD ./local /mxlive/local
ADD deploy/run-server.sh /run-server.sh
RUN chmod -v +x /run-server.sh
RUN /bin/cp /mxlive/deploy/mxlive.conf /etc/httpd/conf.d/
RUN /mxlive/manage.py collectstatic --noinput

VOLUME ["/mxlive/local"]

CMD ["/run-server.sh"]

