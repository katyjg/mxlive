FROM python:3.8-alpine

MAINTAINER Kathryn Janzen <kathryn.janzen@lightsource.ca>

COPY requirements.txt /

RUN apk add --no-cache --virtual .build-deps bash gcc linux-headers musl-dev postgresql-dev libpq libffi-dev \
    apache2-ssl apache2-mod-wsgi certbot-apache openssl openssl-dev python3-dev py3-pip g++ xvfb-run wkhtmltopdf ttf-dejavu zlib zlib-dev jpeg jpeg-dev

RUN set -ex && /usr/bin/pip3 install --upgrade pip && /usr/bin/pip3 install --no-cache-dir -r /requirements.txt

EXPOSE 443

ADD . /mxlive
ADD ./local /mxlive/local

COPY deploy/run-server.sh /run-server.sh
COPY deploy/wait-for-it.sh /wait-for-it.sh
RUN chmod -v +x /run-server.sh /wait-for-it.sh

COPY deploy/mxlive.conf /etc/apache2/conf.d/zzzmxlive.conf

RUN /usr/bin/python3 /mxlive/manage.py collectstatic --noinput

CMD /run-server.sh
