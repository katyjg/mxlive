# -*- coding: utf-8 -*-
# Generated by Django 1.11 on 2017-08-03 17:32
from __future__ import unicode_literals

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('lims', '0015_auto_20170803_1104'),
    ]

    operations = [
        migrations.RenameField(
            model_name='data',
            old_name='experiment',
            new_name='group',
        ),
        migrations.RenameField(
            model_name='data',
            old_name='crystal',
            new_name='sample',
        ),
        migrations.RenameField(
            model_name='result',
            old_name='experiment',
            new_name='group',
        ),
        migrations.RenameField(
            model_name='result',
            old_name='crystal',
            new_name='sample',
        ),
        migrations.RenameField(
            model_name='sample',
            old_name='experiment',
            new_name='group',
        ),
        migrations.RenameField(
            model_name='scanresult',
            old_name='experiment',
            new_name='group',
        ),
        migrations.RenameField(
            model_name='scanresult',
            old_name='crystal',
            new_name='sample',
        ),
    ]
