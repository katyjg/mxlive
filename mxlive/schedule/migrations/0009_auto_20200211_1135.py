# Generated by Django 3.0.2 on 2020-02-11 17:35

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('schedule', '0008_auto_20200211_1129'),
    ]

    operations = [
        migrations.AddField(
            model_name='beamtime',
            name='access',
            field=models.ManyToManyField(to='schedule.AccessType'),
        ),
        migrations.DeleteModel(
            name='BeamtimeType',
        ),
    ]
