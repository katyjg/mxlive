# -*- coding: utf-8 -*-
# Generated by Django 1.11.15 on 2019-04-09 20:59
from __future__ import unicode_literals
import requests
from django.conf import settings
from django.db import migrations
import os

PROXY_URL = getattr(settings, 'DOWNLOAD_PROXY_URL', '')


def make_secure_path(path):
    # Generate Download  key on proxy server
    url = PROXY_URL + '/data/create/'
    r = requests.post(url, data={'path': path})
    if r.status_code == 200:
        key = r.json()['key']
        return key
    else:
        raise ValueError('Unable to create SecurePath')


def add_session_url(apps, schema_editor):
    '''
    generate a secure path key and save it
    '''
    Session = apps.get_model('lims', 'Session')
    for session in Session.objects.all():
        try:
            key = make_secure_path(os.path.join(session.project.name, session.name))
            session.url = key
            session.save()
            print("Added secure path to session {}".format(session.name))
        except ValueError:
            print("Error! Could not create secure path")


class Migration(migrations.Migration):

    dependencies = [
        ('lims', '0005_session_url'),
    ]

    operations = [
        migrations.RunPython(add_session_url),
    ]
