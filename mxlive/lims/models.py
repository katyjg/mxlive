from django.conf import settings
from django.utils.translation import ugettext as _
from django.contrib.contenttypes.fields import GenericForeignKey
from django.contrib.contenttypes.models import ContentType
from django.db import models
from django.db.models import Q, F, ExpressionWrapper
from django.utils import dateformat, timezone
from django.contrib.auth.models import AbstractUser

#from django.contrib.postgres.fields import JSONField
from jsonfield.fields import JSONField

import copy
import hashlib
import string
from model_utils import Choices
from datetime import datetime, timedelta
import json
import itertools

from django_auth_ldap.backend import populate_user, populate_user_profile
from django.db.models.signals import pre_delete, post_delete
from django.dispatch import receiver
from staff import slap

IDENTITY_FORMAT = '-%y%m'
RESTRICTED_DOWNLOADS = getattr(settings, 'RESTRICTED_DOWNLOADS', False)

DRAFT = 0
SENT = 1
ON_SITE = 2
LOADED = 3
RETURNED = 4
ACTIVE = 5
PROCESSING = 6
COMPLETE = 7
REVIEWED = 8
ARCHIVED = 9
TRASHED = 10

GLOBAL_STATES = Choices(
    (0, 'DRAFT', _('Draft')),
    (1, 'SENT', _('Sent')),
    (2, 'ON_SITE', _('On-site')),
    (3, 'LOADED', _('Loaded')),
    (4, 'RETURNED', _('Returned')),
    (5, 'ACTIVE', _('Active')),
    (6, 'PROCESSING', _('Processing')),
    (7, 'COMPLETE', _('Complete')),
    (8, 'REVIEWED', _('Reviewed')),
    (9, 'ARCHIVED', _('Archived')),
    (10, 'TRASHED', _('Trashed'))
)


class Beamline(models.Model):
    name = models.CharField(max_length=600)
    acronym = models.CharField(max_length=50)
    energy_lo = models.FloatField(default=4.0)
    energy_hi = models.FloatField(default=18.5)
    contact_phone = models.CharField(max_length=60)
    automounters = models.ManyToManyField('Container', through='Dewar', through_fields=('beamline', 'container'))

    def __unicode__(self):
        return self.acronym

    def active_session(self):
        return self.sessions.filter(pk__in=Stretch.objects.active().values_list('session__pk')).first()

    def active_automounter(self):
        return self.active_dewar().container

    def active_dewar(self):
        return self.dewar_set.filter(active=True).first()


class Carrier(models.Model):
    name = models.CharField(max_length=60)
    phone_number = models.CharField(max_length=20)
    fax_number = models.CharField(max_length=20)
    code_regex = models.CharField(max_length=60)
    url = models.URLField()

    def __unicode__(self):
        return self.name


class Project(AbstractUser):
    HELP = {
        'contact_person': "Full name of contact person",
    }
    name = models.SlugField('account name')
    contact_person = models.CharField(max_length=200, blank=True, null=True)
    contact_email = models.EmailField(max_length=100, blank=True, null=True)
    carrier = models.ForeignKey(Carrier, blank=True, null=True)
    account_number = models.CharField(max_length=50, blank=True, null=True)
    department = models.CharField(max_length=600, blank=True, null=True)
    address = models.CharField(max_length=600, blank=True, null=True)
    city = models.CharField(max_length=180, blank=True, null=True)
    province = models.CharField(max_length=180, blank=True, null=True)
    postal_code = models.CharField(max_length=30, blank=True, null=True)
    country = models.CharField(max_length=180, blank=True, null=True)
    contact_phone = models.CharField(max_length=60, blank=True, null=True)
    contact_fax = models.CharField(max_length=60, blank=True, null=True)
    organisation = models.CharField(max_length=600, blank=True, null=True)
    show_archives = models.BooleanField(default=False)
    key = models.CharField(max_length=100, blank=True, null=True)

    created = models.DateTimeField('date created', auto_now_add=True, editable=False)
    modified = models.DateTimeField('date modified', auto_now=True, editable=False)
    updated = models.BooleanField(default=False)    
    
    def identity(self):
        return 'PR%03d%s' % (self.id, self.created.strftime(IDENTITY_FORMAT))
    identity.admin_order_field = 'pk'
        
    def __unicode__(self):
        return self.name

    def get_archive_filter(self):
        if self.show_archives:
            return {'status__lte': LimsBaseClass.STATES.ARCHIVED}
        else:
            return {'status__lt': LimsBaseClass.STATES.ARCHIVED}

    def shifts_used_by_year(self, year, blname):
        shifts = []
        for d in self.data_set.filter(created__year=year).filter(beamline=Beamline.objects.get(name=blname)):
            if [d.created.date(), d.created.hour/8] not in shifts:
                shifts.append([d.created.date(), d.created.hour/8])
        return len(shifts)

    def label_hash(self):
        return self.name
    
    def shipment_count(self):
        this_year = datetime.now().year
        return Shipment.objects.filter(project__exact=self).filter(date_shipped__year=this_year).count()
    shipment_count.short_description = "Shipments in {}".format(datetime.now().year)

    def delete(self, *args, **kwargs):
        self.user.delete()
        return super(self.__class__, self).delete(*args, **kwargs)
    
    class Meta:
        verbose_name = "Project Account"


class Hours(models.Func):
    function = 'HOUR'
    template = '%(function)s(%(expressions)s)'

    def as_postgresql(self, compiler, connection):
        self.arg_joiner = " - "
        return self.as_sql(compiler, connection, function="EXTRACT", template="%(function)s(epoch FROM %(expressions)s)/3600")

    def as_mysql(self, compiler, connection):
        self.arg_joiner = " , "
        return self.as_sql(compiler, connection, function="TIMESTAMPDIFF", template="-%(function)s(HOUR,%(expressions)s)")

    def as_sqlite(self, compiler, connection):
        # the template string needs to escape '%Y' to make sure it ends up in the final SQL. Because two rounds of
        # template parsing happen, it needs double-escaping ("%%%%").
        return self.as_sql(compiler, connection, function="strftime", template="%(function)s(\"%%%%H\",%(expressions)s)")


