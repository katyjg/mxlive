FROM fedora:26
MAINTAINER Kathryn Janzen <kathryn.janzen@lightsource.ca>

RUN dnf -y update && \
  dnf -y install httpd python-pip mod_wsgi python-ipaddr python-pillow  python-dateutil python-markdown python-slugify \
  postgresql-libs python-psycopg2 mod_xsendfile numpy scipy python-ldap python-crypto python-memcached \
  mod_ssl python-docutils python-unicodecsv unzip tar gzip ImageMagick wkhtmltopdf xorg-x11-server-Xvfb which\
  python-requests python-msgpack python-matplotlib certbot-apache PyYAML python-twisted python-zope-interface \
  && dnf clean all

RUN pip install --upgrade pip &&  pip install 'Django==1.11'

EXPOSE 443

RUN curl https://www.fontsquirrel.com/fonts/download/alegreya -o /tmp/alegreya.zip && \
    unzip /tmp/alegreya.zip -d /usr/share/fonts/alegreya && /bin/rm -f /tmp/alegreya.zip

RUN dnf -y install CBFlib texlive-newtx && dnf clean all
ADD . /mxlive
ADD ./local /mxlive/local
ADD deploy/run-server.sh /run-server.sh
ADD deploy/wait-for-it.sh /wait-for-it.sh
RUN chmod -v +x /run-server.sh /wait-for-it.sh
RUN /bin/cp /mxlive/deploy/mxlive.conf /etc/httpd/conf.d/

RUN /mxlive/manage.py collectstatic --noinput

VOLUME ["/mxlive/local", "/etc/letsencrypt"]

CMD ["/run-server.sh"]


