# -*- coding: utf-8 -*-
# Generated by Django 1.11 on 2017-08-18 17:39
from __future__ import unicode_literals

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('lims', '0027_auto_20170818_1132'),
    ]

    operations = [
        migrations.CreateModel(
            name='Dewar',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('staff_comments', models.TextField(blank=True, null=True)),
                ('modified', models.DateTimeField(auto_now=True, verbose_name=b'date modified')),
                ('active', models.BooleanField(default=False)),
                ('beamline', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='lims.Beamline')),
                ('container', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='lims.Container')),
            ],
        ),
        migrations.AddField(
            model_name='beamline',
            name='automounters',
            field=models.ManyToManyField(through='lims.Dewar', to='lims.Container'),
        ),
    ]