class Shifts(models.Func):
    function = 'HOUR'
    template = '%(function)s(%(expressions)s)'

    def as_postgresql(self, compiler, connection):
        self.arg_joiner = " - "
        return self.as_sql(compiler, connection, function="EXTRACT", template="(%(function)s(epoch FROM %(expressions)s)/28800)")

    def as_mysql(self, compiler, connection):
        self.arg_joiner = " , "
        return self.as_sql(compiler, connection, function="TIMESTAMPDIFF", template="-%(function)s(HOUR,%(expressions)s)/8")

    def as_sqlite(self, compiler, connection):
        # the template string needs to escape '%Y' to make sure it ends up in the final SQL. Because two rounds of
        # template parsing happen, it needs double-escaping ("%%%%").
        return self.as_sql(compiler, connection, function="strftime", template="%(function)s(\"%%%%H\",%(expressions)s)")


class StretchQuerySet(models.QuerySet):

    def active(self, extras={}):
        return self.filter(end__isnull=True, **extras)

    def recent(self, extras={}):
        recently = timezone.now() - timedelta(minutes=5)
        return self.filter(end__gte=recently, **extras)

    def with_duration(self):
        return self.filter(end__isnull=False).annotate(duration=ExpressionWrapper((F('end')-F('start'))/60000000, output_field=models.IntegerField()))

    def with_hours(self):
        return self.annotate(hours=Hours(F('end'), F('start'), output_field=models.FloatField()))

    def with_shifts(self):
        return self.annotate(shifts=Shifts(F('end'), F('start'), output_field=models.FloatField()))


class StretchManager(models.Manager.from_queryset(StretchQuerySet)):
    use_for_related_fields = True


class Session(models.Model):
    created = models.DateTimeField('date created', auto_now_add=True, editable=False)
    name = models.CharField(max_length=100)
    project = models.ForeignKey(Project, related_name="sessions")
    beamline = models.ForeignKey(Beamline, related_name="sessions")
    comments = models.TextField()

    def launch(self):
        Stretch.objects.active(extras={'session__beamline':self.beamline}).exclude(session=self).update(end=timezone.now())
        self.stretches.recent().update(end=None)
        stretch = self.stretches.active().last() or Stretch.objects.create(session=self, start=timezone.now())
        return stretch

    def close(self):
        self.stretches.active().update(end=timezone.now())

    def is_active(self):
        return self.stretches.active().exists()

    def total_time(self):
        t = sum(self.stretches.with_duration().values_list("duration", flat=True))
        if self.is_active():
            t += int((timezone.now() - self.stretches.active().first().start).total_seconds())/60
        return t/60

    def start(self):
        return self.stretches.last().start

    def end(self):
        return self.stretches.start().end


class Stretch(models.Model):
    start = models.DateTimeField(null=False, blank=False)
    end = models.DateTimeField(null=True, blank=True)
    session = models.ForeignKey(Session, related_name='stretches')
    objects = StretchManager()

    class Meta:
        verbose_name = u"Beamline Usage"
        verbose_name_plural = u"Beamline Usage"
        ordering = ['-start', ]


class LimsBaseClass(models.Model):
    # STATES/TRANSITIONS define a finite state machine (FSM) for the Shipment (and other 
    # models.Model instances also defined in this file).
    #
    # STATES: an Enum specifying all of the valid states for instances of Shipment.
    #
    # TRANSITIONS: a dict specifying valid state transitions. the keys are starting STATES and the 
    #     values are lists of valid final STATES. 

    STATES = GLOBAL_STATES
    TRANSITIONS = {
        STATES.DRAFT: [STATES.SENT],
        STATES.SENT: [STATES.ON_SITE, STATES.DRAFT],
        STATES.ON_SITE: [STATES.RETURNED],
        STATES.LOADED: [STATES.ON_SITE],
        STATES.RETURNED: [STATES.ARCHIVED, STATES.ON_SITE],
        STATES.ACTIVE: [STATES.PROCESSING, STATES.COMPLETE, STATES.REVIEWED, STATES.ARCHIVED],
        STATES.PROCESSING: [STATES.COMPLETE, STATES.REVIEWED, STATES.ARCHIVED],
        STATES.COMPLETE: [STATES.ACTIVE, STATES.PROCESSING, STATES.REVIEWED, STATES.ARCHIVED],
        STATES.REVIEWED: [STATES.ARCHIVED],
    }

    project = models.ForeignKey(Project)
    name = models.CharField(max_length=60)
    staff_comments = models.TextField(blank=True, null=True)
    created = models.DateTimeField('date created', auto_now_add=True, editable=False)
    modified = models.DateTimeField('date modified', auto_now=True, editable=False)

    class Meta:
        abstract = True

    def __unicode__(self):
        return self.name

    def is_editable(self):
        return self.status == self.STATES.DRAFT 
    
    def is_deletable(self):
        return self.status == self.STATES.DRAFT 

    def is_closable(self):
        return self.status == self.STATES.RETURNED 

    def delete(self, request=None):
        super(LimsBaseClass, self).delete()

    def archive(self, request=None):
        if self.is_closable():
            self.change_status(self.STATES.ARCHIVED)

    def send(self, request=None):
        self.change_status(self.STATES.SENT)

    def unsend(self, request=None):
        self.change_status(self.STATES.DRAFT)

    def unreturn(self, request=None):
        self.change_status(self.STATES.ON_SITE)

    def receive(self, request=None):
        self.change_status(self.STATES.ON_SITE) 

    def load(self, request=None):
        self.change_status(self.STATES.LOADED)    

    def unload(self, request=None):
        self.change_status(self.STATES.ON_SITE)   

    def returned(self, request=None):
        self.change_status(self.STATES.RETURNED)     

    def trash(self, request=None):
        self.change_status(self.STATES.TRASHED)     

    def change_status(self, status):
        if status == self.status:
            return
        if status not in self.TRANSITIONS[self.status]:
            raise ValueError("Invalid transition on '{}.{}':  '{}' -> '{}'".format(
                self.__class__, self.pk, self.STATES[self.status], self.STATES[status]))
        self.status = status
        self.save()

    def add_comments(self, message):
        if self.staff_comments:
            if string.find(self.staff_comments, message) == -1:
                self.staff_comments += ' ' + message
        else:
            self.staff_comments = message
        self.save()


