# -*- coding: utf-8 -*-
# Generated by Django 1.11 on 2017-08-03 19:46
from __future__ import unicode_literals

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('lims', '0019_auto_20170803_1346'),
    ]

    operations = [
        migrations.AlterModelOptions(
            name='group',
            options={'ordering': ('priority',), 'verbose_name': 'Group'},
        ),
    ]
