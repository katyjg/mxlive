# Generated by Django 3.0.6 on 2020-07-17 19:18

from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('lims', '0058_auto_20200717_1256'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='supportrecord',
            name='session',
        ),
        migrations.AddField(
            model_name='supportrecord',
            name='beamline',
            field=models.ForeignKey(null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='help', to='lims.Beamline'),
        ),
        migrations.AddField(
            model_name='supportrecord',
            name='user',
            field=models.ForeignKey(null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='help', to=settings.AUTH_USER_MODEL),
        ),
    ]
