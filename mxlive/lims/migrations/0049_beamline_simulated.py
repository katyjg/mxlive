# Generated by Django 3.0.2 on 2020-02-28 14:57

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('lims', '0048_auto_20200227_1445'),
    ]

    operations = [
        migrations.AddField(
            model_name='beamline',
            name='simulated',
            field=models.BooleanField(default=False),
        ),
    ]