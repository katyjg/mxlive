# Generated by Django 2.2.5 on 2019-09-12 22:26

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('lims', '0013_auto_20190912_1451'),
    ]

    operations = [
        migrations.AlterField(
            model_name='containertype',
            name='container_locations',
            field=models.ManyToManyField(blank=True, related_name='types', to='lims.ContainerLocation'),
        ),
    ]
