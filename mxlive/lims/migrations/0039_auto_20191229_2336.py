# Generated by Django 3.0.1 on 2019-12-30 05:36

from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('lims', '0038_data_times_20191226_2205'),
    ]

    operations = [
        migrations.AlterField(
            model_name='group',
            name='project',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='sample_groups', to=settings.AUTH_USER_MODEL),
        ),
    ]
