FROM python:3.9-alpine

MAINTAINER Kathryn Janzen <kathryn.janzen@lightsource.ca>

COPY requirements.txt /
COPY deploy/run-server.sh /
COPY deploy/wait-for-it.sh /
ADD . /mxlive

RUN set -ex && \
    apk add --no-cache --virtual libpq apache2-ssl apache2-mod-wsgi certbot-apache openssl sed py3-pip  && \
    /usr/bin/python3 -m venv /venv && source /venv/bin/activate && \
    /venv/bin/pip3 install --no-cache-dir --upgrade pip && \
    /venv/bin/pip3 install --no-cache-dir -r /requirements.txt  && \
    mkdir -p /mxlive/local && \
    chmod -v +x /run-server.sh /wait-for-it.sh && \
    /bin/cp -v /mxlive/deploy/mxlive.conf /etc/apache2/conf.d/99-mxlive.conf && \
    sed -i -E 's@#!/usr/bin/env python.*@#!/venv/bin/python3@' /mxlive/manage.py && \
    /mxlive/manage.py collectstatic --noinput

EXPOSE 443
VOLUME ["/mxlive/local"]
CMD /run-server.sh
