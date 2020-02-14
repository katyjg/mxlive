# Generated by Django 3.0.2 on 2020-02-13 18:16

from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ('schedule', '0009_auto_20200211_1135'),
    ]

    operations = [
        migrations.CreateModel(
            name='BeamlineSupport',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('date', models.DateField()),
                ('staff', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='support', to=settings.AUTH_USER_MODEL)),
            ],
        ),
    ]