class ObjectBaseClass(LimsBaseClass):
    STATUS_CHOICES = (
        (LimsBaseClass.STATES.DRAFT, _('Draft')),
        (LimsBaseClass.STATES.SENT, _('Sent')),
        (LimsBaseClass.STATES.ON_SITE, _('On-site')),
        (LimsBaseClass.STATES.RETURNED, _('Returned')),
        (LimsBaseClass.STATES.ARCHIVED, _('Archived'))
    )
    status = models.IntegerField(choices=STATUS_CHOICES, default=LimsBaseClass.STATES.DRAFT)

    class Meta:
        abstract = True


class LoadableBaseClass(LimsBaseClass):
    STATUS_CHOICES = (
        (LimsBaseClass.STATES.DRAFT, _('Draft')),
        (LimsBaseClass.STATES.SENT, _('Sent')),
        (LimsBaseClass.STATES.ON_SITE, _('On-site')),
        (LimsBaseClass.STATES.LOADED, _('Loaded')),
        (LimsBaseClass.STATES.RETURNED, _('Returned')),
        (LimsBaseClass.STATES.ARCHIVED, _('Archived'))
    )
    TRANSITIONS = copy.deepcopy(LimsBaseClass.TRANSITIONS)
    TRANSITIONS[LimsBaseClass.STATES.ON_SITE] = [LimsBaseClass.STATES.RETURNED, LimsBaseClass.STATES.LOADED]

    status = models.IntegerField(choices=STATUS_CHOICES, default=LimsBaseClass.STATES.DRAFT)

    class Meta:
        abstract = True


class DataBaseClass(LimsBaseClass):
    STATUS_CHOICES = (
        (LimsBaseClass.STATES.ACTIVE, _('Active')),
        (LimsBaseClass.STATES.ARCHIVED, _('Archived')),
        (LimsBaseClass.STATES.TRASHED, _('Trashed'))
    )
    TRANSITIONS = copy.deepcopy(LimsBaseClass.TRANSITIONS)
    TRANSITIONS[LimsBaseClass.STATES.ACTIVE] = [LimsBaseClass.STATES.TRASHED, LimsBaseClass.STATES.ARCHIVED]
    TRANSITIONS[LimsBaseClass.STATES.ARCHIVED] = [LimsBaseClass.STATES.TRASHED]

    status = models.IntegerField(choices=STATUS_CHOICES, default=LimsBaseClass.STATES.ACTIVE)

    def is_closable(self):
        return self.status not in [LimsBaseClass.STATES.ARCHIVED, LimsBaseClass.STATES.TRASHED]

    class Meta:
        abstract = True


class Shipment(ObjectBaseClass):
    HELP = {
        'name': "This should be an externally visible label",
        'carrier': "Select the company handling this shipment. To change the default option, edit your profile.",
        'cascade': 'containers and samples (along with groups, datasets and results)',
        'cascade_help': 'All associated containers will be left without a shipment'
    }
    comments = models.TextField(blank=True, null=True, max_length=200)
    tracking_code = models.CharField(blank=True, null=True, max_length=60)
    return_code = models.CharField(blank=True, null=True, max_length=60)
    date_shipped = models.DateTimeField(null=True, blank=True)
    date_received = models.DateTimeField(null=True, blank=True)
    date_returned = models.DateTimeField(null=True, blank=True)
    carrier = models.ForeignKey(Carrier, null=True, blank=True)
    storage_location = models.CharField(max_length=60, null=True, blank=True)
   
    def identity(self):
        return 'SH%03d%s' % (self.id, self.created.strftime(IDENTITY_FORMAT))
    identity.admin_order_field = 'pk'

    def groups_by_priority(self):
        return self.group_set.order_by('priority')

    def barcode(self):
        return self.tracking_code or self.name

    def num_containers(self):
        return self.container_set.count()

    def num_samples(self):
        return sum([c.sample_set.count() for c in self.container_set.all()])

    def num_datasets(self):
        samples = self.project.sample_set.filter(container__pk__in=self.container_set.values_list('pk'))
        return sum([c.data_set.count() for c in samples])

    def num_results(self):
        samples = self.project.sample_set.filter(container__pk__in=self.container_set.values_list('pk'))
        return sum([c.result_set.count() for c in samples])

    def is_sendable(self):
        return self.status == self.STATES.DRAFT and not self.shipping_errors()

    def is_receivable(self):
        return self.status == self.STATES.SENT

    def is_pdfable(self):
        return self.is_sendable() or self.status >= self.STATES.SENT
    
    def is_xlsable(self):
        # can generate spreadsheet as long as there are no orphan samples with no group)
        return not Sample.objects.filter(container__in=self.container_set.all()).filter(group__exact=None).exists()
    
    def is_returnable(self):
        return self.status == self.STATES.ON_SITE 

    def has_labels(self):
        return self.status <= self.STATES.SENT and (self.num_containers() or self.component_set.filter(label=True))

    def is_processed(self):
        # if all groups in shipment are complete, then it is a processed shipment.
        group_list = Group.objects.filter(shipment__get_container_list=self)
        for container in self.container_set.all():
            for group in container.get_group_list():
                if group not in group_list:
                    group_list.append(group)
        for group in group_list:
            if group.is_reviewable():
                return False
        return True

    def is_processing(self):
        return self.project.sample_set.filter(container__shipment__exact=self).filter(
            Q(pk__in=self.project.data_set.values('sample')) |
            Q(pk__in=self.project.result_set.values('sample'))).exists()
 
    def add_component(self):
        return self.status <= self.STATES.SENT
 
    def label_hash(self):
        # use dates of project, shipment, and each container within to determine
        # when contents were last changed
        txt = str(self.project) + str(self.project.modified) + str(self.modified)
        for container in self.container_set.all():
            txt += str(container.modified)
        h = hashlib.new('ripemd160')  # no successful collision attacks yet
        h.update(txt)
        return h.hexdigest()
    
    def shipping_errors(self):
        """ Returns a list of descriptive string error messages indicating the Shipment is not
            in a 'shippable' state
        """
        errors = []
        if self.num_containers() == 0:
            errors.append("no Containers")
        for container in self.container_set.all():
            if container.num_samples() == 0:
                errors.append("empty Container (%s)" % container.name)
        return errors
    
    def groups(self):
        return self.group_set.order_by('-priority')

    def delete(self, request=None, cascade=True):
        if self.is_deletable():
            if not cascade:
                self.container_set.all().update(shipment=None)
            for obj in self.container_set.all():
                obj.delete(request=request)
            super(Shipment, self).delete(request=request)

    def receive(self, request=None):
        self.date_received = timezone.now()
        self.save()
        for obj in self.container_set.all():
            obj.receive(request=request)
        super(Shipment, self).receive(request=request)

    def send(self, request=None):
        if self.is_sendable():
            self.date_shipped = timezone.now()
            self.save()
            for obj in self.container_set.all():
                obj.send(request=request)
            self.group_set.all().update(status=Group.STATES.ACTIVE)
            super(Shipment, self).send(request=request)

    def unsend(self, request=None):
        if self.status == self.STATES.SENT:
            self.date_shipped = None
            self.status = self.STATES.DRAFT
            self.save()
            for obj in self.container_set.all():
                obj.unsend()
            self.group_set.all().update(status=Group.STATES.DRAFT)

    def unreturn(self, request=None):
        if self.status == self.STATES.RETURNED:
            self.date_shipped = None
            self.status = self.STATES.ON_SITE
            self.save()
            for obj in self.container_set.all():
                obj.unreturn()

    def returned(self, request=None):
        if self.is_returnable():
            self.date_returned = timezone.now()
            self.save()
            for obj in self.container_set.all():
                obj.returned(request=request)
            super(Shipment, self).returned(request=request)

    def archive(self, request=None):
        for obj in self.container_set.all():
            obj.archive(request=request)
        super(Shipment, self).archive(request=request)


