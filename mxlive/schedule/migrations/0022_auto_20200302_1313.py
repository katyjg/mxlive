# Generated by Django 3.0.2 on 2020-03-02 19:13

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('schedule', '0021_emailnotification_send_time'),
    ]

    operations = [
        migrations.AlterField(
            model_name='emailnotification',
            name='send_time',
            field=models.DateTimeField(null=True, verbose_name='Send Time'),
        ),
    ]
