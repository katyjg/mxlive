import datetime
import hashlib
import copy
import string

from django.conf import settings
from django.db import models
from django.contrib.auth.models import User
from django.contrib.contenttypes.models import ContentType
from django.contrib.contenttypes import generic
from django.db.models import Q

from imm.enum import Enum
from jsonfield import JSONField
from django.utils import dateformat
import logging

from django.db.models.signals import post_save
from django.db.models.signals import pre_delete
from django.db.models.signals import pre_save
from django.db.models.signals import post_delete
from django.core.exceptions import ObjectDoesNotExist
from lims.filterspecs import WeeklyFilterSpec

IDENTITY_FORMAT = '-%y%m'
RESUMBITTED_LABEL = 'Resubmitted_'

def cassette_loc_repr(pos):
    return "ABCDEFGHIJKL"[pos/8]+str(1+pos%8)

GLOBAL_STATES =   Enum(
        'Draft', 
        'Sent', 
        'On-site',
        'Loaded', 
        'Returned',
        'Active',
        'Processing',
        'Complete',
        'Reviewed', 
        'Archived',
    )

class ManagerWrapper(models.Manager):
    """ This a models.Manager instance that wraps any models.Manager instance and alters the query_set() of
    the warpper models.Manager instance. All it does it proxy all requests to the wrapped manager EXCEPT
    for calls to get_query_set() which it alters.
    """
    def __init__(self, manager):
        """ The constructor
        @param manager: a models.Manager instance
        """
        self.manager = manager
        
    def get_query_set(self):
        raise NotImplementedError()
    
    def __getattr__(self, attr):
        """ Proxies everything to the wrapped manager """
        return getattr(self.manager, attr)
        
class ExcludeManagerWrapper(ManagerWrapper):
    """ This a models.Manager instance that wraps any models.Manager instance and .excludes()
    results from the query_set. All it does it proxy all requests to the wrapped manager EXCEPT
    for calls to get_query_set() which it alters with the appropriate excludes
    """
    def __init__(self, manager, **excludes):
        """ The constructor
        @param manager: a models.Manager instance
        @param param:  
        """
        super(ExcludeManagerWrapper, self).__init__(manager)
        self.excludes = excludes
        
    def get_query_set(self):
        """ Returns a QuerySet with appropriate .excludes() applied """
        query_set = self.manager.get_query_set()
        query_set = query_set.exclude(**self.excludes)
        return query_set
    
class FilterManagerWrapper(ManagerWrapper):
    """ This a models.Manager instance that wraps any models.Manager instance and .filters()
    results from the query_set. All it does is proxy all requests to the wrapped manager EXCEPT
    for calls to get_query_set() which it alters with the appropriate filters
    """
    def __init__(self, manager, **filters):
        """ The constructor
        @param manager: a models.Manager instance
        @param param:  
        """
        super(FilterManagerWrapper, self).__init__(manager)
        self.filters = filters
        
    def get_query_set(self):
        """ Returns a QuerySet with appropriate .excludes() applied """
        query_set = self.manager.get_query_set()
        query_set = query_set.filter(**self.filters)
        return query_set
    
class DistinctManagerWrapper(ManagerWrapper):
    """ This a models.Manager instance that wraps any models.Manager instance and .distinct()
    results from the query_set. All it does it proxy all requests to the wrapped manager EXCEPT
    for calls to get_query_set() which it alters with the appropriate distinct
    """
    def __init__(self, manager):
        """ The constructor
        @param manager: a models.Manager instance
        """
        super(DistinctManagerWrapper, self).__init__(manager)
        
    def get_query_set(self):
        """ Returns a QuerySet with appropriate .distinct() applied """
        query_set = self.manager.get_query_set()
        query_set = query_set.distinct()
        return query_set
    
class OrderByManagerWrapper(ManagerWrapper):
    """ This a models.Manager instance that wraps any models.Manager instance and .order_by()
    results from the query_set. All it does it proxy all requests to the wrapped manager EXCEPT
    for calls to get_query_set() which it alters with the appropriate orderings
    """
    def __init__(self, manager, *fields):
        """ The constructor
        @param manager: a models.Manager instance
        @param param:  
        """
        super(OrderByManagerWrapper, self).__init__(manager)
        self.fields = fields
        
    def get_query_set(self):
        """ Returns a QuerySet with appropriate .order_by() applied """
        query_set = self.manager.get_query_set()
        query_set = query_set.order_by(*self.fields)
        return query_set

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
        
