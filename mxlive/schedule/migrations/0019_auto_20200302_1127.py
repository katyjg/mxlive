# Generated by Django 3.0.2 on 2020-03-02 17:27

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('schedule', '0018_auto_20200302_1124'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='emailnotification',
            name='kind',
        ),
        migrations.AddField(
            model_name='beamtime',
            name='maintenance',
            field=models.BooleanField(default=False),
        ),
        migrations.DeleteModel(
            name='EmailType',
        ),
    ]
