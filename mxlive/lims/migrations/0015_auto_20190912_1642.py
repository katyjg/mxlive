# Generated by Django 2.2.5 on 2019-09-12 22:42

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('lims', '0014_auto_20190912_1626'),
    ]

    operations = [
        migrations.RenameField(
            model_name='containertype',
            old_name='container_locations',
            new_name='locations',
        ),
        migrations.AlterField(
            model_name='containerlocation',
            name='accepts',
            field=models.ManyToManyField(blank=True, related_name='acceptors', to='lims.ContainerType'),
        ),
    ]
