# Generated by Django 3.0.2 on 2020-01-14 13:00

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('publications', '0005_auto_20200113_2357'),
    ]

    operations = [
        migrations.RenameField(
            model_name='publication',
            old_name='date',
            new_name='published',
        ),
    ]
