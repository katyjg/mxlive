# Generated by Django 3.0.6 on 2020-07-22 20:38

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('lims', '0064_auto_20200721_2258'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='userfeedback',
            name='project',
        ),
        migrations.AddField(
            model_name='userfeedback',
            name='session',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, to='lims.Session'),
        ),
    ]