class ComponentType(models.Model):
    name = models.CharField(max_length=50)

    def __unicode__(self):
        return self.name


class Component(models.Model):
    shipment = models.ForeignKey(Shipment, related_name="components")
    kind = models.ForeignKey(ComponentType)


class ContainerType(models.Model):
    STATES = Choices(
        (0, 'PENDING', _('Pending')),
        (1, 'LOADED', _('Loaded')),
    )
    TRANSITIONS = {
        STATES.PENDING: [STATES.LOADED],
        STATES.LOADED: [STATES.PENDING],
    }
    name = models.CharField(max_length=20)
    container_locations = models.ManyToManyField("ContainerLocation", blank=True, related_name="containers")
    layout = JSONField(null=True, blank=True)
    envelope = models.CharField(max_length=200, blank=True)

    def __unicode__(self):
        return self.name.title()


class ContainerLocation(models.Model):
    name = models.CharField(max_length=5)
    accepts = models.ManyToManyField(ContainerType, blank=True, related_name="locations")

    def __unicode__(self):
        return self.name


class Container(LoadableBaseClass):
    HELP = {
        'name': "A visible label on the container. If there is a barcode on the container, scan it here",
        'capacity': "The maximum number of samples this container can hold",
        'cascade': 'samples (along with groups, datasets and results)',
        'cascade_help': 'All associated samples will be left without a container'
    }
    kind = models.ForeignKey(ContainerType, blank=False, null=False)
    shipment = models.ForeignKey(Shipment, blank=True, null=True)
    comments = models.TextField(blank=True, null=True)
    priority = models.IntegerField(default=0)
    parent = models.ForeignKey('self', on_delete=models.CASCADE, blank=True, null=True, related_name="children")
    location = models.ForeignKey(ContainerLocation, blank=True, null=True)

    def identity(self):
        return 'CN%03d%s' % (self.id, self.created.strftime(IDENTITY_FORMAT))
    identity.admin_order_field = 'pk'

    def __unicode__(self):
        return "{} | {} | {}".format(self.project.username, self.kind.name.title(), self.name.title())

    class Meta:
        unique_together = (
            ("project", "name", "shipment"),
        )
        ordering = ('kind', 'location')

    def barcode(self):
        return self.name

    def num_samples(self):
        return self.sample_set.count()

    def has_children(self):
        return self.children.count() > 0

    def accepts_children(self):
        return self.kind.container_locations.filter(accepts__isnull=False).exists()

    def accepted_by(self):
        return ContainerType.objects.filter(pk__in=self.kind.locations.values_list('containers', flat=True))

    def children_by_location(self):
        return self.children.order_by('location')

    def is_assigned(self):
        return self.shipment is not None

    def capacity(self):
        return self.kind.container_locations.count()

    def groups(self):
        groups = set([])
        for sample in self.sample_set.all():
            for group in sample.group_set.all():
                groups.add('%s-%s' % (group.project.name, group.name))
        return ', '.join(groups)
    
    def get_group_list(self):
        groups = list()
        for sample in self.sample_set.all():
            if sample.group not in groups:
                groups.append(sample.group)
        return groups
    
    def update_priority(self):
        """ Updates the Container's priority to max(group priorities)
        """
        for field in ['priority']:
            priority = None
            for sample in self.sample_set.all():
                if sample.group:
                    if priority is None:
                        priority = getattr(sample.group, field)
                    else:
                        priority = max(priority, getattr(sample.group, field))
            if priority is not None:
                setattr(self, field, priority)
    
    def loc_and_xtal(self):
        retval = {}
        xtalset = self.sample_set.all()
        for xtal in xtalset:
            retval[xtal.container_location] = xtal        
        return retval

    def delete(self, request=None, cascade=True):
        if self.is_deletable:
            if not cascade:
                self.sample_set.all().update(container=None)
            for obj in self.sample_set.all():
                obj.delete(request=request)
            super(Container, self).delete(request=request)

    def json_dict(self):
        return {
            'project_id': self.project.pk,
            'id': self.pk,
            'name': self.name,
            'type': self.kind.name,
            'load_position': '',
            'comments': self.comments,
            'samples': [sample.pk for sample in self.sample_set.all()]
        }


