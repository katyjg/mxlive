# -*- coding: utf-8 -*-
# Generated by Django 1.11 on 2017-07-19 21:50
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('lims', '0004_activitylog_user'),
    ]

    operations = [
        migrations.AlterField(
            model_name='containerlocation',
            name='accepts',
            field=models.ManyToManyField(null=True, related_name='locations', to='lims.ContainerType'),
        ),
    ]
