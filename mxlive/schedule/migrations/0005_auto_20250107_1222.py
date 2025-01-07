# Generated by Django 3.2.25 on 2025-01-07 18:22

import colorfield.fields
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('schedule', '0004_accesstype_remote'),
    ]

    operations = [
        migrations.AlterField(
            model_name='accesstype',
            name='color',
            field=colorfield.fields.ColorField(default='#000000', image_field=None, max_length=25, samples=None),
        ),
        migrations.AlterField(
            model_name='accesstype',
            name='id',
            field=models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID'),
        ),
        migrations.AlterField(
            model_name='beamlinesupport',
            name='id',
            field=models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID'),
        ),
        migrations.AlterField(
            model_name='beamtime',
            name='id',
            field=models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID'),
        ),
        migrations.AlterField(
            model_name='downtime',
            name='id',
            field=models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID'),
        ),
        migrations.AlterField(
            model_name='emailnotification',
            name='id',
            field=models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID'),
        ),
        migrations.AlterField(
            model_name='facilitymode',
            name='color',
            field=colorfield.fields.ColorField(default='#000000', image_field=None, max_length=25, samples=None),
        ),
        migrations.AlterField(
            model_name='facilitymode',
            name='id',
            field=models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID'),
        ),
    ]
