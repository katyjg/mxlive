# Generated by Django 3.0.2 on 2020-01-17 15:03

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('publications', '0009_auto_20200116_1117'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='metrics',
            name='captures',
        ),
        migrations.RemoveField(
            model_name='metrics',
            name='usage',
        ),
    ]
