# Generated by Django 3.0.6 on 2020-09-23 14:57

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('lims', '0074_auto_20200810_1358'),
    ]

    operations = [
        migrations.AlterModelOptions(
            name='sample',
            options={'ordering': ['priority', 'container__name', 'location__pk', 'name']},
        ),
        migrations.AddField(
            model_name='supportarea',
            name='external',
            field=models.BooleanField(default=False, verbose_name="Affected by factors out of the beamline's control"),
        ),
    ]