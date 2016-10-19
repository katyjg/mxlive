FROM fedora:21
MAINTAINER Michel Fodje <michel.fodje@lightsource.ca>

RUN yum -y update && \
  yum -y install httpd python-django mod_wsgi python-ipaddr python-pillow  python-dateutil python-markdown \
  MySQL-python mod_xsendfile texlive texlive-xetex texlive-xetex-def texlive-collection-xetex \
  texlive-graphics sil-gentium-basic-fonts numpy scipy python-ldap python-crypto python-memcached \
  mod_ssl && yum clean all

EXPOSE 443

# Simple startup script to avoid some issues observed with container restart 
ADD . /mxlive
ADD ./local /mxlive/local
ADD deploy/run-server.sh /run-server.sh
RUN chmod -v +x /run-server.sh
RUN /bin/cp /mxlive/deploy/mxlive.conf /etc/httpd/conf.d/
RUN curl https://raw.githubusercontent.com/vishnubob/wait-for-it/master/wait-for-it.sh -o /wait-for-it.sh && chmod -v +x /wait-for-it.sh

RUN /mxlive/manage.py collectstatic --noinput


VOLUME ["/mxlive/local", "/users"]

CMD ["/run-server.sh"]