class Project(models.Model):
    user = models.ForeignKey(User, unique=True)
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

    class Meta:
        verbose_name = "Project Profile"

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
        STATES.ACTIVE: [STATES.PROCESSING, STATES.REVIEWED],
        STATES.PROCESSING: [STATES.COMPLETE, STATES.REVIEWED],
        STATES.COMPLETE: [STATES.PROCESSING, STATES.REVIEWED],
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
        message = '%s (%s) deleted.' % (self.__class__.__name__[0].upper() + self.__class__.__name__[1:].lower(), self.name)
        if request is not None:
            ActivityLog.objects.log_activity(request, self, ActivityLog.TYPE.DELETE, message)
        super(LimsBaseClass, self).delete()

    def archive(self, request=None):
        if self.is_closable():
            self.change_status(self.STATES.ARCHIVED)
            message = '%s (%s) archived.' % (self.__class__.__name__[0].upper() + self.__class__.__name__[1:].lower(), self.name)
            if request is not None:
                ActivityLog.objects.log_activity(request, self, ActivityLog.TYPE.ARCHIVE, message)

    def send(self, request=None):
        self.change_status(self.STATES.SENT)       
        message = '%s (%s) sent to CLS.' % (self.__class__.__name__[0].upper() + self.__class__.__name__[1:].lower(), self.name)
        if request is not None:
            ActivityLog.objects.log_activity(request, self, ActivityLog.TYPE.MODIFY, message)

    def receive(self, request=None):
        self.change_status(self.STATES.ON_SITE) 
        message = '%s (%s) received at CLS.' % (self.__class__.__name__[0].upper() + self.__class__.__name__[1:].lower(), self.name)
        if request is not None:
            ActivityLog.objects.log_activity(request, self, ActivityLog.TYPE.MODIFY, message)

    def load(self, request=None):
        self.change_status(self.STATES.LOADED)    
        message = '%s (%s) loaded into automounter.' % (self.__class__.__name__[0].upper() + self.__class__.__name__[1:].lower(), self.name)
        if request is not None:
            ActivityLog.objects.log_activity(request, self, ActivityLog.TYPE.MODIFY, message)

    def unload(self, request=None):
        self.change_status(self.STATES.ON_SITE)   
        message = '%s (%s) unloaded from automounter.' % (self.__class__.__name__[0].upper() + self.__class__.__name__[1:].lower(), self.name)
        if request is not None:
            ActivityLog.objects.log_activity(request, self, ActivityLog.TYPE.MODIFY, message)

    def returned(self, request=None):
        self.change_status(self.STATES.RETURNED)     
        message = '%s (%s) returned.' % (self.__class__.__name__[0].upper() + self.__class__.__name__[1:].lower(), self.name)
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
    STATUS_CHOICES = LimsBaseClass.STATES.get_choices([LimsBaseClass.STATES.DRAFT, LimsBaseClass.STATES.SENT, LimsBaseClass.STATES.ON_SITE, LimsBaseClass.STATES.RETURNED, LimsBaseClass.STATES.ARCHIVED])

    status = models.IntegerField(max_length=1, choices=STATUS_CHOICES, default=LimsBaseClass.STATES.DRAFT)
    class Meta:
        abstract = True

class LoadableBaseClass(LimsBaseClass):
    STATUS_CHOICES = LimsBaseClass.STATES.get_choices([LimsBaseClass.STATES.DRAFT, LimsBaseClass.STATES.SENT, LimsBaseClass.STATES.ON_SITE, LimsBaseClass.STATES.LOADED, LimsBaseClass.STATES.RETURNED, LimsBaseClass.STATES.ARCHIVED])
    TRANSITIONS = copy.deepcopy(LimsBaseClass.TRANSITIONS)
    TRANSITIONS[LimsBaseClass.STATES.ON_SITE] = [LimsBaseClass.STATES.RETURNED, LimsBaseClass.STATES.LOADED]

    status = models.IntegerField(max_length=1, choices=STATUS_CHOICES, default=LimsBaseClass.STATES.DRAFT)    
    class Meta:
        abstract = True