class Dewar(models.Model):
    beamline = models.ForeignKey(Beamline, on_delete=models.CASCADE)
    container = models.ForeignKey(Container, on_delete=models.CASCADE)
    staff_comments = models.TextField(blank=True, null=True)
    modified = models.DateTimeField('date modified', auto_now=True, editable=False)
    active = models.BooleanField(default=False)

    def identity(self):
        return 'DE%03d%s' % (self.id, self.created.strftime(IDENTITY_FORMAT))
    identity.admin_order_field = 'pk'

    def json_dict(self):
        return {
            'project_id': self.project.pk,
            'id': self.pk,
            'name': self.beamline.name,
            'comments': self.staff_comments,
            'container': [container.pk for container in self.children.all()]
        }


class SpaceGroup(models.Model):
    CS_CHOICES = (
        ('a', 'triclinic'),
        ('m', 'monoclinic'),
        ('o', 'orthorombic'),
        ('t', 'tetragonal'),
        ('h', 'hexagonal'),
        ('c', 'cubic'),
    )
    
    LT_CHOICES = (
        ('P', 'primitive'),
        ('C', 'side-centered'),
        ('I', 'body-centered'),
        ('F', 'face-centered'),
        ('R', 'rhombohedral'),
    )
    
    name = models.CharField(max_length=20)
    crystal_system = models.CharField(max_length=1, choices=CS_CHOICES)
    lattice_type = models.CharField(max_length=1, choices=LT_CHOICES)
    
    def __unicode__(self):
        return self.name


class Group(LimsBaseClass):
    STATUS_CHOICES = (
        (LimsBaseClass.STATES.DRAFT, _('Draft')),
        (LimsBaseClass.STATES.ACTIVE, _('Active')),
        (LimsBaseClass.STATES.PROCESSING, _('Processing')),
        (LimsBaseClass.STATES.COMPLETE, _('Complete')),
        (LimsBaseClass.STATES.REVIEWED, _('Reviewed')),
        (LimsBaseClass.STATES.ARCHIVED, _('Archived'))
    )

    HELP = {
        'cascade': 'samples, datasets and results',
        'cascade_help': 'All associated samples will be left without a group',
        'kind': "If SAD or MAD, be sure to provide the absorption edge below. Otherwise Se-K will be assumed.",
        'plan': "Select the plan which describes your instructions for all samples in this group.",
        'delta_angle': 'If left blank, an appropriate value will be calculated during screening.',
        'total_angle': 'The total angle range to collect.',
        'multiplicity': 'Values entered here take precedence over the specified "Angle Range".',
    }
    EXP_TYPES = Choices(
        (0, 'NATIVE', 'Native'),
        (1, 'MAD', 'MAD'),
        (2, 'SAD', 'SAD'),
    )
    EXP_PLANS = Choices(
        (0, 'RANK_AND_COLLECT_BEST', 'Rank and collect best'),
        (1, 'COLLECT_FIRST_GOOD', 'Collect first good'),
        (2, 'SCREEN_AND_CONFIRM', 'Screen and confirm'),
        (3, 'SCREEN_AND_COLLECT', 'Screen and collect'),
        (4, 'JUST_COLLECT', 'Just collect'),
    )
    TRANSITIONS = copy.deepcopy(LimsBaseClass.TRANSITIONS)
    TRANSITIONS[LimsBaseClass.STATES.DRAFT] = [LimsBaseClass.STATES.ACTIVE]

    status = models.IntegerField(choices=STATUS_CHOICES, default=LimsBaseClass.STATES.DRAFT)
    shipment = models.ForeignKey(Shipment, null=True, blank=True)
    energy = models.DecimalField(null=True, max_digits=10, decimal_places=4, blank=True)
    kind = models.IntegerField('exp. type', choices=EXP_TYPES, default=EXP_TYPES.NATIVE)
    absorption_edge = models.CharField(max_length=5, null=True, blank=True)
    plan = models.IntegerField(choices=EXP_PLANS, default=EXP_PLANS.SCREEN_AND_CONFIRM)
    comments = models.TextField(blank=True, null=True)
    priority = models.IntegerField(blank=True, null=True)
    sample_count = models.PositiveIntegerField('Number of Samples', default=1)

    class Meta:
        verbose_name = 'Group'
        unique_together = (
            ("project", "name", "shipment"),
        )
        ordering = ['priority']

    def identity(self):
        return 'EX%03d%s' % (self.id, self.created.strftime(IDENTITY_FORMAT))    
    identity.admin_order_field = 'pk'

    def num_samples(self):
        return self.sample_set.count()

    def get_shipments(self):
        return self.project.shipment_set.filter(pk__in=self.sample_set.values('container__shipment__pk'))

    def best_sample(self):
        # need to change to [id, score]
        if self.plan == Group.EXP_PLANS.RANK_AND_COLLECT_BEST:
            results = self.project.result_set.filter(group=self, sample__in=self.sample_set.all()).order_by('-score')
            if results:
                return [results[0].sample.pk, results[0].score]

    def unassigned_samples(self):
        return self.sample_count - self.sample_set.count()

    def group_errors(self):
        """ Returns a list of descriptive string error messages indicating the group has missing samples
        """
        errors = []
        if self.sample_set.count() == 0:
            errors.append("no samples")
        if self.status == Group.STATES.ACTIVE:
            diff = self.sample_set.count() - self.sample_set.filter(
                status__in=[Sample.STATES.ON_SITE, Sample.STATES.LOADED]).count()
            if diff:
                errors.append("%i samples have not arrived on-site." % diff)
        return errors

    def is_processing(self):
        return self.sample_set.filter(
            Q(pk__in=self.project.data_set.values('sample')) |
            Q(pk__in=self.project.result_set.values('sample'))).exists()

    def is_reviewable(self):
        return self.status != Group.STATES.REVIEWED
    
    def is_closable(self):
        return self.sample_set.all().exists() and not self.sample_set.exclude(
            status__in=[Sample.STATES.RETURNED, Sample.STATES.ARCHIVED]).exists() and \
               self.status != self.STATES.ARCHIVED
        
    def delete(self, request=None, cascade=True):
        if self.is_deletable:
            if not cascade:
                self.sample_set.all().update(group=None)
            for obj in self.sample_set.all():
                obj.group = None
                obj.delete(request=request)
            super(Group, self).delete(request=request)

    def archive(self, request=None):
        for obj in self.sample_set.exclude(status__exact=Sample.STATES.ARCHIVED):
            obj.archive(request=request)
        super(Group, self).archive(request=request)
        
    def json_dict(self):
        """ Returns a json dictionary of the Runlist """
        json_info = {
            'project_id': self.project.pk,
            'project_name': self.project.name,
            'id': self.pk,
            'name': self.name,
            'plan': Group.EXP_PLANS[self.plan],
            'absorption_edge': self.absorption_edge,
            'energy': self.energy,
            'type': Group.EXP_TYPES[self.kind],
            'comments': self.comments,
            'samples': [sample.pk for sample in self.sample_set.filter(Q(collect_status__exact=False))],
            'best_sample': self.best_sample()
        }
        return json_info
        
     
