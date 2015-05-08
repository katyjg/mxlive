FROM fedora:21
MAINTAINER Michel Fodje <michel.fodje@lightsource.ca>

RUN yum -y update && yum clean all
RUN yum -y install httpd python-django mod_wsgi python-ipaddr python-pillow  python-dateutil python-markdown && yum clean all
RUN yum -y install MySQL-python mod_xsendfile && yum clean all
RUN yum -y install texlive texlive-xetex texlive-xetex-def texlive-collection-xetex texlive-graphics && yum clean all
RUN yum -y install sil-gentium-basic-fonts && yum clean all
RUN yum -y install numpy scipy python-ldap && yum clean all

EXPOSE 443
EXPOSE 80

# Simple startup script to avoid some issues observed with container restart 
ADD . /mxlive
ADD ./local /mxlive/local
ADD deploy/run-server.sh /run-server.sh
RUN chmod -v +x /run-server.sh
RUN /bin/cp /mxlive/deploy/mxlive.conf /etc/httpd/conf.d/
RUN /mxlive/manage.py collectstatic --noinput

VOLUME ["/mxlive/local", "/users"]

CMD ["/run-server.sh"]

