FROM fedora:27
MAINTAINER Kathryn Janzen <kathryn.janzen@lightsource.ca>

RUN dnf -y update && \
  dnf -y install httpd python-pip mod_wsgi python-dateutil python-markdown \
  postgresql-libs python-psycopg2 numpy scipy python-crypto python-memcached wget \
  mod_ssl python-docutils wkhtmltopdf xorg-x11-server-Xvfb which\
  certbot-apache python-ldap openssl\
  && dnf clean all

ADD requirements.txt /

RUN pip install --upgrade pip && pip install -r requirements.txt

EXPOSE 443

ADD . /mxlive

ADD ./local /mxlive/local
ADD deploy/run-server.sh /run-server.sh
ADD deploy/wait-for-it.sh /wait-for-it.sh
RUN chmod -v +x /run-server.sh /wait-for-it.sh
RUN /bin/cp /mxlive/deploy/mxlive.conf /etc/httpd/conf.d/
RUN openssl req -x509 -nodes -newkey rsa:2048 -keyout /etc/pki/tls/private/localhost.key -out /etc/pki/tls/certs/localhost.crt -subj '/CN=localhost'
RUN /bin/mv /etc/httpd/conf.d/ssl.conf /etc/httpd/conf.d/zzzssl.conf
RUN /mxlive/manage.py collectstatic --noinput

VOLUME ["/mxlive/local", "/etc/letsencrypt"]

CMD ["/run-server.sh"]