class Sample(LimsBaseClass):
    HELP = {
        'cascade': 'datasets and results',
        'cascade_help': 'All associated datasets and results will be left without a sample',
        'name': "Avoid using spaces or special characters in sample names",
        'barcode': "If there is a datamatrix code on sample, please scan or input the value here",
        'comments': 'You can use restructured text formatting in this field',
        'container_location': 'This field is required only if a container has been selected',
        'group': 'This field is optional here.  Samples can also be added to a group on the groups page.',
        'container': 'This field is optional here.  Samples can also be added to a container on the containers page.',
    }
    barcode = models.SlugField(null=True, blank=True)
    container = models.ForeignKey(Container, null=True, blank=True)
    location = models.CharField(max_length=10, null=True, blank=True, verbose_name='port')
    comments = models.TextField(blank=True, null=True)
    collect_status = models.BooleanField(default=False)
    priority = models.IntegerField(null=True, blank=True)
    group = models.ForeignKey(Group, null=True, blank=True)

    class Meta:
        unique_together = (
            ("project", "container", "location"),
        )
        ordering = ['priority', 'container__name', 'location', 'name']

    def identity(self):
        return 'XT%03d%s' % (self.id, self.created.strftime(IDENTITY_FORMAT))
    identity.admin_order_field = 'pk'

    def dewar(self):
        try:
            return self.container.parent.parent.dewar_set.first().beamline
        except:
            return self.container.parent and self.container.parent.dewar_set.first() and (self.container.parent.dewar_set.first().beamline)

    def container_and_location(self):
        return "{} - {}".format(self.container.name, self.location)
    container_and_location.short_description = "Container Location"

    def port(self):
        if not self.dewar():
            return ""
        return '{}{}{}'.format(self.container.parent and self.container.parent.location or "", self.container.location or "", self.location)

    def is_editable(self):
        return True

    def delete(self, request=None, cascade=True):
        if self.is_deletable:
            if self.group:
                if self.group.sample_set.count() == 1:
                    self.group.delete(request=request, cascade=False)
            super(Sample, self).delete(request=request)

    def json_dict(self):
        return {
            'container': self.container.name,
            'container_type': self.container.kind.name,
            'group': self.group.name,
            'id': self.pk,
            'name': self.name,
            'barcode': self.barcode,
            'priority': self.priority if self.priority else 1,
            'comments': self.comments,
            'location': self.location,
            'port': self.port(),
        }


def parse_frames(frame_string):
    frames = []
    if frame_string:
        for w in frame_string.split(','):
            v = map(int, w.split('-'))
            if len(v) == 2:
                frames.extend(range(v[0], v[1]+1))
            elif len(v) == 1:
                frames.extend(v)
    return frames


def frame_ranges(frame_list):
    for a, b in itertools.groupby(enumerate(frame_list), lambda (x, y): y - x):
        b = list(b)
        yield b[0][1], b[-1][1]


class FrameField(models.CharField):
    description = _("List of frames")

    def get_prep_value(self, value):
        if value is None or isinstance(value, basestring):
            return value
        else:
            try:
                value = isinstance(json.loads(value), list) and json.loads(value)
            except:
                pass
            if isinstance(value, list):
                val_str = ",".join([r[0] == r[1] and "{}".format(r[0]) or "{}-{}".format(r[0], r[1])
                                    for r in list(frame_ranges(value))])
                return val_str
        return value

    def from_db_value(self, value, expression, connection, context):
        if value is None or isinstance(value, list):
            return value
        if isinstance(value, basestring):
            return parse_frames(value)
        return value


class DataQueryset(models.QuerySet):
    def screening(self):
        return self.filter(kind='MX_SCREEN')

    def collection(self):
        return self.filter(kind='MX_DATA')


class DataManager(models.Manager.from_queryset(DataQueryset)):
    use_for_related_fields = True


