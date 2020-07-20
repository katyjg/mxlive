# Generated by Django 3.0.6 on 2020-05-27 23:06

from django.db import migrations, models
import django.db.models.deletion
from django.db.models import F, Count, Subquery, OuterRef
from django.forms.models import model_to_dict


def update_layout(apps, schema_editor):

    ContainerType = apps.get_model('lims', 'ContainerType')
    ContainerLocation = apps.get_model('lims', 'ContainerLocation')
    LocationCoord = apps.get_model('lims', 'LocationCoord')
    Sample = apps.get_model('lims', 'Sample')
    db_alias = schema_editor.connection.alias

    for c in ContainerType.objects.using(db_alias).all():
        c.radius = c.layout.get('radius', 8.0)
        c.height = c.layout.get('height', 1.0)
        c.save()

    ContainerLocation.objects.using(db_alias).update(
        kind=Subquery(LocationCoord.objects.using(db_alias).filter(location=OuterRef('pk')).values('kind')[:1]),
        x=Subquery(LocationCoord.objects.using(db_alias).filter(location=OuterRef('pk')).values('x')[:1]),
        y=Subquery(LocationCoord.objects.using(db_alias).filter(location=OuterRef('pk')).values('y')[:1]))

    to_create = []
    for obj in LocationCoord.objects.all():
        if not ContainerLocation.objects.using(db_alias).filter(kind=obj.kind, name=obj.location.name).exists():
            info = model_to_dict(obj, fields=['x', 'y'])
            info['kind'] = obj.kind
            info['name'] = obj.location.name
            to_create.append(ContainerLocation(**info))
        else:
            ContainerLocation.objects.using(db_alias).filter(kind=obj.kind, name=obj.location.name).update(x=obj.x, y=obj.y)

    ContainerLocation.objects.using(db_alias).bulk_create(to_create)

    for s in Sample.objects.using(db_alias).exclude(container__kind=F('location__kind')):
        new_location = ContainerLocation.objects.using(db_alias).get(kind=s.container.kind, name=s.location.name)
        s.location = new_location
        s.save()


class Migration(migrations.Migration):

    dependencies = [
        ('lims', '0054_auto_20200519_1654'),
    ]

    operations = [
        migrations.AddField(
            model_name='containerlocation',
            name='kind',
            field=models.ForeignKey(null=True, on_delete=django.db.models.deletion.CASCADE, to='lims.ContainerType'),
        ),
        migrations.AddField(
            model_name='containerlocation',
            name='x',
            field=models.FloatField(default=0.0),
        ),
        migrations.AddField(
            model_name='containerlocation',
            name='y',
            field=models.FloatField(default=0.0),
        ),
        migrations.AddField(
            model_name='containertype',
            name='height',
            field=models.FloatField(default=1.0),
        ),
        migrations.AddField(
            model_name='containertype',
            name='radius',
            field=models.FloatField(default=8.0),
        ),

        migrations.RunPython(update_layout),
        migrations.RemoveField(
            model_name='containertype',
            name='locations',
        ),
        migrations.AlterField(
            model_name='containerlocation',
            name='kind',
            field=models.ForeignKey(null=True, on_delete=django.db.models.deletion.CASCADE, related_name='locations',
                                    to='lims.ContainerType'),
        ),
        migrations.DeleteModel(
            name='LocationCoord',
        ),
    ]