# -*- coding: utf-8 -*-
# Generated by Django 1.11 on 2017-07-19 22:00
from __future__ import unicode_literals

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('lims', '0007_auto_20170719_1557'),
    ]

    operations = [
        migrations.AddField(
            model_name='container',
            name='type',
            field=models.ForeignKey(default=0, on_delete=django.db.models.deletion.CASCADE, to='lims.ContainerType'),
            preserve_default=False,
        ),
    ]