class Shipment(ObjectBaseClass):
    HELP = {
        'name': "This should be an externally visible label",
        'comments': "Use this field to jot notes related to this shipment for your own use",
        'cascade': 'dewars, containers and crystals (along with experiments)',
        'cascade_help': 'All associated dewars will be left without a shipment'
    }
    comments = models.TextField(blank=True, null=True, max_length=200)
    tracking_code = models.CharField(blank=True, null=True, max_length=60)
    return_code = models.CharField(blank=True, null=True, max_length=60)
    date_shipped = models.DateTimeField(null=True, blank=True)
    date_received = models.DateTimeField(null=True, blank=True)
    date_returned = models.DateTimeField(null=True, blank=True)
    carrier = models.ForeignKey(Carrier, null=True, blank=True)
   
    def identity(self):
        return 'SH%03d%s' % (self.id, self.created.strftime(IDENTITY_FORMAT))
    identity.admin_order_field = 'pk'
    
    def barcode(self):
        return self.tracking_code or self.name

    def num_dewars(self):
        return self.dewar_set.count()
    
    def is_sendable(self):
        return self.status == self.STATES.DRAFT and not self.shipping_errors()
    
    def is_pdfable(self):
        return self.is_sendable() or self.status >= self.STATES.SENT
    
    def is_xlsable(self):
        # removed is_sendable check. orphan crystals don't get the default created experiment until sent. 
        return self.status >= self.STATES.SENT
    
    def is_returnable(self):
        return self.status == self.STATES.ON_SITE 

    def has_labels(self):
        return self.status <= self.STATES.SENT and self.num_dewars()  

    def is_processed():
        # if all experiments in shipment are complete, then it is a processed shipment. 
        experiment_list = Experiment.objects.filter(shipment__get_container_list=self)
        for dewar in self.dewar_set.all():
            for container in dewar.container_set.all():
                for experiment in container.get_experiment_list():
                    if experiment not in experiment_list:
                        experiment_list.append(experiment)
        for experiment in experiment_list:
            if experiment.is_reviewable():
                return False
        return True
 
    def label_hash(self):
        # use dates of project, shipment, and each shipment within dewar to determine
        # when contents were last changed
        txt = str(self.project) + str(self.project.modified) + str(self.modified)
        for dewar in self.dewar_set.all():
            txt += str(dewar.modified)
        h = hashlib.new('ripemd160') # no successful collisoin attacks yet
        h.update(txt)
        return h.hexdigest()
    
    def shipping_errors(self):
        """ Returns a list of descriptive string error messages indicating the Shipment is not
            in a 'shippable' state
        """
        errors = []
        if self.num_dewars() == 0:
            errors.append("no Dewars")
        for dewar in self.dewar_set.all():
            if dewar.num_containers() == 0:
                errors.append("empty Dewar (%s)" % dewar.name)
            for container in dewar.container_set.all():
                if container.num_crystals() == 0:
                    errors.append("empty Container (%s)" % container.name)
        return errors
    
    def setup_default_experiment(self, data=None):
        """ If there are unassociated Crystals in the project, creates a default Experiment and associates the
            crystals
        """
        unassociated_crystals = self.project.crystal_set.filter(experiment__isnull=True)
        if unassociated_crystals:
            exp_name = '%s auto' % dateformat.format(datetime.datetime.now(), 'M jS P')
            experiment = Experiment(project=self.project, name=exp_name)
            experiment.save()
            for unassociated_crystal in unassociated_crystals:
                unassociated_crystal.experiment = experiment
                unassociated_crystal.save()

    def delete(self, request=None, cascade=True):
        if self.is_deletable():
            if not cascade:
                self.dewar_set.all().update(shipment=None)
            for obj in self.dewar_set.all():
                obj.delete(request=request)
            super(Shipment, self).delete(request=request)

    def send(self, request=None):
        if self.is_sendable():
            self.date_shipped = datetime.datetime.now()
            self.setup_default_experiment()
            self.save()
            for obj in self.dewar_set.all():
                obj.send(request=request)
            super(Shipment, self).send(request=request)

    def returned(self, request=None):
        if self.is_returnable():
            self.date_returned = datetime.datetime.now()
            self.save()
            for obj in self.dewar_set.all():
                obj.returned(request=request)
            super(Shipment, self).returned(request=request)

    def archive(self, request=None):
        for obj in self.dewar_set.all():
            obj.archive(request=request)
        super(Shipment, self).archive(request=request)
        
class Dewar(ObjectBaseClass):
    HELP = {
        'name': "An externally visible label on the dewar. If there is a barcode on the dewar, please scan it here",
        'comments': "Use this field to jot notes related to this shipment for your own use",
        'cascade': 'containers and crystals (along with experiments)',
        'cascade_help': 'All associated containers will be left without a dewar'
    }
    comments = models.TextField(blank=True, null=True, help_text=HELP['comments'])
    storage_location = models.CharField(max_length=60, null=True, blank=True)
    shipment = models.ForeignKey(Shipment, blank=True, null=True)

    def identity(self):
        return 'DE%03d%s' % (self.id, self.created.strftime(IDENTITY_FORMAT))
    identity.admin_order_field = 'pk'

    def barcode(self):
        return "CLS%04d-%04d" % (self.id, self.shipment.id)

    def num_containers(self):
        return self.container_set.count()   

    def is_assigned(self):
        return self.shipment is not None
    
    def is_receivable(self):
        return self.status == self.STATES.SENT 
    
    def delete(self, request=None, cascade=True):
        if self.is_deletable():
            if not cascade:
                self.container_set.all().update(dewar=None)
            for obj in self.container_set.all():
                obj.delete(request=request)
            super(Dewar, self).delete(request=request)

    def send(self, request=None):
        for obj in self.container_set.all():
            obj.send(request=request)
        super(Dewar, self).send(request=request)

    def receive(self, request=None):
        if self.is_receivable():
            for obj in self.container_set.all():
                obj.receive(request=request)
            super(Dewar, self).receive(request=request)
            all_dewars_received = True
            for dewar in self.shipment.dewar_set.all():
                if dewar.status != Dewar.STATES.ON_SITE: all_dewars_received = False
            if all_dewars_received:
                super(Shipment, self.shipment).receive(request=request)

    def returned(self, request=None):
        for obj in self.container_set.all():
            obj.returned(request=request)
        super(Dewar, self).returned(request=request)

    def archive(self, request=None):
        for obj in self.container_set.all():
            obj.archive(request=request)
        super(Dewar, self).archive(request=request)