class Data(DataBaseClass):
    DATA_TYPES = Choices(
        ('MX_SCREEN', 'MX Screening'),
        ('MX_DATA', 'MX Dataset'),
        ('XRD_DATA', 'XRD Dataset'),
        ('RASTER', 'Raster'),
        ('XAS_SCAN', 'XAS Scan'),
        ('XRF_SCAN', 'XRF Scan'),
        ('MAD_SCAN', 'MAD Scan'),
    )
    METADATA = {
        DATA_TYPES.MX_SCREEN:  ['delta_angle', 'start_angle', 'resolution', 'detector', 'detector_size', 'pixel_size',
                                'beam_x', 'beam_y', 'two_theta'],
        DATA_TYPES.MX_DATA: ['delta_angle', 'start_angle', 'resolution', 'detector', 'detector_size', 'pixel_size',
                             'beam_x', 'beam_y', 'two_theta'],
        DATA_TYPES.MAD_SCAN: ['roi', 'edge'],
        DATA_TYPES.XRF_SCAN: [],
        DATA_TYPES.RASTER: ['grid_points', 'grid_origin', 'start_angle', 'delta_angle', 'detector_type',
                            'detector_size', 'pixel_size', 'beam_x', 'beam_y','inverse_beam'],
        DATA_TYPES.XRD_DATA: [],
    }
    group = models.ForeignKey(Group, null=True, blank=True)
    sample = models.ForeignKey(Sample, null=True, blank=True)
    session = models.ForeignKey(Session, null=True, blank=True)
    first_frame = models.IntegerField(default=1)
    file_name = models.CharField(max_length=200, null=True, blank=True)
    frames = FrameField(max_length=200, null=True, blank=True)
    exposure_time = models.FloatField(null=True, blank=True)
    attenuation = models.FloatField()
    energy = models.DecimalField(decimal_places=4, max_digits=6)
    beamline = models.ForeignKey(Beamline)
    beam_size = models.FloatField(null=True, blank=True)
    url = models.CharField(max_length=200)
    kind = models.CharField('Data type', choices=DATA_TYPES, default=DATA_TYPES.MX_SCREEN, max_length=20)
    download = models.BooleanField(default=False)
    meta_data = JSONField(default={})

    objects = DataManager()

    def identity(self):
        return 'DA%03d%s' % (self.id, self.created.strftime(IDENTITY_FORMAT))
    identity.admin_order_field = 'pk'

    # need a method to determine how many frames are in item
    def num_frames(self):
        return len(self.frames)

    def frame_sets(self):
        if isinstance(self.frames, list):
            val_str = ",".join([r[0] == r[1] and "{}".format(r[0]) or "{}-{}".format(r[0], r[1])
                                for r in list(frame_ranges(self.frames))])
            return val_str
        return self.frames

    def can_download(self):
        return (not RESTRICTED_DOWNLOADS) or self.download

    def __unicode__(self):
        return '%s (%d)' % (self.name, self.num_frames())

    def report(self):
        return self.reports.first()

    def result(self):
        if len(self.result_set.all()) is 1:
            return self.result_set.all()[0]
        return False

    def wavelength(self):
        _h = 4.13566733e-15  # eV.s
        _c = 299792458e10  # A/s
        if float(self.energy) == 0.0:
            return 0.0
        return (_h * _c) / (float(self.energy) * 1000.0)

    def total_angle(self):
        return float(self.meta_data.get('delta_angle', 0)) * self.num_frames()
        
    def file_extension(self):
        detector = 'detector' in self.meta_data and self.meta_data['detector'] or ""
        return '.cbf' if 'PILATUS' in detector else '.img'

    def start_angle_for_frame(self, frame):
        return (frame - self.first_frame) * self.delta_angle + self.start_angle 

    def archive(self, request=None):
        for obj in self.result_set.all():
            if obj.status not in [GLOBAL_STATES.ARCHIVED, GLOBAL_STATES.TRASHED]:
                obj.archive(request=request)
        super(Data, self).archive(request=request)

    def trash(self, request=None):
        for obj in self.result_set.all():
            if obj.status not in [GLOBAL_STATES.TRASHED]:
                obj.trash(request=request)
        super(Data, self).trash(request=request)

    class Meta:
        verbose_name = 'Dataset'


class AnalysisReport(DataBaseClass):
    kind = models.CharField(max_length=100)
    group = models.ForeignKey(Group, null=True, blank=True)
    sample = models.ForeignKey(Sample, null=True, blank=True)
    score = models.FloatField()
    data = models.ForeignKey(Data, related_name="reports")
    result = models.ForeignKey('Result', related_name="reports")
    details = JSONField()

    class Meta:
        ordering = ['-score']

    def identity(self):
        return 'AR%03d%s' % (self.id, self.created.strftime(IDENTITY_FORMAT))
    identity.admin_order_field = 'pk'


class Result(DataBaseClass):
    RESULT_TYPES = Choices(
        (0, 'SCREENING', 'Screening'),
        (1, 'COLLECTION', 'Collection'),
    )
    group = models.ForeignKey(Group, null=True, blank=True)
    sample = models.ForeignKey(Sample, null=True, blank=True)
    data = models.ForeignKey(Data)
    score = models.FloatField()
    space_group = models.ForeignKey(SpaceGroup)
    cell_a = models.FloatField('a')
    cell_b = models.FloatField('b')
    cell_c = models.FloatField('c')
    cell_alpha = models.FloatField('alpha')
    cell_beta = models.FloatField('beta')
    cell_gamma = models.FloatField('gamma')
    resolution = models.FloatField()
    reflections = models.IntegerField()
    unique = models.IntegerField()
    multiplicity = models.FloatField()
    completeness = models.FloatField()
    mosaicity = models.FloatField()
    wavelength = models.FloatField(blank=True, null=True)
    i_sigma = models.FloatField('I/Sigma')
    r_meas = models.FloatField('R-meas')
    r_mrgdf = models.FloatField('R-mrgd-F', blank=True, null=True)
    cc_half = models.FloatField('CC-1/2', blank=True, null=True)
    sigma_spot = models.FloatField('Sigma(spot)')
    sigma_angle = models.FloatField('Sigma(angle)')
    ice_rings = models.IntegerField()
    url = models.CharField(max_length=200)
    kind = models.IntegerField('Result type', choices=RESULT_TYPES)
    details = JSONField()

    def identity(self):
        return 'RT%03d%s' % (self.id, self.created.strftime(IDENTITY_FORMAT))
    identity.admin_order_field = 'pk'

    def archive(self, request=None):
        super(Result, self).archive(request=request)
        self.data.archive(request=request)

    def trash(self, request=None):
        super(Result, self).trash(request=request)
        self.data.trash(request=request)

    def frames(self):
        return self.data and self.data.num_frames() or ""

    class Meta:
        ordering = ['-score']
        verbose_name = 'Analysis Report'


