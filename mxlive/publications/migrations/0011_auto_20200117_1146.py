# Generated by Django 3.0.2 on 2020-01-17 17:46

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('publications', '0010_auto_20200117_0903'),
    ]

    operations = [
        migrations.RenameModel(
            old_name='Metrics',
            new_name='Metric',
        ),
        migrations.RemoveIndex(
            model_name='metric',
            name='publication_owner_i_ca0155_idx',
        ),
        migrations.AddIndex(
            model_name='metric',
            index=models.Index(fields=['owner', 'effective'], name='publication_owner_i_79d2eb_idx'),
        ),
    ]
