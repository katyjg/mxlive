# Generated by Django 2.2.5 on 2019-09-14 22:43

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('lims', '0017_create_coords_data'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='containertype',
            name='locations',
        ),
    ]
