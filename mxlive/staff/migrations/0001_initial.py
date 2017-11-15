# -*- coding: utf-8 -*-
# Generated by Django 1.10.8 on 2017-11-15 19:17
from __future__ import unicode_literals

from django.conf import settings
from django.db import migrations, models
import staff.models


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name='Announcement',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('title', models.CharField(blank=True, max_length=50)),
                ('description', models.TextField(blank=True)),
                ('priority', models.IntegerField(blank=True)),
                ('attachment', models.FileField(blank=True, upload_to=staff.models.get_storage_path)),
                ('url', models.CharField(blank=True, max_length=200)),
            ],
            options={
                'abstract': False,
            },
        ),
        migrations.CreateModel(
            name='UserList',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(max_length=60, unique=True)),
                ('description', models.TextField(blank=True, null=True)),
                ('address', models.GenericIPAddressField()),
                ('active', models.BooleanField(default=False)),
                ('created', models.DateTimeField(auto_now_add=True, verbose_name=b'date created')),
                ('modified', models.DateTimeField(auto_now_add=True, verbose_name=b'date modified')),
                ('users', models.ManyToManyField(blank=True, to=settings.AUTH_USER_MODEL)),
            ],
            options={
                'verbose_name': 'Access List',
            },
        ),
    ]
