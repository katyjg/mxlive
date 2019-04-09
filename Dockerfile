FROM fedora:26
MAINTAINER Kathryn Janzen <kathryn.janzen@lightsource.ca>

RUN dnf -y update && \
  dnf -y install httpd python-pip mod_wsgi python-dateutil python-markdown \
  postgresql-libs python-psycopg2 mod_xsendfile numpy scipy python-crypto python-memcached wget \
  mod_ssl python-docutils unzip tar gzip ImageMagick wkhtmltopdf xorg-x11-server-Xvfb which\
  python-msgpack python-matplotlib certbot-apache PyYAML python-twisted python-zope-interface\
  && dnf clean all

ADD requirements.txt /

RUN pip install --upgrade pip && pip install -r requirements.txt

EXPOSE 443

RUN curl https://www.fontsquirrel.com/fonts/download/alegreya -o /tmp/alegreya.zip && \
    unzip /tmp/alegreya.zip -d /usr/share/fonts/alegreya && /bin/rm -f /tmp/alegreya.zip

RUN dnf -y install CBFlib && dnf clean all
ADD . /mxlive

RUN wget https://github.com/d3/d3/releases/download/v4.10.2/d3.zip -O /tmp/d3.v4.zip && \
    unzip /tmp/d3.v4.zip -d /tmp/d3.v4 && /bin/cp /tmp/d3.v4/d3.min.js /mxlive/mxlive/static/js/d3.v4.min.js && \
    /bin/rm -rf /tmp/d3.v4*

RUN wget https://github.com/d3/d3/releases/download/v3.5.16/d3.zip -O /tmp/d3.v3.zip && \
    unzip /tmp/d3.v3.zip -d /tmp/d3.v3 && /bin/cp /tmp/d3.v3/d3.min.js /mxlive/mxlive/static/js/d3.v3.min.js && \
    /bin/rm -rf /tmp/d3.v3*

ADD ./local /mxlive/local
ADD deploy/run-server.sh /run-server.sh
ADD deploy/wait-for-it.sh /wait-for-it.sh
RUN chmod -v +x /run-server.sh /wait-for-it.sh
RUN /bin/cp /mxlive/deploy/mxlive.conf /etc/httpd/conf.d/

RUN /mxlive/manage.py collectstatic --noinput

VOLUME ["/mxlive/local", "/etc/letsencrypt"]

CMD ["/run-server.sh"]


