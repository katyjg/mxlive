# Generated by Django 3.0.6 on 2020-10-20 21:29

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('lims', '0075_auto_20200923_0857'),
    ]

    operations = [
        migrations.AlterField(
            model_name='supportarea',
            name='external',
            field=models.BooleanField(default=False, verbose_name="External (out of the beamline's control)"),
        ),
    ]