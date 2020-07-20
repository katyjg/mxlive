# Generated by Django 3.0.2 on 2020-01-14 00:02

from django.db import migrations
import mxlive.utils.fields


class Migration(migrations.Migration):

    dependencies = [
        ('publications', '0002_subjectarea_data'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='journal',
            name='code',
        ),
        migrations.AddField(
            model_name='journal',
            name='codes',
            field=mxlive.utils.fields.StringListField(default='', unique=True, verbose_name='ISSN'),
            preserve_default=False,
        ),
    ]