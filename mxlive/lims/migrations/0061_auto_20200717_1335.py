# Generated by Django 3.0.6 on 2020-07-17 19:35

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('lims', '0060_auto_20200717_1331'),
    ]

    operations = [
        migrations.AlterField(
            model_name='supportrecord',
            name='areas',
            field=models.ManyToManyField(blank=True, to='lims.SupportArea'),
        ),
    ]
