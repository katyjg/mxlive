# Generated by Django 3.0.2 on 2020-02-11 17:29

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('schedule', '0007_auto_20200211_1125'),
    ]

    operations = [
        migrations.AlterField(
            model_name='beamtimetype',
            name='beamtime',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='access_types', to='schedule.Beamtime'),
        ),
        migrations.AlterField(
            model_name='beamtimetype',
            name='kind',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='access_types', to='schedule.AccessType'),
        ),
    ]
