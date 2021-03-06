# Generated by Django 3.0.6 on 2020-07-22 04:58

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('lims', '0063_userareafeedback_userfeedback'),
    ]

    operations = [
        migrations.AddField(
            model_name='userfeedback',
            name='contact',
            field=models.BooleanField(default=False, verbose_name='I would like to be contacted about my recent experience.'),
        ),
        migrations.AlterField(
            model_name='supportarea',
            name='user_feedback',
            field=models.BooleanField(default=False, verbose_name='Add to User Experience Survey'),
        ),
    ]
