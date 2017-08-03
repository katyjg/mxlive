from django.conf import settings
from django.utils.translation import ugettext as _
#from django.contrib.auth import get_user_model
from django.contrib.contenttypes.fields import GenericForeignKey
from django.contrib.contenttypes.models import ContentType
from django.db import models
from django.db.models import Q
from django.utils import dateformat, timezone
from django.contrib.auth.models import AbstractUser
from jsonfield.fields import JSONField
import copy
import hashlib
import string
from model_utils import Choices

IDENTITY_FORMAT = '-%y%m'
RESUMBITTED_LABEL = 'Resubmitted_'
RESTRICTED_DOWNLOADS = getattr(settings, 'RESTRICTED_DOWNLOADS', False)
#User = get_user_model()

def cassette_loc_repr(pos):
    return "ABCDEFGHIJKL"[pos/8]+str(1+pos%8)

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
    energy_lo = models.FloatField(default=4.0)
    energy_hi = models.FloatField(default=18.5)
    contact_phone = models.CharField(max_length=60)

    def __unicode__(self):
        return self.name

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

    created = models.DateTimeField('date created', auto_now_add=True, editable=False)
    modified = models.DateTimeField('date modified',auto_now=True, editable=False)
    updated = models.BooleanField(default=False)    
    
    def identity(self):
        return 'PR%03d%s' % (self.id, self.created.strftime(IDENTITY_FORMAT))
    identity.admin_order_field = 'pk'
        
    def __unicode__(self):
        return self.name

    def is_editable(self):
        return True

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
        return Shipment.objects.filter(project__exact=self).filter(created__year=2013).count()

    def delete(self, *args, **kwargs):
        self.user.delete()
        return super(self.__class__, self).delete(*args, **kwargs)
    
    class Meta:
        verbose_name = "Project Account"

class Session(models.Model):
    project = models.ForeignKey(Project)
    beamline = models.ForeignKey(Beamline)
    start_time = models.DateTimeField(null=False, blank=False)
    end_time = models.DateTimeField(null=False, blank=False)
    comments = models.TextField()
    
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
        STATES.SENT: [STATES.ON_SITE],
        STATES.ON_SITE: [STATES.RETURNED],
        STATES.LOADED: [STATES.ON_SITE],
        STATES.RETURNED: [STATES.ARCHIVED],
        STATES.ACTIVE: [STATES.PROCESSING, STATES.COMPLETE, STATES.REVIEWED, STATES.ARCHIVED],
        STATES.PROCESSING: [STATES.COMPLETE, STATES.REVIEWED, STATES.ARCHIVED],
        STATES.COMPLETE: [STATES.ACTIVE, STATES.PROCESSING, STATES.REVIEWED, STATES.ARCHIVED],
        STATES.REVIEWED: [STATES.ARCHIVED],
    }

    project = models.ForeignKey(Project)
    name = models.CharField(max_length=60)
    staff_comments = models.TextField(blank=True, null=True)
    created = models.DateTimeField('date created', auto_now_add=True, editable=False)
    modified = models.DateTimeField('date modified',auto_now=True, editable=False)

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

    def delete(self, request=None, cascade=True):
        message = '%s deleted' % (self._meta.verbose_name)
        if request is not None:
            ActivityLog.objects.log_activity(request, self, ActivityLog.TYPE.DELETE, message)
        super(LimsBaseClass, self).delete()

    def archive(self, request=None):
        if self.is_closable():
            self.change_status(self.STATES.ARCHIVED)
            message = '%s archived' % (self._meta.verbose_name)
            if request is not None:
                ActivityLog.objects.log_activity(request, self, ActivityLog.TYPE.ARCHIVE, message)

    def send(self, request=None):
        self.change_status(self.STATES.SENT)       
        message = '%s sent to CLS' % (self._meta.verbose_name)
        if request is not None:
            ActivityLog.objects.log_activity(request, self, ActivityLog.TYPE.MODIFY, message)

    def receive(self, request=None):
        self.change_status(self.STATES.ON_SITE) 
        message = '%s received at CLS' % (self._meta.verbose_name)
        if request is not None:
            ActivityLog.objects.log_activity(request, self, ActivityLog.TYPE.MODIFY, message)

    def load(self, request=None):
        self.change_status(self.STATES.LOADED)    
        message = '%s loaded into automounter' % (self._meta.verbose_name)
        if request is not None:
            ActivityLog.objects.log_activity(request, self, ActivityLog.TYPE.MODIFY, message)

    def unload(self, request=None):
        self.change_status(self.STATES.ON_SITE)   
        message = '%s unloaded from automounter' % (self._meta.verbose_name)
        if request is not None:
            ActivityLog.objects.log_activity(request, self, ActivityLog.TYPE.MODIFY, message)

    def returned(self, request=None):
        self.change_status(self.STATES.RETURNED)     
        message = '%s returned to user' % (self._meta.verbose_name)
        if request is not None:
            ActivityLog.objects.log_activity(request, self, ActivityLog.TYPE.MODIFY, message)

    def trash(self, request=None):
        self.change_status(self.STATES.TRASHED)     
        message = '%s sent to trash' % (self._meta.verbose_name)
        if request is not None:
            ActivityLog.objects.log_activity(request, self, ActivityLog.TYPE.MODIFY, message)

    def change_status(self, status):
        if status == self.status:
            return
        if status not in self.TRANSITIONS[self.status]:
            raise ValueError("Invalid transition on '%s.%s':  '%s' -> '%s'" % (self.__class__, self.pk, self.STATES[self.status], self.STATES[status]))
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

    def is_trashable(self):
        return True

    def update_states(self):
        return

    class Meta:
        abstract = True

