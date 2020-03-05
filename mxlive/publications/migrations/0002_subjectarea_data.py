# Generated by Django 3.0.2 on 2020-01-12 05:34

import csv
import os

from django.db import migrations


def activity(apps, schema_editor):
    """
    Populate Subject Areas
    """
    SubjectArea = apps.get_model('publications', 'SubjectArea')
    db_alias = schema_editor.connection.alias
    with open(os.path.join(os.path.dirname(__file__), 'asjc-codes.tsv'), encoding='utf-8') as fobj:
        reader = csv.DictReader(fobj, fieldnames=['code', 'name'], delimiter='\t')
        to_create = [
            SubjectArea(name=row['name'], code=row['code'])
            for row in reader
        ]

    # create new objects
    SubjectArea.objects.using(db_alias).bulk_create(to_create)

    # Update parents
    to_update = []
    entries = {}
    for sa in SubjectArea.objects.using(db_alias).all():
        entries[sa.code] = sa

    for code, sa in entries.items():
        parent_code = '{}00'.format(sa.code[:2])
        parent = entries.get(parent_code, None)
        if code.endswith('00') or not parent: continue
        sa.parent_id = parent.pk
        to_update.append(sa)

    # update object relationships
    SubjectArea.objects.using(db_alias).bulk_update(to_update, fields=['parent_id'])


class Migration(migrations.Migration):

    dependencies = [
        ('publications', '0001_initial'),
    ]

    operations = [
        migrations.RunPython(activity)
    ]