class ScanResult(DataBaseClass):
    XRF_COLOR_LIST = ['#800080', '#FF0000', '#008000',
                      '#FF00FF', '#800000', '#808000',
                      '#008080', '#00FF00', '#000080',
                      '#00FFFF', '#0000FF', '#000000',
                      '#800040', '#BD00BD', '#00FA00',
                      '#800000', '#FA00FA', '#00BD00',
                      '#008040', '#804000', '#808000',
                      '#408000', '#400080', '#004080']
    SCAN_TYPES = Choices(
        (0, 'MAD_SCAN', 'MAD Scan'),
        (1, 'EXCITATION_SCAN', 'Excitation Scan'),
    )
    group = models.ForeignKey(Group, null=True, blank=True)
    sample = models.ForeignKey(Sample, null=True, blank=True)
    edge = models.CharField(max_length=20)
    details = JSONField()
    kind = models.IntegerField('Scan type', choices=SCAN_TYPES)
    
    energy = models.FloatField(null=True, blank=True)
    exposure_time = models.FloatField(null=True, blank=True)
    attenuation = models.FloatField(null=True, blank=True)
    beamline = models.ForeignKey(Beamline)
    
    def identity(self):
        return 'SC%03d%s' % (self.id, self.created.strftime(IDENTITY_FORMAT))
    identity.admin_order_field = 'pk'
    
    def summarize_lines(self):
        name_dict = {
            'L1M2,3,L2M4': 'L1,2M',
            'L1M3,L2M4': 'L1,2M',       
            'L1M,L2M4': 'L1,2M',
        }
        peaks = self.details['peaks']
        if peaks is None:
            return
        data = peaks.items()
        line_data = []
        for el in data:
            line_data.append(el)
            
        def join(a, b):
            if a == b:
                return [a]
            if abs(b[1]-a[1]) < 0.200:
                if a[0][:-1] == b[0][:-1]:
                    nm = b[0][:-1]
                else:
                    nm = '%s,%s' % (a[0], b[0])
                nm = name_dict.get(nm, nm)
                ht = (a[2] + b[2])
                pos = (a[1]*a[2] + b[1]*b[2])/ht
                return [(nm, round(pos, 4), round(ht, 2))]
            else:
                return [a, b]
            
        new_lines = []
        for entry in line_data:
            new_data = [entry[1][1][0]]
            for edge in entry[1][1]:
                old = new_data[-1]
                _new = join(old, edge)
                new_data.remove(old)
                new_data.extend(_new)
            new_lines.append((entry[0], new_data, self.XRF_COLOR_LIST[line_data.index(entry)]))
        
        return new_lines


class ActivityLogManager(models.Manager):
    def log_activity(self, request, obj, action_type, description=''):
        e = self.model()
        if obj is None:
            try:
                project = request.user
                e.project_id = project.pk
            except Project.DoesNotExist:
                pass

        else:
            if getattr(obj, 'project', None) is not None:
                e.project_id = obj.project.pk
            elif getattr(request, 'project', None) is not None:
                e.project_id = request.project.pk
            elif isinstance(obj, Project):
                e.project_id = obj.pk

            e.object_id = obj.pk
            e.affected_item = obj
            e.content_type = ContentType.objects.get_for_model(obj)
        try:
            e.user = request.user
            e.user_description = request.user.username
        except:
            e.user_description = "System"
        e.ip_number = request.META['REMOTE_ADDR']
        e.action_type = action_type
        e.description = description
        if obj is not None:
            e.object_repr = '%s: %s' % (obj.__class__.__name__.upper(), obj)
        else:
            e.object_repr = 'N/A'
        e.save()

    def last_login(self, request):
        logs = self.filter(user__exact=request.user, action_type__exact=ActivityLog.TYPE.LOGIN)
        if logs.count() > 1:
            return logs[1]
        else:
            return None


class ActivityLog(models.Model):
    TYPE = Choices(
        (0, 'LOGIN', 'Login'),
        (1, 'LOGOUT', 'Logout'),
        (2, 'TASK', 'Task'),
        (3, 'CREATE', 'Create'),
        (4, 'MODIFY', 'Modify'),
        (5, 'DELETE', 'Delete'),
        (6, 'ARCHIVE', 'Archive')
    )
    created = models.DateTimeField('Date/Time', auto_now_add=True, editable=False)
    project = models.ForeignKey(Project, blank=True, null=True)
    user = models.ForeignKey(Project, blank=True, null=True, related_name='activities')
    user_description = models.CharField('User name', max_length=60, blank=True, null=True)
    ip_number = models.GenericIPAddressField('IP Address')
    object_id = models.PositiveIntegerField(blank=True, null=True)
    content_type = models.ForeignKey(ContentType, blank=True, null=True)
    affected_item = GenericForeignKey('content_type', 'object_id')
    action_type = models.IntegerField(choices=TYPE)
    object_repr = models.CharField('Entity', max_length=200, blank=True, null=True)
    description = models.TextField(blank=True)
    
    objects = ActivityLogManager()
    
    class Meta:
        ordering = ('-created',)
    
    def __unicode__(self):
        return str(self.created)


@receiver(populate_user)
def populate_user_handler(sender, user, ldap_user, **kwargs):
    user_uids = set(map(int, ldap_user.attrs.get('gidnumber', [])))
    admin_uids = set(getattr(settings, 'LDAP_ADMIN_UIDS', []))
    if user_uids & admin_uids:
        user.is_superuser = True
        user.is_staff = True
    if not Project.objects.filter(name=user.username).exists():
        Project.objects.create(
            user=user, name=user.username, contact_person=user.get_full_name(),
        )


@receiver(post_delete, sender=Project)
def on_project_delete(sender, instance, **kwargs):
    if instance.user.pk:
        instance.user.delete()
    slap.del_user(instance.name)