class Shipment(ObjectBaseClass):
    HELP = {
        'name': "This should be an externally visible label",
        'carrier': "Please select the carrier company. To change shipping companies, edit your profile on the Project Home page.",
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

    def _Carrier(self):
        return self.carrier and self.carrier.name or None
    _Carrier.admin_order_field = 'carrier__name'

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
    
    def is_pdfable(self):
        return self.is_sendable() or self.status >= self.STATES.SENT
    
    def is_xlsable(self):
        # can generate spreadsheet as long as there are no orphan samples with no group)
        return not Sample.objects.filter(container__in=self.container_set.all()).filter(group__exact=None).exists()
    
    def is_returnable(self):
        return self.status == self.STATES.ON_SITE 

    def has_labels(self):
        return self.status <= self.STATES.SENT and (self.num_containers() or self.component_set.filter(label__exact=True))

    def item_labels(self):
        return self.component_set.filter(label__exact=True)

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
        return self.project.sample_set.filter(container__shipment__exact=self).filter(Q(pk__in=self.project.data_set.values('sample')) | Q(pk__in=self.project.result_set.values('sample'))).exists()
 
    def add_component(self):
        return self.status <= self.STATES.SENT
 
    def label_hash(self):
        # use dates of project, shipment, and each container within to determine
        # when contents were last changed
        txt = str(self.project) + str(self.project.modified) + str(self.modified)
        for container in self.container_set.all():
            txt += str(container.modified)
        h = hashlib.new('ripemd160') # no successful collision attacks yet
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
    
    def setup_default_group(self, data=None):
        """ If there are unassociated samples in the project, creates a default group and associates the
            samples
        """
        unassociated_samples = self.project.sample_set.filter(group__isnull=True)
        if unassociated_samples:
            exp_name = '%s auto' % dateformat.format(timezone.now(), 'M jS P')
            group = Group(project=self.project, name=exp_name)
            group.save()
            for unassociated_sample in unassociated_samples:
                unassociated_sample.group = group
                unassociated_sample.save()

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
        for obj in self.container_set.all():
            obj.receive(request=request)
        super(Shipment, self).receive(request=request)

    def send(self, request=None):
        if self.is_sendable():
            self.date_shipped = timezone.now()
            self.setup_default_group()
            self.save()
            for obj in self.container_set.all():
                obj.send(request=request)
            super(Shipment, self).send(request=request)

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

class Component(ObjectBaseClass):
    HELP = {
        'label': 'If this box is checked, an additional label for this item will be printed along with dewar labels.',
        'name': 'Components can be hard drives, tools, or any other items you are including in your shipment.'
    }
    shipment = models.ForeignKey(Shipment)
    description = models.CharField(max_length=100)
    label = models.BooleanField()
    
    def identity(self):
        return 'CM%03d%s' % (self.id, self.created.strftime(IDENTITY_FORMAT))
    identity.admin_order_field = 'pk'
    
    def barcode(self):
        return "CM%04d-%04d" % (self.id, self.shipment.id)
        


class ContainerType(models.Model):
    TYPE = Choices(
        (0, 'CASSETTE', 'Cassette'),
        (1, 'UNI_PUCK','Uni-Puck'),
        (2, 'CANE','Cane'),
        (3, 'BASKET','Basket')
    )
    STATES = Choices(
        (0, 'PENDING', _('Pending')),
        (1, 'LOADED', _('Loaded')),
    )
    TRANSITIONS = {
        STATES.PENDING: [STATES.LOADED],
        STATES.LOADED: [STATES.PENDING],
    }
    name = models.CharField(max_length=20)
    kind = models.IntegerField('type', choices=TYPE)
    container_locations = models.ManyToManyField("ContainerLocation", blank=True)
    layout = JSONField(null=True, blank=True)
    envelope = models.CharField(max_length=200, blank=True)

    def __unicode__(self):
        return self.get_kind_display()


class ContainerLocation(models.Model):
    name = models.CharField(max_length=5)
    accepts = models.ManyToManyField(ContainerType, blank=True, related_name="locations")

    def __unicode__(self):
        return self.name

class Container(LoadableBaseClass):
    TYPE = Choices(
        (0, 'CASSETTE', 'Cassette'),
        (1, 'UNI_PUCK','Uni-Puck'),
        (2, 'CANE','Cane'),
        (3, 'BASKET','Basket'),
        (4, 'ADAPTOR','Adaptor')
    )
    HELP = {
        'name': "An externally visible label on the container. If there is a barcode on the container, please scan it here",
        'capacity': "The maximum number of samples this container can hold",
        'cascade': 'samples (along with groups, datasets and results)',
        'cascade_help': 'All associated samples will be left without a container'
    }
    kind = models.ForeignKey(ContainerType, blank=False, null=False)
    shipment = models.ForeignKey(Shipment, blank=True, null=True)
    comments = models.TextField(blank=True, null=True)
    priority = models.IntegerField(default=0)

    def identity(self):
        return 'CN%03d%s' % (self.id, self.created.strftime(IDENTITY_FORMAT))
    identity.admin_order_field = 'pk'

    class Meta:
        unique_together = (
            ("project", "name", "shipment"),
        )

    def barcode(self):
        return self.name

    def num_samples(self):
        return self.sample_set.count()
    
    def is_assigned(self):
        return self.shipment is not None

    def capacity(self):
        _cap = {
            self.TYPE.CASSETTE : 96,
            self.TYPE.UNI_PUCK : 16,
            self.TYPE.CANE : 6,
            self.TYPE.BASKET: 10,
            None : 0,
        }
        return _cap[self.kind.kind]

    def get_form_field(self):
        return 'container'

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
    
    def contains_group(self, group):
        """
        Checks if the specified group is in the container.
        """
        for sample in self.sample_set.all():
            for sample_group in sample.group_set.all():
                if sample_group == group:
                    return True
        return False
    
    def contains_groups(self, group_list):
        for group in group_list:
            if self.contains_group(group):
                return True
        return False
    
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
    
    def get_location_choices(self):
        vp = self.valid_locations()
        return tuple([(a,a) for a in vp])
            
    def valid_locations(self):
        if self.kind == self.TYPE.CASSETTE:
            all_positions = []
            for x in range(self.capacity()//12):
                num = str(1+x%8)
                position = ["ABCDEFGHIJKL"[y]+str(x+1) for y in range(self.capacity()//8) ]
                for item in position:
                    all_positions.append(item)
        else:
            all_positions = [ str(x+1) for x in range(self.capacity()) ]
        return all_positions
    
    def location_is_valid(self, loc):
        return loc in self.valid_locations()
    
    def location_is_available(self, loc, id=None):
        occupied_positions = [xtl.container_location for xtl in self.sample_set.all().exclude(pk=id) ]
        return loc not in occupied_positions
    
    def location_and_sample(self):
        retval = []
        xtalset = self.sample_set.all()
        for location in self.valid_locations():
            xtl = None
            for sample in xtalset:
                if sample.container_location == location:
                    xtl = sample
            retval.append((location, xtl))
        return retval

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

    def send(self, request=None):
        for obj in self.sample_set.all():
            obj.send(request=request)
        super(Container, self).send(request=request)

    def receive(self, request=None):
        for obj in self.sample_set.all():
            obj.receive(request=request)
        super(Container, self).receive(request=request)

    def load(self, request=None):
        for obj in self.sample_set.all(): obj.load(request=request)
        super(Container, self).load(request=request)

    def unload(self, request=None):
        for obj in self.sample_set.all(): obj.unload(request=request)
        super(Container, self).unload(request=request)  

    def returned(self, request=None):
        for obj in self.sample_set.all():
            obj.returned(request=request)
        super(Container, self).returned(request=request)

    def archive(self, request=None):
        for obj in self.sample_set.all():
            obj.archive(request=request)
        super(Container, self).archive(request=request)
        
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

class SpaceGroup(models.Model):
    CS_CHOICES = (
        ('a','triclinic'),
        ('m','monoclinic'),
        ('o','orthorombic'),
        ('t','tetragonal'),
        ('h','hexagonal'),
        ('c','cubic'),
    )
    
    LT_CHOICES = (
        ('P','primitive'),
        ('C','side-centered'),
        ('I','body-centered'),
        ('F','face-centered'),
        ('R','rhombohedral'),       
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
        'kind': "If you select SAD or MAD make sure you provide the absorption edge below, otherwise Se-K will be assumed.",
        'plan': "Select the plan which describes your instructions for all samples in this group.",
        'delta_angle': 'If left blank, an appropriate value will be calculated during screening.',
        'total_angle': 'The total angle range to collect.',
        'multiplicity': 'Values entered here take precedence over the specified "Angle Range".',
    }
    EXP_TYPES = Choices(
        (0,'NATIVE','Native'),
        (1,'MAD','MAD'),
        (2,'SAD','SAD'),
    )
    EXP_PLANS = Choices(
        (0,'RANK_AND_COLLECT_BEST','Rank and collect best'),
        (1,'COLLECT_FIRST_GOOD','Collect first good'),
        (2,'SCREEN_AND_CONFIRM','Screen and confirm'),
        (3,'SCREEN_AND_COLLECT','Screen and collect'),
        (4,'JUST_COLLECT','Just collect'),
    )
    TRANSITIONS = copy.deepcopy(LimsBaseClass.TRANSITIONS)
    TRANSITIONS[LimsBaseClass.STATES.DRAFT] = [LimsBaseClass.STATES.ACTIVE]

    status = models.IntegerField(choices=STATUS_CHOICES, default=LimsBaseClass.STATES.DRAFT)
    shipment = models.ForeignKey(Shipment, null=True)
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

    def identity(self):
        return 'EX%03d%s' % (self.id, self.created.strftime(IDENTITY_FORMAT))    
    identity.admin_order_field = 'pk'

    def accept(self):
        return "sample"

    def num_samples(self):
        return self.sample_set.count()
        
    def get_form_field(self):
        return 'group'

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
            diff = self.sample_set.count() - self.sample_set.filter(status__in=[Sample.STATES.ON_SITE, Sample.STATES.LOADED]).count()
            if diff:
                errors.append("%i samples have not arrived on-site." % diff)
        return errors

    def is_processing(self):
        return self.sample_set.filter(Q(pk__in=self.project.data_set.values('sample')) | Q(pk__in=self.project.result_set.values('sample'))).exists()

    def is_reviewable(self):
        return self.status != Group.STATES.REVIEWED
    
    def is_closable(self):
        return self.sample_set.all().exists() and not self.sample_set.exclude(status__in=[Sample.STATES.RETURNED, Sample.STATES.ARCHIVED]).exists() and self.status != Group.STATES.ARCHIVED
        
    def is_complete(self):
        """
        Checks group type, and depending on type, determines if it's fully completed or not.
        Updates Exp Status if considered complete. 
        """
        if self.sample_set.filter(Q(screen_status__exact=Sample.EXP_STATES.PENDING) | Q(collect_status__exact=Sample.EXP_STATES.PENDING)).exists():
            return False
        if self.plan == Group.EXP_PLANS.RANK_AND_COLLECT_BEST or self.plan == Group.EXP_PLANS.COLLECT_FIRST_GOOD:
            # complete if all samples are "screened" (or "ignored") and at least 1 is "collected"
            if not self.sample_set.filter(collect_status__exact=Sample.EXP_STATES.COMPLETED).exists():
                if not self.sample_set.filter(collect_status__exact=Sample.EXP_STATES.NOT_REQUIRED).exists():
                    self.add_comments('Unable to collect a dataset for any sample in this group.')
                    return True
                return False
        elif self.plan == Group.EXP_PLANS.SCREEN_AND_CONFIRM:
            # complete if all samples are "screened" (or "ignored")
            if not self.sample_set.exclude(screen_status__exact=Sample.EXP_STATES.IGNORE).exists():
                self.add_comments('Unable to screen any samples in this group.')
        elif self.plan == Group.EXP_PLANS.SCREEN_AND_COLLECT or self.plan == Group.EXP_PLANS.JUST_COLLECT:
            # complete if all samples are "screened" or "collected"
            if not self.sample_set.exclude(collect_status__exact=Sample.EXP_STATES.IGNORE).exists():
                self.add_comments('Unable to collect a dataset for any sample in this group.')
        else:
            # should never get here.
            raise Exception('Invalid plan')  
        return True
        
    def delete(self, request=None, cascade=True):
        if self.is_deletable:
            if not cascade:
                self.sample_set.all().update(group=None)
            for obj in self.sample_set.all():
                obj.group = None
                obj.delete(request=request)
            super(Group, self).delete(request=request)

    def review(self, request=None):
        super(Group, self).change_status(LimsBaseClass.STATES.REVIEWED)
        message = '%s reviewed' % (self._meta.verbose_name)
        if request is not None:
            ActivityLog.objects.log_activity(request, self, ActivityLog.TYPE.MODIFY, message)

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
            'r_meas': self.r_meas,
            'i_sigma': self.i_sigma,
            'absorption_edge': self.absorption_edge,
            'energy': self.energy,
            'type': Group.EXP_TYPES[self.kind],
            'resolution': self.resolution,
            'delta_angle': self.delta_angle,
            'total_angle': self.total_angle,
            'multiplicity': self.multiplicity,
            'comments': self.comments,
            'samples': [sample.pk for sample in self.sample_set.filter(Q(screen_status__exact=Sample.EXP_STATES.PENDING) | Q(collect_status__exact=Sample.EXP_STATES.PENDING))],
            'best_sample': self.best_sample()
        }
        return json_info
        
     
class Sample(LoadableBaseClass):
    HELP = {
        'cascade': 'datasets and results',
        'cascade_help': 'All associated datasets and results will be left without a sample',
        'name': "Give the sample a name by which you can recognize it. Avoid using spaces or special characters in sample names",
        'barcode': "If there is a datamatrix code on sample, please scan or input the value here",
        'pin_length': "18 mm pins are standard. Please make sure you discuss other sizes with Beamline staff before sending the sample!",
        'comments': 'You can use restructured text formatting in this field',
        'container_location': 'This field is required only if a container has been selected',
        'group': 'This field is optional here.  Samples can also be added to a group on the groups page.',
        'container': 'This field is optional here.  Samples can also be added to a container on the containers page.',
    }
    EXP_STATES = Choices(
        (0, 'NOT_REQUIRED','Not Required'),
        (1, 'PENDING','Pending'),
        (2, 'COMPLETED','Completed'),
        (3, 'IGNORE','Ignore'),
    )
    barcode = models.SlugField(null=True, blank=True)
    pin_length = models.IntegerField(default=18)
    loop_size = models.FloatField(null=True, blank=True)
    container = models.ForeignKey(Container, null=True, blank=True)
    container_location = models.CharField(max_length=10, null=True, blank=True, verbose_name='port')
    comments = models.TextField(blank=True, null=True)
    collect_status = models.IntegerField(choices=EXP_STATES, default=EXP_STATES.NOT_REQUIRED)
    screen_status = models.IntegerField(choices=EXP_STATES, default=EXP_STATES.NOT_REQUIRED)
    priority = models.IntegerField(null=True, blank=True)
    group = models.ForeignKey(Group, null=True, blank=True)

    class Meta:
        unique_together = (
            ("project", "container", "container_location"),
        )
        ordering = ['priority','container','container_location']

    def identity(self):
        return 'XT%03d%s' % (self.id, self.created.strftime(IDENTITY_FORMAT))
    identity.admin_order_field = 'pk'

    def _Container(self):
        return self.container and self.container.name or None
    _Container.admin_order_field = 'container__name'
    
    def get_data_set(self):
        return self.data_set.filter(**self.project.get_archive_filter())

    def get_result_set(self):
        return self.result_set.filter(**self.project.get_archive_filter())
    
    def get_scanresult_set(self):
        return self.scanresult_set.filter(**self.project.get_archive_filter())

    def best_screening(self):
        info = {}
        results = self.get_result_set().filter(kind__exact=Result.RESULT_TYPES.SCREENING).order_by('-score')
        if len(results) > 0:
            info['report'] = results[0]
            info['data'] = info['report'].data
        else:
            data = self.get_data_set().filter(kind__exact=Data.DATA_TYPES.SCREENING).order_by('-created')
            if len(data) > 0:
                info['data'] = data[0]
        return info
    
    def best_collection(self):
        info = {}
        results = self.get_result_set().filter(kind__exact=Result.RESULT_TYPES.COLLECTION).order_by('-score')
        if len(results) > 0:
            info['report'] = results[0]
            info['data'] = info['report'].data
        else:
            data = self.get_data_set().filter(kind__exact=Data.DATA_TYPES.COLLECTION).order_by('-created')
            if len(data) > 0:
                info['data'] = data[0]
        return info

    def best_overall(self):
        if 'report' in self.best_collection():
            return self.best_collection()
        return self.best_screening()

    def is_clonable(self):
        return True

    def is_complete(self):
        return (self.screen_status != Sample.EXP_STATES.PENDING and self.collect_status != Sample.EXP_STATES.PENDING and self.status > Sample.STATES.DRAFT) or self.collect_status == Sample.EXP_STATES.COMPLETED
    
    def is_started(self):
        msg = str()
        data = Data.objects.filter(sample__exact=self)
        result = Result.objects.filter(sample__exact=self)
        scan = ScanResult.objects.filter(sample__exact=self)
        types = [Data.DATA_TYPES, Result.RESULT_TYPES, ScanResult.SCAN_TYPES]
        for i, set in enumerate([data, result, scan]):
            if set.exists():
                s0 = set.filter(kind=0).count() and '%i %s' % (set.filter(kind=0).count(), types[i][0]) or ''
                s1 = set.filter(kind=1).count() and '%i %s' % (set.filter(kind=1).count(), types[i][1]) or ''
                if s1 or s0:
                    msg += '%s%s%s %s<br>' % (s0, (s0 and s1) and '/' or '', s1, set[0].__class__.__name__)
        return msg
    
    def delete(self, request=None, cascade=True):
        if self.is_deletable:
            if self.group:
                if self.group.sample_set.count() == 1:
                    self.group.delete(request=request, cascade=False)
            obj_list = []
            for obj in self.data_set.all(): obj_list.append(obj)
            for obj in self.result_set.all(): obj_list.append(obj)
            for obj in obj_list:
                obj.sample = None
                obj.save()
                if cascade:
                    obj.trash(request=request)
            super(Sample, self).delete(request=request)

    def send(self, request=None):
        assert self.group
        self.group.change_status(Group.STATES.ACTIVE)
        super(Sample, self).send(request=request)

    def archive(self, request=None):
        super(Sample, self).archive(request=request)
        assert self.group
        if self.group.sample_set and self.group.sample_set.exclude(status__exact=Sample.STATES.ARCHIVED).count() == 0:
            super(Group, self.group).archive(request=request)
        for obj in self.data_set.exclude(status__exact=Data.STATES.ARCHIVED):
            obj.archive(request=request)
            super(Data, obj).archive(request=request)
        for obj in self.result_set.exclude(status__exact=Result.STATES.ARCHIVED):
            obj.archive(request=request)
            super(Result, obj).archive(request=request)

    def change_screen_status(self, status):
        if self.screen_status != status:
            self.screen_status = status
            self.save()

    def change_collect_status(self, status):
        if self.collect_status != status:
            self.collect_status = status
            self.save()

    def json_dict(self):
        if self.group is not None:
            exp_id = self.group.pk
        else:
            exp_id = None
        return {
            'project_id': self.project.pk,
            'container_id': self.container.pk,
            'group_id': exp_id,
            'id': self.pk,
            'name': self.name,
            'barcode': self.barcode,
            'priority': self.priority if self.priority else 1,
            'container_location': self.container_location,
            'comments': self.comments
        }
        
class Data(DataBaseClass):
    DATA_TYPES = Choices(
        (0,'SCREENING','Screening'),
        (1,'COLLECTION','Collection'),
    )
    group = models.ForeignKey(Group, null=True, blank=True)
    sample = models.ForeignKey(Sample, null=True, blank=True)
    resolution = models.FloatField()
    start_angle = models.FloatField()
    delta_angle = models.FloatField()
    first_frame = models.IntegerField(default=1)
    #changed to frame_sets 
    frame_sets = models.CharField(max_length=200)
    exposure_time = models.FloatField()
    two_theta = models.FloatField()
    wavelength = models.FloatField()
    detector = models.CharField(max_length=20)
    detector_size = models.IntegerField()
    pixel_size = models.FloatField()
    beam_x = models.FloatField()
    beam_y = models.FloatField()
    beamline = models.ForeignKey(Beamline)
    url = models.CharField(max_length=200)
    kind = models.IntegerField('Data type', choices=DATA_TYPES, default=DATA_TYPES.SCREENING)
    download = models.BooleanField(default=False)
    
    # need a method to determine how many frames are in item
    def num_frames(self):
        return len(self.get_frame_list())          

    def toggle_download(self, state):
        self.download = state
        self.save()

    def can_download(self):
        return (not RESTRICTED_DOWNLOADS) or self.download

    def get_frame_list(self):
        frame_numbers = []
        wlist = [map(int, w.split('-')) for w in self.frame_sets.split(',')]
        for v in wlist:
            if len(v) == 2:
                frame_numbers.extend(range(v[0],v[1]+1))
            elif len(v) == 1:
                frame_numbers.extend(v) 
        return frame_numbers

    def __unicode__(self):
        return '%s (%d)' % (self.name, self.num_frames())
    
    def score_label(self):
        if len(self.result_set.all()) is 1:
            return self.result_set.all()[0].score
        return False

    def result(self):
        if len(self.result_set.all()) is 1:
            return self.result_set.all()[0]
        return False

    def energy(self):
        if self.wavelength: 
            return 4.13566733e-15 * 299792458e10 / (self.wavelength * 1000) 
        return 0

    def total_angle(self):
        return self.delta_angle * self.num_frames()
        
    def file_extension(self):
        return '.cbf' if 'PILATUS' in self.detector else '.img'

    def generate_image_base(self, frame):
        image_url = settings.IMAGE_PREPEND or ''
        return image_url + "/download/images/%s/%s_%04d%s" % (self.url, self.name, frame, self.file_extension())

    def generate_image_url(self, frame, brightness=None):
        # brightness is assumed to be "nm" "dk" or "lt"
        image_url = self.generate_image_base(frame)
        
        if brightness:
            image_url = '%s-%s.png' % (image_url, brightness)

        return image_url   
    
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

    def update_states(self):
        # check type, and change status accordingly
        if self.sample is not None:
            if self.kind == Result.RESULT_TYPES.SCREENING:
                self.sample.change_screen_status(Sample.EXP_STATES.COMPLETED)
            elif self.kind == Result.RESULT_TYPES.COLLECTION:
                self.sample.change_collect_status(Sample.EXP_STATES.COMPLETED)
        if self.group is not None:
            if self.group.status == Group.STATES.ACTIVE:
                self.group.change_status(Group.STATES.PROCESSING)

    class Meta:
        verbose_name = 'Dataset'

class Result(DataBaseClass):
    RESULT_TYPES = Choices(
        (0,'SCREENING','Screening'),
        (1,'COLLECTION','Collection'),
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
    r_meas =  models.FloatField('R-meas')
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
    XRF_COLOR_LIST = ['#800080','#FF0000','#008000',
                  '#FF00FF','#800000','#808000',
                  '#008080','#00FF00','#000080',
                  '#00FFFF','#0000FF','#000000',
                  '#800040','#BD00BD','#00FA00',
                  '#800000','#FA00FA','#00BD00',
                  '#008040','#804000','#808000',
                  '#408000','#400080','#004080',
                  ]
    SCAN_TYPES = Choices(
        (0,'MAD_SCAN','MAD Scan'),
        (1,'EXCITATION_SCAN','Excitation Scan'),
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
            
        def join(a,b):
            if a==b:
                return [a]
            if abs(b[1]-a[1]) < 0.200:
                if a[0][:-1] == b[0][:-1]:
                    nm = b[0][:-1]
                else:
                    nm = '%s,%s' % (a[0], b[0])
                nm = name_dict.get(nm, nm)
                ht =  (a[2] + b[2])
                pos = (a[1]*a[2] + b[1]*b[2])/ht
                return [(nm, round(pos,4), round(ht,2))]
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
                project = request.user.get_profile()
                e.project_id = project.pk
            except Project.DoesNotExist:
                project = None
                
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
            # use api_user if available in request
            if getattr(request, 'api_user') is not None:
                e.user_description = request.api_user.client_name
            else:
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
        (0,'LOGIN','Login'),
        (1,'LOGOUT','Logout'),
        (2,'TASK','Task'),
        (3,'CREATE','Create'),
        (4,'MODIFY','Modify'),
        (5,'DELETE','Delete'),
        (6,'ARCHIVE','Archive')
    )
    created = models.DateTimeField('Date/Time', auto_now_add=True, editable=False)
    project = models.ForeignKey(Project, blank=True, null=True)
    user = models.ForeignKey(Project, blank=True, null=True, related_name='activities')
    user_description = models.CharField('User name', max_length=60, blank=True, null=True)
    ip_number = models.GenericIPAddressField('IP Address')
    object_id = models.PositiveIntegerField(blank=True, null=True)
    content_type = models.ForeignKey(ContentType, blank=True, null=True)
    affected_item = GenericForeignKey('content_type', 'object_id')
    action_type = models.IntegerField(choices=TYPE )
    object_repr = models.CharField('Entity', max_length=200, blank=True, null=True)
    description = models.TextField(blank=True)
    
    objects = ActivityLogManager()
    
    class Meta:
        ordering = ('-created',)
    
    def __unicode__(self):
        return str(self.created)
    
class Feedback(models.Model):
    HELP = {
        'message': 'You can use Restructured Text formatting to compose your message.',
    }
    TYPE = Choices(
        (0,'REMOTE_CONTROL','Remote Control'),
        (1,'MXLIVE_WEBSITE','MxLIVE Website'),
        (2,'OTHER','Other')
    )
    project = models.ForeignKey(Project)
    category = models.IntegerField('Category', choices=TYPE)
    contact_name = models.CharField(max_length=100, blank=True, null=True)
    contact = models.EmailField(max_length=100, blank=True, null=True)
    message = models.TextField(blank=False)
    created = models.DateTimeField('date created', auto_now_add=True, editable=False)

    def __unicode__(self):
        if len(self.message) > 23:
            return "%s:'%s'..." % (self.get_category_display(), self.message[:20])
        else:
            return "%s:'%s'" % (self.get_category_display(), self.message)
  
    class Meta:
        verbose_name = 'Feedback comment'

from django_auth_ldap.backend import populate_user, populate_user_profile
from django.db.models.signals import pre_delete, post_delete
from django.dispatch import receiver
from staff import slap


@receiver(populate_user)
def populate_user_handler(sender, user, ldap_user, **kwargs):
    user_uids = set(map(int, ldap_user.attrs.get('gidnumber', [])))
    admin_uids = set(getattr(settings, 'LDAP_ADMIN_UIDS', []))
    if user_uids & admin_uids :
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

#FIXME: Remove everything below here - only there so old data can be loaded
class Dewar(ObjectBaseClass):
    HELP = {
        'name': "An externally visible label on the dewar. If there is a barcode on the dewar, please scan it here",
        'comments': "Use this field to jot notes related to this shipment for your own use",
        'cascade': 'containers and samples (along with groups)',
        'cascade_help': 'All associated containers will be left without a dewar'
    }
    comments = models.TextField(blank=True, null=True, help_text=HELP['comments'])
    storage_location = models.CharField(max_length=60, null=True, blank=True)
    shipment = models.ForeignKey(Shipment, blank=True, null=True)