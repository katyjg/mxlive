FROM fedora:22
MAINTAINER Michel Fodje <michel.fodje@lightsource.ca>

RUN dnf -y update && \
  dnf -y install httpd python-pip mod_wsgi python-ipaddr python-pillow  python-dateutil python-markdown \
  MySQL-python mod_xsendfile texlive texlive-xetex texlive-xetex-def texlive-collection-xetex \
  texlive-graphics sil-gentium-basic-fonts numpy scipy python-ldap python-crypto python-memcached \
  texlive-pst-barcode texlive-multirow mod_ssl python-docutils unzip && dnf clean all

RUN pip install --upgrade pip &&  pip install 'Django==1.6.11'

EXPOSE 443

RUN curl https://www.fontsquirrel.com/fonts/download/alegreya -o /tmp/alegreya.zip && \
    unzip /tmp/alegreya.zip -d /usr/share/fonts/alegreya && /bin/rm -f /tmp/alegreya.zip

ADD . /mxlive
ADD ./local /mxlive/local
ADD deploy/run-server.sh /run-server.sh
ADD deploy/wait-for-it.sh /wait-for-it.sh
RUN chmod -v +x /run-server.sh /wait-for-it.sh
RUN /bin/cp /mxlive/deploy/mxlive.conf /etc/httpd/conf.d/

RUN /mxlive/manage.py collectstatic --noinput


VOLUME ["/mxlive/local", "/users"]

CMD ["/run-server.sh"]

