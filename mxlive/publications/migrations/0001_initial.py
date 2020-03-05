# Generated by Django 3.0.2 on 2020-01-13 05:20

import datetime
from django.db import migrations, models
import django.db.models.deletion
import django.utils.timezone
from django.utils.timezone import utc
import model_utils.fields
import mxpubs.utils.fields


class Migration(migrations.Migration):

    initial = True

    dependencies = [
    ]

    operations = [
        migrations.CreateModel(
            name='Contributor',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('created', model_utils.fields.AutoCreatedField(default=django.utils.timezone.now, editable=False, verbose_name='created')),
                ('modified', model_utils.fields.AutoLastModifiedField(default=django.utils.timezone.now, editable=False, verbose_name='modified')),
                ('given_name', models.CharField(max_length=100)),
                ('last_name', models.CharField(max_length=100)),
            ],
            options={
                'abstract': False,
            },
        ),
        migrations.CreateModel(
            name='Funder',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('created', model_utils.fields.AutoCreatedField(default=django.utils.timezone.now, editable=False, verbose_name='created')),
                ('modified', model_utils.fields.AutoLastModifiedField(default=django.utils.timezone.now, editable=False, verbose_name='modified')),
                ('name', models.CharField(max_length=255, unique=True)),
                ('code', models.CharField(max_length=50)),
            ],
            options={
                'abstract': False,
            },
        ),
        migrations.CreateModel(
            name='Institution',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('created', model_utils.fields.AutoCreatedField(default=django.utils.timezone.now, editable=False, verbose_name='created')),
                ('modified', model_utils.fields.AutoLastModifiedField(default=django.utils.timezone.now, editable=False, verbose_name='modified')),
                ('name', models.CharField(max_length=255)),
                ('country', models.CharField(blank=True, max_length=255, null=True)),
            ],
            options={
                'abstract': False,
            },
        ),
        migrations.CreateModel(
            name='Journal',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('created', model_utils.fields.AutoCreatedField(default=django.utils.timezone.now, editable=False, verbose_name='created')),
                ('modified', model_utils.fields.AutoLastModifiedField(default=django.utils.timezone.now, editable=False, verbose_name='modified')),
                ('title', models.CharField(max_length=255)),
                ('short_name', models.CharField(max_length=100)),
                ('code', models.CharField(max_length=50, unique=True, verbose_name='ISSN')),
                ('publisher', models.CharField(blank=True, max_length=100, null=True)),
            ],
            options={
                'abstract': False,
            },
        ),
        migrations.CreateModel(
            name='Tag',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('created', model_utils.fields.AutoCreatedField(default=django.utils.timezone.now, editable=False, verbose_name='created')),
                ('modified', model_utils.fields.AutoLastModifiedField(default=django.utils.timezone.now, editable=False, verbose_name='modified')),
                ('name', models.CharField(max_length=255, unique=True)),
                ('description', models.TextField(blank=True)),
            ],
            options={
                'abstract': False,
            },
        ),
        migrations.CreateModel(
            name='SubjectArea',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('created', model_utils.fields.AutoCreatedField(default=django.utils.timezone.now, editable=False, verbose_name='created')),
                ('modified', model_utils.fields.AutoLastModifiedField(default=django.utils.timezone.now, editable=False, verbose_name='modified')),
                ('name', models.CharField(max_length=255, unique=True)),
                ('description', models.TextField(blank=True, null=True)),
                ('code', models.CharField(max_length=10, verbose_name='ASJC Code')),
                ('parent', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='children', to='publications.SubjectArea')),
            ],
            options={
                'abstract': False,
            },
        ),
        migrations.CreateModel(
            name='Publication',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('created', model_utils.fields.AutoCreatedField(default=django.utils.timezone.now, editable=False, verbose_name='created')),
                ('modified', model_utils.fields.AutoLastModifiedField(default=django.utils.timezone.now, editable=False, verbose_name='modified')),
                ('date', models.DateField(verbose_name='Published')),
                ('authors', models.TextField()),
                ('code', models.CharField(max_length=255, null=True, unique=True)),
                ('keywords', mxpubs.utils.fields.StringListField(blank=True)),
                ('abstract', models.TextField(blank=True, null=True)),
                ('kind', models.CharField(choices=[('article', 'Peer-Reviewed Article'), ('proceeding', 'Conference Proceeding'), ('phd_thesis', 'Doctoral Thesis'), ('msc_thesis', 'Masters Thesis'), ('magazine', 'Magazine Article'), ('book', 'Book'), ('chapter', 'Book / Chapter'), ('patent', 'Patent')], default='article', max_length=20, verbose_name='Type')),
                ('active', models.BooleanField(default=False)),
                ('comments', models.TextField(blank=True, null=True)),
                ('main_title', models.CharField(blank=True, max_length=255, null=True)),
                ('title', models.TextField()),
                ('editor', models.TextField(blank=True, null=True)),
                ('publisher', models.CharField(blank=True, max_length=100, null=True)),
                ('volume', models.CharField(blank=True, max_length=100, null=True)),
                ('issue', models.CharField(blank=True, max_length=20, null=True)),
                ('pages', models.CharField(blank=True, max_length=20, null=True)),
                ('contributors', models.ManyToManyField(blank=True, related_name='publications', to='publications.Contributor')),
                ('funders', models.ManyToManyField(blank=True, related_name='publications', to='publications.Funder')),
                ('journal', models.ForeignKey(null=True, on_delete=django.db.models.deletion.CASCADE, related_name='articles', to='publications.Journal')),
                ('tags', models.ManyToManyField(blank=True, related_name='publications', to='publications.Tag', verbose_name='Tags')),
                ('topics', models.ManyToManyField(blank=True, related_name='publications', to='publications.SubjectArea', verbose_name='Subject Areas')),
            ],
            options={
                'abstract': False,
            },
        ),
        migrations.CreateModel(
            name='Metrics',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('expired', models.DateTimeField(db_index=True, default=datetime.datetime(9999, 12, 31, 0, 0, tzinfo=utc), editable=False)),
                ('created', models.DateTimeField(auto_now_add=True)),
                ('modified', models.DateTimeField(auto_now=True)),
                ('effective', models.DateTimeField()),
                ('citations', models.IntegerField(default=0)),
                ('usage', models.IntegerField(default=0)),
                ('captures', models.IntegerField(default=0)),
                ('mentions', models.IntegerField(default=0)),
                ('owner', models.ForeignKey(null=True, on_delete=django.db.models.deletion.CASCADE, related_name='metrics', to='publications.Publication')),
            ],
            options={
                'abstract': False,
            },
        ),
        migrations.CreateModel(
            name='JournalProfile',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('expired', models.DateTimeField(db_index=True, default=datetime.datetime(9999, 12, 31, 0, 0, tzinfo=utc), editable=False)),
                ('created', models.DateTimeField(auto_now_add=True)),
                ('modified', models.DateTimeField(auto_now=True)),
                ('effective', models.DateTimeField()),
                ('scimago_rank', models.FloatField(default=0.0, verbose_name='SJR-Rank')),
                ('impact_factor', models.FloatField(default=0.0, verbose_name='Impact Factor')),
                ('h_index', models.IntegerField(default=1.0, verbose_name='H-Index')),
                ('owner', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='profiles', to='publications.Journal')),
            ],
            options={
                'abstract': False,
            },
        ),
        migrations.CreateModel(
            name='Deposition',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('created', model_utils.fields.AutoCreatedField(default=django.utils.timezone.now, editable=False, verbose_name='created')),
                ('modified', model_utils.fields.AutoLastModifiedField(default=django.utils.timezone.now, editable=False, verbose_name='modified')),
                ('code', models.CharField(max_length=20, unique=True)),
                ('title', models.TextField()),
                ('authors', models.TextField()),
                ('doi', models.CharField(max_length=255, unique=True)),
                ('resolution', models.FloatField(default=0.0)),
                ('released', models.DateField()),
                ('deposited', models.DateField()),
                ('collected', models.DateField(null=True)),
                ('citation', models.CharField(blank=True, max_length=255, null=True)),
                ('reference', models.ForeignKey(null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='depositions', to='publications.Publication')),
                ('tags', models.ManyToManyField(related_name='depositions', to='publications.Tag', verbose_name='Tags')),
            ],
            options={
                'abstract': False,
            },
        ),
        migrations.CreateModel(
            name='Affiliation',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('expired', models.DateTimeField(db_index=True, default=datetime.datetime(9999, 12, 31, 0, 0, tzinfo=utc), editable=False)),
                ('created', models.DateTimeField(auto_now_add=True)),
                ('modified', models.DateTimeField(auto_now=True)),
                ('effective', models.DateTimeField()),
                ('institutions', models.ManyToManyField(blank=True, to='publications.Institution')),
                ('owner', models.ForeignKey(null=True, on_delete=django.db.models.deletion.CASCADE, related_name='profiles', to='publications.Contributor')),
            ],
            options={
                'abstract': False,
            },
        ),
        migrations.AddIndex(
            model_name='metrics',
            index=models.Index(fields=['owner', 'effective'], name='publication_owner_i_ca0155_idx'),
        ),
        migrations.AlterUniqueTogether(
            name='metrics',
            unique_together={('owner', 'effective')},
        ),
        migrations.AddIndex(
            model_name='journalprofile',
            index=models.Index(fields=['owner', 'effective'], name='publication_owner_i_5175a7_idx'),
        ),
        migrations.AlterUniqueTogether(
            name='journalprofile',
            unique_together={('owner', 'effective')},
        ),
        migrations.AddIndex(
            model_name='affiliation',
            index=models.Index(fields=['owner', 'effective'], name='publication_owner_i_bb7427_idx'),
        ),
        migrations.AlterUniqueTogether(
            name='affiliation',
            unique_together={('owner', 'effective')},
        ),
    ]