class Container(LoadableBaseClass):
    TYPE = Enum(
        'Cassette', 
        'Uni-Puck', 
        'Cane', 
    )
    HELP = {
        'name': "An externally visible label on the container. If there is a barcode on the container, please scan it here",
        'capacity': "The maximum number of samples this container can hold",
        'cascade': 'crystals (along with experiments)',
        'cascade_help': 'All associated crystals will be left without a container'
    }
    kind = models.IntegerField('type', max_length=1, choices=TYPE.get_choices() )
    dewar = models.ForeignKey(Dewar, blank=True, null=True)
    comments = models.TextField(blank=True, null=True)
    priority = models.IntegerField(default=0)
    staff_priority = models.IntegerField(default=0)
    
    def identity(self):
        return 'CN%03d%s' % (self.id, self.created.strftime(IDENTITY_FORMAT))
    identity.admin_order_field = 'pk'
    
    def barcode(self):
        return self.name

    def num_crystals(self):
        return self.crystal_set.count()
    
    def is_assigned(self):
        return self.dewar is not None

    def capacity(self):
        _cap = {
            self.TYPE.CASSETTE : 96,
            self.TYPE.UNI_PUCK : 16,
            self.TYPE.CANE : 6,
            None : 0,
        }
        return _cap[self.kind]

    def get_form_field(self):
        return 'container'

    def experiments(self):
        experiments = set([])
        for crystal in self.crystal_set.all():
            for experiment in crystal.experiment_set.all():
                experiments.add('%s-%s' % (experiment.project.name, experiment.name))
        return ', '.join(experiments)
    
    def get_experiment_list(self):
        experiments = list()
        for crystal in self.crystal_set.all():
            if crystal.experiment not in experiments:
                experiments.append(crystal.experiment)
        return experiments
    
    def contains_experiment(self, experiment):
        """
        Checks if the specified experiment is in the container.
        """
        for crystal in self.crystal_set.all():
            for crys_experiment in crystal.experiment_set.all():
                if crys_experiment == experiment:
                    return true
        return false
    
    def contains_experiments(self, experiment_list):
        for experiment in experiment_list:
            if self.contains_experiment(experiment):
                return true
        return false
    
    def update_priority(self):
        """ Updates the Container's priority/staff_priority to max(Experiment priorities)
        """
        for field in ['priority', 'staff_priority']:
            priority = None
            for crystal in self.crystal_set.all():
                if crystal.experiment:
                    if priority is None:
                        priority = getattr(crystal.experiment, field)
                    else:
                        priority = max(priority, getattr(crystal.experiment, field))
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
        occupied_positions = [xtl.container_location for xtl in self.crystal_set.all().exclude(pk=id) ]
        return loc not in occupied_positions
    
    def location_and_crystal(self):
        retval = []
        xtalset = self.crystal_set.all()
        for location in self.valid_locations():
            xtl = None
            for crystal in xtalset:
                if crystal.container_location == location:
                    xtl = crystal
            retval.append((location, xtl))
        return retval

    def delete(self, request=None, cascade=True):
        if self.is_deletable:
            if not cascade:
                self.crystal_set.all().update(container=None)
            for obj in self.crystal_set.all():
                obj.delete(request=request)
            super(Container, self).delete(request=request)

    def send(self, request=None):
        for obj in self.crystal_set.all():
            obj.send(request=request)
        super(Container, self).send(request=request)

    def receive(self, request=None):
        for obj in self.crystal_set.all():
            obj.receive(request=request)
            obj.setup_experiment()
        super(Container, self).receive(request=request)

    def load(self, request=None):
        for obj in self.crystal_set.all(): obj.load(request=request)
        super(Container, self).load(request=request)

    def unload(self, request=None):
        for obj in self.crystal_set.all(): obj.unload(request=request)
        super(Container, self).unload(request=request)  

    def returned(self, request=None):
        for obj in self.crystal_set.all():
            obj.returned(request=request)
        super(Container, self).returned(request=request)

    def archive(self, request=None):
        for obj in self.crystal_set.all():
            obj.archive(request=request)
        super(Container, self).archive(request=request)
        
    def json_dict(self):
        return {
            'project_id': self.project.pk,
            'id': self.pk,
            'name': self.name,
            'type': Container.TYPE[self.kind],
            'load_position': '',
            'comments': self.comments,
            'crystals': [crystal.pk for crystal in self.crystal_set.all()]
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

class Cocktail(LimsBaseClass):
    HELP = {
        'cascade': 'crystals',
        'cascade_help': 'All associated crystals will be left without a cocktail'
    }
    is_radioactive = models.BooleanField()
    contains_heavy_metals = models.BooleanField()
    contains_prions = models.BooleanField()
    contains_viruses = models.BooleanField()
    description = models.TextField(blank=True, null=True)

    def identity(self):
        return 'CT%03d%s' % (self.id, self.created.strftime(IDENTITY_FORMAT))
    identity.admin_order_field = 'pk'

    is_editable = True
    is_deletable = True
    is_closable = False
    
    def delete(self, request=None, cascade=True):
        if not cascade:
            for obj in self.crystal_set.all():
                if obj.is_editable():
                    obj.cocktail = None
                    obj.save()
        super(Cocktail, self).delete()

    class Meta:
        ordering = ['name','-created']
        verbose_name = "Protein Cocktail"
        verbose_name_plural = 'Protein Cocktails'
    
class CrystalForm(LimsBaseClass):
    HELP = {
        'cascade': 'crystals',
        'cascade_help': 'All associated crystals will be left without a crystal form'
    }
    space_group = models.ForeignKey(SpaceGroup,null=True, blank=True)
    cell_a = models.FloatField(' a', null=True, blank=True)
    cell_b = models.FloatField(' b', null=True, blank=True)
    cell_c = models.FloatField(' c',null=True, blank=True)
    cell_alpha = models.FloatField(' alpha',null=True, blank=True)
    cell_beta = models.FloatField(' beta',null=True, blank=True)
    cell_gamma = models.FloatField(' gamma',null=True, blank=True)
    
    def identity(self):
        return 'CF%03d%s' % (self.id, self.created.strftime(IDENTITY_FORMAT))
    identity.admin_order_field = 'pk'
    
    class Meta:
        ordering = ['name','-created']
        verbose_name = 'Crystal Form'

    is_editable = True
    is_deletable = True
    is_closable = False
    
    def delete(self, request=None, cascade=True):
        if not cascade:
            for obj in self.crystal_set.all():
                if obj.is_editable():
                    obj.crystal_form = None
                    obj.save()
        super(CrystalForm, self).delete()

class Experiment(LimsBaseClass):
    STATUS_CHOICES = LimsBaseClass.STATES.get_choices([LimsBaseClass.STATES.DRAFT, LimsBaseClass.STATES.ACTIVE, LimsBaseClass.STATES.PROCESSING, LimsBaseClass.STATES.COMPLETE, LimsBaseClass.STATES.REVIEWED, LimsBaseClass.STATES.ARCHIVED])
    HELP = {
        'cascade': 'crystals',
        'cascade_help': 'All associated crystals will be left without an experiment'
    }
    EXP_TYPES = Enum(
        'Native',   
        'MAD',
        'SAD',
    )
    EXP_PLANS = Enum(
        'Rank and collect best',
        'Collect first good',
        'Screen and confirm',
        'Screen and collect',
        'Just collect',
    )
    TRANSITIONS = copy.deepcopy(LimsBaseClass.TRANSITIONS)
    TRANSITIONS[LimsBaseClass.STATES.DRAFT] = [LimsBaseClass.STATES.ACTIVE]
    TRANSITIONS[LimsBaseClass.STATES.ACTIVE] = [LimsBaseClass.STATES.PROCESSING, LimsBaseClass.STATES.COMPLETE, LimsBaseClass.STATES.REVIEWED, LimsBaseClass.STATES.ARCHIVED]   
    TRANSITIONS[LimsBaseClass.STATES.COMPLETE] = [LimsBaseClass.STATES.REVIEWED, LimsBaseClass.STATES.ACTIVE, LimsBaseClass.STATES.PROCESSING]

    status = models.IntegerField(max_length=1, choices=STATUS_CHOICES, default=LimsBaseClass.STATES.DRAFT)
    resolution = models.FloatField('Desired Resolution', null=True, blank=True)
    delta_angle = models.FloatField(null=True, blank=True)
    i_sigma = models.FloatField('Desired I/Sigma', null=True, blank=True)
    r_meas =  models.FloatField('Desired R-factor', null=True, blank=True)
    multiplicity = models.FloatField(null=True, blank=True)
    total_angle = models.FloatField('Desired Angle Range', null=True, blank=True)
    energy = models.DecimalField(null=True, max_digits=10, decimal_places=4, blank=True)
    kind = models.IntegerField('exp. type',max_length=1, choices=EXP_TYPES.get_choices(), default=EXP_TYPES.NATIVE)
    absorption_edge = models.CharField(max_length=5, null=True, blank=True)
    plan = models.IntegerField(max_length=1, choices=EXP_PLANS.get_choices(), default=EXP_PLANS.SCREEN_AND_CONFIRM)
    comments = models.TextField(blank=True, null=True)
    priority = models.IntegerField(default=0)
    staff_priority = models.IntegerField(default=0)
    
    class Meta:
        verbose_name = 'experiment request'
    
    def identity(self):
        return 'EX%03d%s' % (self.id, self.created.strftime(IDENTITY_FORMAT))    
    identity.admin_order_field = 'pk'

    def accept(self):
        return "crystal"

    def num_crystals(self):
        return self.crystal_set.count()
        
    def get_form_field(self):
        return 'experiment'

    def set_strategy_status_resubmitted(self, data=None):
        strategy = data['strategy']
        perform_action(strategy, 'resubmit')
        
    def best_crystal(self):
        # need to change to [id, score]
        if self.plan == Experiment.EXP_PLANS.RANK_AND_COLLECT_BEST:
            results = self.project.result_set.filter(experiment=self, crystal__in=self.crystal_set.all()).order_by('-score')
            if results:
                return [results[0].crystal.pk, results[0].score]
        
    def experiment_errors(self):
        """ Returns a list of descriptive string error messages indicating the Experiment has missing crystals
        """
        errors = []
        if self.crystal_set.count() == 0:
            errors.append("no Crystals")
        if self.status == Experiment.STATES.ACTIVE:
            diff = self.crystal_set.count() - self.crystal_set.filter(status__in=[Crystal.STATES.ON_SITE, Crystal.STATES.LOADED]).count()
            if diff:
                errors.append("%i crystals have not arrived on-site." % diff)
        return errors

    def is_reviewable(self):
        return self.status != Experiment.STATES.REVIEWED
    
    def is_closable(self):
        return self.status == Experiment.STATES.REVIEWED
        
    def is_complete(self):
        """
        Checks experiment type, and depending on type, determines if it's fully completed or not. 
        Updates Exp Status if considered complete. 
        """
        if self.crystal_set.filter(Q(screen_status__exact=Crystal.EXP_STATES.PENDING) | Q(collect_status__exact=Crystal.EXP_STATES.PENDING)).exists():
            return False
        if self.plan == Experiment.EXP_PLANS.RANK_AND_COLLECT_BEST or self.plan == Experiment.EXP_PLANS.COLLECT_FIRST_GOOD:
            # complete if all crystals are "screened" (or "ignored") and at least 1 is "collected"
            if not self.crystal_set.filter(collect_status__exact=Crystal.EXP_STATES.COMPLETED).exists():
                if not self.crystal_set.filter(collect_status__exact=Crystal.EXP_STATES.NOT_REQUIRED).exists():
                    self.add_comments('Unable to collect a dataset for any crystal in this experiment.')
                    return True
                return False
        elif self.plan == Experiment.EXP_PLANS.SCREEN_AND_CONFIRM:
            # complete if all crystals are "screened" (or "ignored")
            if not self.crystal_set.exclude(screen_status__exact=Crystal.EXP_STATES.IGNORE).exists():
                self.add_comments('Unable to screen any crystals in this experiment.')
        elif self.plan == Experiment.EXP_PLANS.SCREEN_AND_COLLECT or self.plan == Experiment.EXP_PLANS.JUST_COLLECT:
            # complete if all crystals are "screened" or "collected"
            if not self.crystal_set.exclude(collect_status__exact=Crystal.EXP_STATES.IGNORE).exists():
                self.add_comments('Unable to collect a dataset for any crystal in this experiment.')
        else:
            # should never get here.
            raise Exception('Invalid plan')  
        return True
        
    def delete(self, request=None, cascade=True):
        if self.is_deletable:
            if not cascade:
                self.crystal_set.all().update(experiment=None)
            else: 
                for obj in self.crystal_set.all():
                    obj.delete(request=request)
            super(Experiment, self).delete(request=request)

    def review(self, request=None):
        super(Experiment, self).change_status(LimsBaseClass.STATES.REVIEWED)
        message = '%s (%s) marked as reviewed.' % (self.__class__.__name__.upper(), self.name)
        if request is not None:
            ActivityLog.objects.log_activity(request, self, ActivityLog.TYPE.MODIFY, message)

    def archive(self, request=None):
        if cascade:
            for obj in self.crystal_set.all():
                obj.archive(request=request)
        super(Experiment, self).archive(request=request)
        
    def json_dict(self):
        """ Returns a json dictionary of the Runlist """
        json_info = {
            'project_id': self.project.pk,
            'project_name': self.project.name,
            'id': self.pk,
            'name': self.name,
            'plan': Experiment.EXP_PLANS[self.plan],
            'r_meas': self.r_meas,
            'i_sigma': self.i_sigma,
            'absorption_edge': self.absorption_edge,
            'energy': self.energy,
            'type': Experiment.EXP_TYPES[self.kind],
            'resolution': self.resolution,
            'delta_angle': self.delta_angle,
            'total_angle': self.total_angle,
            'multiplicity': self.multiplicity,
            'comments': self.comments,
            'crystals': [crystal.pk for crystal in self.crystal_set.filter(Q(screen_status__exact=Crystal.EXP_STATES.PENDING) | Q(collect_status__exact=Crystal.EXP_STATES.PENDING))],
            'best_crystal': self.best_crystal()
        }
        return json_info
        
     
class Crystal(LoadableBaseClass):
    HELP = {
        'name': "Give the sample a name by which you can recognize it. Avoid using spaces or special characters in sample names",
        'barcode': "If there is a datamatrix code on sample, please scan or input the value here",
        'pin_length': "18 mm pins are standard. Please make sure you discuss other sizes with Beamline staff before sending the sample!",
        'comments': 'You can use restructured text formatting in this field',
        'cocktail': '',
    }
    EXP_STATES = Enum(
        'Not Required',
        'Pending',
        'Completed',
        'Ignore',
    )
    barcode = models.SlugField(null=True, blank=True)
    crystal_form = models.ForeignKey(CrystalForm, null=True, blank=True)
    pin_length = models.IntegerField(max_length=2, default=18)
    loop_size = models.FloatField(null=True, blank=True)
    cocktail = models.ForeignKey(Cocktail, null=True, blank=True)
    container = models.ForeignKey(Container, null=True, blank=True)
    container_location = models.CharField(max_length=10, null=True, blank=True)
    comments = models.TextField(blank=True, null=True)
    collect_status = models.IntegerField(max_length=1, choices=EXP_STATES.get_choices(), default=EXP_STATES.NOT_REQUIRED)
    screen_status = models.IntegerField(max_length=1, choices=EXP_STATES.get_choices(), default=EXP_STATES.NOT_REQUIRED)
    priority = models.IntegerField(default=0)
    staff_priority = models.IntegerField(default=0)
    experiment = models.ForeignKey(Experiment, null=True, blank=True)
    
    class Meta:
        unique_together = (
            ("project", "container", "container_location"),
        )

    def identity(self):
        return 'XT%03d%s' % (self.id, self.created.strftime(IDENTITY_FORMAT))
    identity.admin_order_field = 'pk'
    
    def best_screening(self):
        info = {}
        results = self.result_set.filter(kind__exact=Result.RESULT_TYPES.SCREENING).order_by('-score')
        if len(results) > 0:
            info['report'] = results[0]
            info['data'] = info['report'].data
        else:
            data = self.data_set.filter(kind__exact=Data.DATA_TYPES.SCREENING).order_by('-created')
            if len(data) > 0:
                info['data'] = data[0]
        return info
    
    def best_collection(self):
        info = {}
        results = self.result_set.filter(kind__exact=Result.RESULT_TYPES.COLLECTION).order_by('-score')
        if len(results) > 0:
            info['report'] = results[0]
            info['data'] = info['report'].data
        else:
            data = self.data_set.filter(kind__exact=Data.DATA_TYPES.COLLECTION).order_by('-created')
            if len(data) > 0:
                info['data'] = data[0]
        return info

    def is_clonable(self):
        return True
    
    def setup_experiment(self):
        """ If crystal is on-site, updates the screen_status and collect_status based on its experiment type
        """
        assert self.experiment
        if self.status == Crystal.STATES.ON_SITE:
            if self.experiment.plan != Experiment.EXP_PLANS.JUST_COLLECT:
                self.change_screen_status(Crystal.EXP_STATES.PENDING)
                if self.experiment.plan != Experiment.EXP_PLANS.SCREEN_AND_COLLECT:
                    return
            self.change_collect_status(Crystal.EXP_STATES.PENDING) 

    def delete(self, request=None, cascade=True):
        if self.is_deletable:
            if self.experiment:
                if self.experiment.crystal_set.count() == 1:
                    self.experiment.delete(request=request, cascade=False)
            super(Crystal, self).delete(request=request)

    def send(self, request=None):
        assert self.experiment
        self.experiment.change_status(Experiment.STATES.ACTIVE)
        super(Crystal, self).send(request=request)

    def archive(self, request=None):
        super(Crystal, self).archive(request=request)
        assert self.experiment
        if self.experiment.crystal_set and self.experiment.crystal_set.exclude(status__exact=Crystal.STATES.ARCHIVED).count() == 0:
            super(Experiment, self.experiment).archive(request=request)

    def change_screen_status(self, status):
        if self.screen_status != status:
            self.screen_status = status
            self.save()

    def change_collect_status(self, status):
        if self.collect_status != status:
            self.collect_status = status
            self.save()

    def json_dict(self):
        return {
            'project_id': self.project.pk,
            'container_id': self.container.pk,
            'id': self.pk,
            'name': self.name,
            'barcode': self.barcode,
            'container_location': self.container_location,
            'comments': self.comments
        }
        
class Data(LimsBaseClass):
    DATA_TYPES = Enum(
        'Screening',   
        'Collection',
    )
    experiment = models.ForeignKey(Experiment, null=True, blank=True)
    crystal = models.ForeignKey(Crystal, null=True, blank=True)
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
    kind = models.IntegerField('Data type',max_length=1, choices=DATA_TYPES.get_choices(), default=DATA_TYPES.SCREENING)
    
    # need a method to determine how many frames are in item
    def num_frames(self):
        return len(self.get_frame_list())          
    
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
        return '%s (%d images)' % (self.name, self.num_frames())
    
    def total_angle(self):
        return self.delta_angle * self.num_frames()
        
    
    def generate_image_url(self, frame, brightness=None):
        # brightness is assumed to be "nm" "dk" or "lt" 
        frame_numbers = []
        wlist = [map(int, w.split('-')) for w in self.frame_sets.split(',')]
        for v in wlist:
            if len(v) == 2:
                frame_numbers.extend(range(v[0],v[1]+1))
            elif len(v) == 1:
                frame_numbers.extend(v)
                  # check that frame is in frame_numbers
         
        image_url = settings.IMAGE_PREPEND or ''
        if frame in frame_numbers:
            image_url = image_url + "/download/images/%s/%s_%03d" % (self.url, self.name, frame)
        
        # confirm brightness is valid
        if not (brightness == "nm" or brightness == "lt" or brightness == "dk"):
            brightness = None
        
        if brightness == None:
            image_url = image_url + ".img"
        else:
            image_url = image_url + "-" + brightness + ".png"
            
        return image_url   
    
    def start_angle_for_frame(self, frame):
        return (frame - self.first_frame) * self.delta_angle + self.start_angle 

    def is_closable(self):
        return True

        
    class Meta:
        verbose_name = 'Dataset'

class Strategy(LimsBaseClass):
    attenuation = models.FloatField()
    distance = models.FloatField(default=200.0)
    start_angle = models.FloatField(default=0.0)
    delta_angle = models.FloatField(default=1.0)
    total_angle = models.FloatField(default=180.0)
    exposure_time = models.FloatField(default=1.0)
    two_theta = models.FloatField(default=0.0)
    energy = models.FloatField(default=12.658)
    exp_resolution = models.FloatField('Expected Resolution')
    exp_completeness = models.FloatField('Expected Completeness')
    exp_multiplicity = models.FloatField('Expected Multiplicity')
    exp_i_sigma = models.FloatField('Expected I/Sigma')
    exp_r_factor =models.FloatField('Expected R-factor')

    def identity(self):
        return 'ST%03d%s' % (self.id, self.created.strftime(IDENTITY_FORMAT))
    identity.admin_order_field = 'pk'

    def is_strategy_type(self):
        return True

    class Meta:
        verbose_name_plural = 'Strategies'

class Result(LimsBaseClass):
    RESULT_TYPES = Enum(
        'Screening',   
        'Collection',
    )
    experiment = models.ForeignKey(Experiment, null=True, blank=True)
    crystal = models.ForeignKey(Crystal, null=True, blank=True)
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
    r_mrgdf = models.FloatField('R-mrgd-F')
    sigma_spot = models.FloatField('Sigma(spot)')
    sigma_angle = models.FloatField('Sigma(angle)')
    ice_rings = models.IntegerField()
    url = models.CharField(max_length=200)
    kind = models.IntegerField('Result type',max_length=1, choices=RESULT_TYPES.get_choices())
    details = JSONField()
    strategy = models.OneToOneField(Strategy, null=True, blank=True)
    
    def identity(self):
        return 'RT%03d%s' % (self.id, self.created.strftime(IDENTITY_FORMAT))
    identity.admin_order_field = 'pk'

    class Meta:
        ordering = ['-score']
        verbose_name = 'Analysis Report'

class ScanResult(LimsBaseClass):
    SCAN_TYPES = Enum(
        'MAD Scan',   
        'Excitation Scan',
    )
    experiment = models.ForeignKey(Experiment, null=True, blank=True)
    crystal = models.ForeignKey(Crystal, null=True, blank=True)
    edge = models.CharField(max_length=20)
    details = JSONField()
    kind = models.IntegerField('Scan type',max_length=1, choices=SCAN_TYPES.get_choices())
    
    def identity(self):
        return 'SC%03d%s' % (self.id, self.created.strftime(IDENTITY_FORMAT))
    identity.admin_order_field = 'pk'
    
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
            e.user_description = request.user.get_full_name()
        except:
            # use api_user if available in request
            if getattr(request, 'api_user') is not None:
                e.user_description = request.api_user.client_name
            else:
                e.user_description = "System"
        e.ip_number = request.META['REMOTE_ADDR']
        e.action_type = action_type
        e.description = description
        e.object_repr = repr(obj)
        e.save()

    def last_login(self, request):
        logs = self.filter(user__exact=request.user, action_type__exact=ActivityLog.TYPE.LOGIN)
        if logs.count() > 1:
            return logs[1]
        else:
            return None
        
class ActivityLog(models.Model):
    TYPE = Enum('Login', 'Logout', 'Task', 'Create', 'Modify','Delete', 'Archive')
    created = models.DateTimeField('Date/Time', auto_now_add=True, editable=False)
    project = models.ForeignKey(Project, blank=True, null=True)
    user = models.ForeignKey(User, blank=True, null=True)
    user_description = models.CharField('User name', max_length=60, blank=True, null=True)
    ip_number = models.IPAddressField('IP Address')
    object_id = models.PositiveIntegerField(blank=True, null=True)
    content_type = models.ForeignKey(ContentType, blank=True, null=True)
    affected_item = generic.GenericForeignKey('content_type', 'object_id')
    action_type = models.IntegerField(max_length=1, choices=TYPE.get_choices() )
    object_repr = models.CharField('Item', max_length=200, blank=True, null=True)
    description = models.TextField(blank=True)
    
    objects = ActivityLogManager()
    created.weekly_filter = True
    
    class Meta:
        ordering = ('-created',)
    
    def __unicode__(self):
        return str(self.created)
    
class Feedback(models.Model):
    TYPE = Enum(
        'Remote Control',
        'LIMS Website',
        'Other',
    )
    project = models.ForeignKey(Project)
    category = models.IntegerField('Category',max_length=1, choices=TYPE.get_choices())
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

__all__ = [
    'ExcludeManagerWrapper',
    'FilterManagerWrapper',
    'OrderByManagerWrapper',
    'DistinctManagerWrapper',
    'Carrier',
    'Project',
    'Session',
    'Beamline',
    'Shipment',
    'Dewar',
    'Container',
    'SpaceGroup',
    'Cocktail',
    'CrystalForm',
    'Experiment',
    'Crystal',
    'Data',
    'Strategy',
    'Result',
    'ScanResult',
    'ActivityLog',
    'Feedback',
    ]   

