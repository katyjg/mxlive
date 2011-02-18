import datetime
import hashlib

from django.conf import settings
from django.db import models
from django.contrib.auth.models import User
from django.contrib.contenttypes.models import ContentType
from django.contrib.contenttypes import generic

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
OBJECT_STATES = Enum(
    'ACTIVE', 
    'ARCHIVED', 
    'DELETED')
RESUMBITTED_LABEL = 'Resubmitted_'

def cassette_loc_repr(pos):
    return "ABCDEFGHIJKL"[pos/8]+str(1+pos%8)

class Beamline(models.Model):
    name = models.CharField(max_length=600)
    energy_lo = models.FloatField(default=4.0)
    energy_hi = models.FloatField(default=18.5)
    contact_phone = models.CharField(max_length=60)

    def __unicode__(self):
        return self.name
        
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
    

class Cocktail(models.Model):
    SOURCES = Enum(
        'Unknown',
        'Synthetic',
        'Plant',
        'Animal',
        'Human',
        'Bacterial',
        'Fungal',
        'Viral',
    )
    TYPES = Enum(
        'Protein',
        'Salt',
        'Precipitant',
        'Organic molecule',
        'Buffer',
    )
    HELP = {
        'constituents': 'Comma separated list of the constituents in this cocktail',
    }
    project = models.ForeignKey(Project)
    name = models.CharField(max_length=60)
    constituents = models.CharField(max_length=200) 
    #source = models.IntegerField(max_length=1, choices=SOURCES.get_choices(), default=SOURCES.UNKNOWN)
    #kind = models.IntegerField('type', max_length=1, choices=TYPES.get_choices(), default=TYPES.PROTEIN)
    is_radioactive = models.BooleanField()
    is_contaminant = models.BooleanField()
    is_toxic = models.BooleanField()
    is_oxidising = models.BooleanField()
    is_explosive = models.BooleanField()
    is_corrosive = models.BooleanField()
    is_inflamable = models.BooleanField()
    is_biological_hazard = models.BooleanField()
    description = models.TextField(blank=True, null=True)
    created = models.DateTimeField('date created', auto_now_add=True, editable=False)
    modified = models.DateTimeField('date modified',auto_now=True, editable=False)

    
    def __unicode__(self):
        return self.name

    def identity(self):
        return 'CT%03d%s' % (self.id, self.created.strftime(IDENTITY_FORMAT))
    identity.admin_order_field = 'pk'

    is_editable = True
    is_deletable = True
    
    '''    
    FIELD_TO_ENUM = {
        'source': SOURCES,
        'kind': TYPES,
    }
    '''

    class Meta:
        verbose_name = "Protein Cocktail"
        verbose_name_plural = 'Protein Cocktails'
        
        

    
def perform_action(instance, action, data=None):
    """ Performs an action (send a message to FSM) on an object. See Shipment for a description
        of how the FSM datastructure is setup.
            
        @param instance: a models.Model instance with STATES/TRANSITIONS/ACTIONS defined
        @param status: a new STATE to transition to. 
        @param data: a dict of additional data possibly required by the methods in the ACTIONS dictionary 
    """
    # check the assertions
    for field, value in instance.ACTIONS[action].items():
        if field == 'assertions':
            for assertion in value:
                if not getattr(instance, assertion)():
                    raise ValueError('Unsatisfied assertion: %s' % assertion)
    
    # set the status appropriately
    for field, value in instance.ACTIONS[action].items():
        if field == 'assertions':
            continue # dealt with these already
        if field == 'methods':
            continue # deal with these later
        if callable(value):
            value = value()
        if field == 'status':
            change_status(instance, value)
        else:
            setattr(instance, field, value)
    instance.save()

    # perform the action on the children
    if hasattr(instance, 'get_children'):
        for child in instance.get_children():
            if child.ACTIONS.has_key(action):
                perform_action(child, action, data=data)
        
    # call the post methods
    for field, value in instance.ACTIONS[action].items():
        if field != 'methods':
            continue # dealt with these already
        for method in value:
            if data:
                getattr(instance, method)(data=data)
            else:
                getattr(instance, method)()
            instance.save()
            
def change_status(instance, status):
    """ Changes the state of the instance's FSM to status
    
    @param instance: a models.Model instance with STATES/TRANSITIONS/ACTIONS defined
    @param status: a new STATE to transition to. 
    """
    if status == instance.status:
        return
    if status not in instance.TRANSITIONS[instance.status]:
        raise ValueError("Invalid transition on '%s.%s':  '%s' -> '%s'" % (instance.__class__, instance.pk, instance.STATES[instance.status], instance.STATES[status]))
    #logging.info("Changing status of '%s.%s': '%s' -> '%s'" % (instance.__class__, instance.pk, instance.STATES[instance.status], instance.STATES[status]))
    instance.status = status
    
class Shipment(models.Model):
    #
    # STATES/TRANSITIONS/ACTIONS define a finite state machine (FSM) for the Shipment (and other 
    # models.Model instances also defined in this file).
    #
    # STATES: an Enum specifying all of the valid states for instances of Shipment.
    #
    # TRANSITIONS: a dict specifying valid state transitions. the keys are starting STATES and the 
    #     values are lists of valid final STATES. 
    #
    # ACTIONS: a dict of valid actions (messages) for the FSM. the keys are actions/messages and 
    #    the values are dicts describing what code should be executed as a result of the action/message.
    #    this dictionary has the following possible keys : values 
    #        'status' : the final state of the object
    #        'date_*' : function returning a datetime object
    #        'methods' : a list of method names to execute in order after the status has been changed
    #
    STATES = Enum(
        'Draft', 
        'Sent', 
        'On-site', 
        'Returned', 
        'Archived',
    )
    TRANSITIONS = {
        STATES.DRAFT: [STATES.SENT],
        STATES.SENT: [STATES.ON_SITE],
        STATES.ON_SITE: [STATES.RETURNED],
        STATES.RETURNED: [STATES.ARCHIVED],
    }
    ACTIONS = {
        'send': { 'status': STATES.SENT, 'date_shipped': datetime.datetime.now, 'assertions': ['is_sendable'], 'methods': ['setup_default_experiment'] },
        'receive': { 'status': STATES.ON_SITE, 'date_received': datetime.datetime.now, 'assertions': ['is_receivable'] },
        'return': { 'status': STATES.RETURNED, 'date_returned': datetime.datetime.now, 'assertions': ['is_returnable'] },
        'archive': { 'status': STATES.ARCHIVED},
    }
    HELP = {
        'label': "This should be an externally visible label",
        'code': "Barcode",
        'comments': "Use this field to jot notes related to this shipment for your own use",
    }
    project = models.ForeignKey(Project)
    label = models.CharField(max_length=60)
    comments = models.TextField(blank=True, null=True, max_length=200)
    staff_comments = models.TextField(blank=True, null=True)
    tracking_code = models.CharField(blank=True, null=True, max_length=60)
    return_code = models.CharField(blank=True, null=True, max_length=60)
    date_shipped = models.DateTimeField(null=True, blank=True)
    date_received = models.DateTimeField(null=True, blank=True)
    date_returned = models.DateTimeField(null=True, blank=True)
    status = models.IntegerField(max_length=1, choices=STATES.get_choices(), default=STATES.DRAFT)
    carrier = models.ForeignKey(Carrier, null=True, blank=True)
    created = models.DateTimeField('date created', auto_now_add=True, editable=False)
    modified = models.DateTimeField('date modified',auto_now=True, editable=False)
    
    FIELD_TO_ENUM = {
        'status': STATES,
    }
    
#    def accept(self):
#        return "dewar"
    
    def num_dewars(self):
        return self.dewar_set.count()
    
    def label_hash(self):
        # use dates of project, shipment, and each shipment within dewar to determine
        # when contents were last changed
        txt = str(self.project) + str(self.project.modified) + str(self.modified)
        for dewar in self.dewar_set.all():
            txt += str(dewar.modified)
        h = hashlib.new('ripemd160') # no successful collisoin attacks yet
        h.update(txt)
        return h.hexdigest()
    
    
    def is_empty(self):
        return self.dewar_set.count() == 0
    
    def __unicode__(self):
        return self.label
    
    def _name(self):
        return self.label
    
    name = property(_name)

    def identity(self):
        return 'SH%03d%s' % (self.id, self.created.strftime(IDENTITY_FORMAT))
    identity.admin_order_field = 'pk'
    
    def shipping_errors(self):
        """ Returns a list of descriptive string error messages indicating the Shipment is not
            in a 'shippable' state
        """
        errors = []
        if self.num_dewars() == 0:
            errors.append("no Dewars")
        for dewar in self.dewar_set.all():
            if dewar.is_empty():
                errors.append("empty Dewar (%s)" % dewar.label)
            for container in dewar.container_set.all():
                if container.num_crystals() == 0:
                    errors.append("empty Container (%s)" % container.label)
        # these are the orphaned crystals
#        for crystal in self.project.crystal_set.all():
#            if not crystal.is_assigned():
#                errors.append("Crystal (%s) not in Container" % crystal.name)
        return errors
    
    def setup_default_experiment(self, data=None):
        """ If there are unassociated Crystals in the project, creates a default Experiment and associates the
            crystals
        """
        unassociated_crystals = []
        for crystal in self.project.crystal_set.all():
            if crystal.num_experiments() == 0:
                unassociated_crystals.append(crystal)
        if unassociated_crystals:
            exp_name = '%s auto' % dateformat.format(datetime.datetime.now(), 'M jS P')
            experiment = Experiment(project=self.project, name=exp_name)
            experiment.save()
            for unassociated_crystal in unassociated_crystals:
                unassociated_crystal.experiment = experiment
                unassociated_crystal.save()
#            experiment.save()
  
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
 
    def barcode(self):
        return self.tracking_code or self.label
    
    def get_children(self):
        return self.dewar_set.all()
    
    def is_editable(self):
        return self.status == self.STATES.DRAFT 
    
    def is_deletable(self):
        return self.status == self.STATES.DRAFT 
    
    def is_sendable(self):
        return self.status == self.STATES.DRAFT and not self.shipping_errors()
    
    def is_pdfable(self):
        return self.is_sendable() or self.status >= self.STATES.SENT

    def has_labels(self):
        return self.status <= self.STATES.SENT and self.num_dewars()
    
    def is_xlsable(self):
        # removed is_sendable check. orphan crystals don't get the default created experiment until sent. 
        return self.status >= self.STATES.SENT
    
    def is_closable(self):
        return self.status == self.STATES.RETURNED 
    
    def is_returnable(self):
        return self.status == self.STATES.ON_SITE 
        
class Dewar(models.Model):
    STATES = Enum(
        'Draft', 
        'Sent', 
        'On-site', 
        'Returned', 
        'Archived',
    )
    TRANSITIONS = {
        STATES.DRAFT: [STATES.SENT],
        STATES.SENT: [STATES.ON_SITE],
        STATES.ON_SITE: [STATES.RETURNED],
        STATES.RETURNED: [STATES.ARCHIVED],
    }
    ACTIONS = {
        'send': { 'status': STATES.SENT },
        'receive': { 'status': STATES.ON_SITE, 'methods' : ['receive_parent_shipment',] },
        'return': { 'status': STATES.RETURNED  },
        'archive': { 'status': STATES.ARCHIVED},
    }
    HELP = {
        'label': "An externally visible label on the dewar. If there is a barcode on the dewar, please scan it here",
        'comments': "Use this field to jot notes related to this shipment for your own use",
    }
    project = models.ForeignKey(Project)
    label = models.CharField(max_length=60, help_text=HELP['label'])
    #code = models.CharField(max_length=128, blank=True, help_text=HELP['code'])
    comments = models.TextField(blank=True, null=True, help_text=HELP['comments'])
    staff_comments = models.TextField(blank=True, null=True)
    storage_location = models.CharField(max_length=60, null=True, blank=True)
    shipment = models.ForeignKey(Shipment, blank=True, null=True)
    created = models.DateTimeField('date created', auto_now_add=True, editable=False)
    modified = models.DateTimeField('date modified',auto_now=True, editable=False)
    status = models.IntegerField(max_length=1, choices=STATES.get_choices(), default=STATES.DRAFT)
    
    FIELD_TO_ENUM = {
        'status': STATES,
    }
    
    def is_assigned(self):
        return self.shipment is not None

    def is_empty(self):
        return self.container_set.count() == 0
    
    def num_containers(self):
        return self.container_set.count()    

    def __unicode__(self):
        return self.label
    
    def _name(self):
        return self.label
    
    name = property(_name)

    def identity(self):
        return 'DE%03d%s' % (self.id, self.created.strftime(IDENTITY_FORMAT))
    identity.admin_order_field = 'pk'
    
    def barcode(self):
        return "CLS%04d-%04d" % (self.id, self.shipment.id)
    
    def get_children(self):
        return self.container_set.all()
    
        
    def receive_parent_shipment(self, data=None):
        """ Updates the status of the parent Shipment to 'On-Site' if all the Dewars are 'On-Site'
        """
        all_dewars_received = True
        for dewar in self.shipment.dewar_set.all():
            all_dewars_received = all_dewars_received and dewar.status == Dewar.STATES.ON_SITE
        if all_dewars_received:
            self.shipment.status = Shipment.STATES.ON_SITE
            self.shipment.save()
            
    def is_editable(self):
        return self.status == self.STATES.DRAFT

    def is_deletable(self):
        return self.status == self.STATES.DRAFT 

    def is_receivable(self):
        return self.status == self.STATES.SENT 

class Container(models.Model):
    STATES = Enum(
        'Draft', 
        'Sent', 
        'On-site', 
        'Loaded',
        'Returned', 
        'Archived',
    )
    TRANSITIONS = {
        STATES.DRAFT: [STATES.SENT],
        STATES.SENT: [STATES.ON_SITE],
        STATES.ON_SITE: [STATES.RETURNED, STATES.LOADED],
        STATES.LOADED: [STATES.ON_SITE],
        STATES.RETURNED: [STATES.ARCHIVED],
    }
    ACTIONS = {
        'send': { 'status': STATES.SENT },
        'receive': { 'status': STATES.ON_SITE },
        'load': { 'status': STATES.LOADED },
        'unload': { 'status': STATES.ON_SITE },
        'return': { 'status': STATES.RETURNED },
        'archive': { 'status': STATES.ARCHIVED },
    }
    TYPE = Enum(
        'Cassette', 
        'Uni-Puck', 
        'Cane', 
    )
    HELP = {
        'label': "This should be an externally visible label on the container",
        'code': "If there is a barcode on the container, please scan the value here",
        'capacity': "The maximum number of samples this container can hold",
    }
    project = models.ForeignKey(Project)
    label = models.CharField(max_length=60)
    code = models.SlugField(null=True, blank=True)
    kind = models.IntegerField('type', max_length=1, choices=TYPE.get_choices() )
    dewar = models.ForeignKey(Dewar, blank=True, null=True)
    comments = models.TextField(blank=True, null=True)
    created = models.DateTimeField('date created', auto_now_add=True, editable=False)
    modified = models.DateTimeField('date modified',auto_now=True, editable=False)
    status = models.IntegerField(max_length=1, choices=STATES.get_choices(), default=STATES.DRAFT)
    priority = models.IntegerField(default=0)
    staff_priority = models.IntegerField(default=0)
    
    FIELD_TO_ENUM = {
        'status': STATES,
        'kind': TYPE,
    }

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
    
    def num_crystals(self):
        return self.crystal_set.count()
    

    def capacity(self):
        _cap = {
            self.TYPE.CASSETTE : 96,
            self.TYPE.UNI_PUCK : 16,
            self.TYPE.CANE : 6,
            None : 0,
        }
        return _cap[self.kind]
        
    def is_assigned(self):
        return self.dewar is not None
    
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
        
    def __unicode__(self):
        return self.label

    def identity(self):
        return 'CN%03d%s' % (self.id, self.created.strftime(IDENTITY_FORMAT))
    identity.admin_order_field = 'pk'
    
    def barcode(self):
        return self.code or self.label
    
    def get_children(self):
        return self.crystal_set.all()
    
    def is_editable(self):
        return self.status == self.STATES.DRAFT 

    def is_closable(self):
        return self.status == self.STATES.RETURNED 

    def is_deletable(self):
        return self.status == self.STATES.DRAFT 
    
    def get_form_field(self):
        return 'container'
    
    def _name(self):
        return self.label
    
    name = property(_name)
        
    def json_dict(self):
        return {
            'project_id': self.project.pk,
            'id': self.pk,
            'name': self.label,
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
    
class CrystalForm(models.Model):
    project = models.ForeignKey(Project)
    name = models.CharField(max_length=60, blank=False)
    space_group = models.ForeignKey(SpaceGroup,null=True, blank=True)
    cell_a = models.FloatField(' a', null=True, blank=True)
    cell_b = models.FloatField(' b', null=True, blank=True)
    cell_c = models.FloatField(' c',null=True, blank=True)
    cell_alpha = models.FloatField(' alpha',null=True, blank=True)
    cell_beta = models.FloatField(' beta',null=True, blank=True)
    cell_gamma = models.FloatField(' gamma',null=True, blank=True)
    created = models.DateTimeField('date created', auto_now_add=True, editable=False)
    modified = models.DateTimeField('date modified',auto_now=True, editable=False)
    
    def __unicode__(self):
        return self.name

    def identity(self):
        return 'CF%03d%s' % (self.id, self.created.strftime(IDENTITY_FORMAT))
    identity.admin_order_field = 'pk'
    
    class Meta:
        verbose_name = 'Crystal Form'

    is_editable = True
    is_deletable = True

class Experiment(models.Model):
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
    STATES = Enum(
        'Draft', 
        'Active',
        'Processing', 
        'Paused', 
        'Archived',
    )  
    EXP_STATES = Enum(
        'Incomplete',
        'Complete',
        'Reviewed',
    )
    
    TRANSITIONS = {
        STATES.DRAFT: [STATES.ACTIVE],
        STATES.ACTIVE: [STATES.PROCESSING],
        STATES.PROCESSING: [STATES.PAUSED],
        STATES.PAUSED: [STATES.ARCHIVED],
        EXP_STATES.INCOMPLETE: [EXP_STATES.COMPLETE],
        EXP_STATES.COMPLETE: [EXP_STATES.REVIEWED, EXP_STATES.INCOMPLETE],
        
    }

    ACTIONS = {
        'resubmit': { 'status': STATES.ACTIVE, 'methods': ['set_strategy_status_resubmitted',] },
        'review': { 'exp_status': EXP_STATES.REVIEWED, 'methods': ['set']},
        'archive': { 'status': STATES.ARCHIVED }
    }
    project = models.ForeignKey(Project)
    name = models.CharField(max_length=60)
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
    status = models.IntegerField(max_length=1, choices=STATES.get_choices(), default=STATES.DRAFT)
    exp_status = models.IntegerField(max_length=1, choices=EXP_STATES.get_choices(), default=EXP_STATES.INCOMPLETE)
    created = models.DateTimeField('date created', auto_now_add=True, editable=False)
    modified = models.DateTimeField('date modified',auto_now=True, editable=False)
    priority = models.IntegerField(default=0)
    staff_priority = models.IntegerField(default=0)
    
    FIELD_TO_ENUM = {
        'status': STATES,
        'kind': EXP_TYPES,
        'plan': EXP_PLANS,
    }
    
    class Meta:
        verbose_name = 'experiment request'
    
    def accept(self):
        return "crystal"
    
    def num_crystals(self):
        return self.crystal_set.count()
        
    def __unicode__(self):
        return self.name

    def identity(self):
        return 'EX%03d%s' % (self.id, self.created.strftime(IDENTITY_FORMAT))    
    identity.admin_order_field = 'pk'
    
    def is_editable(self):
        return self.status == self.STATES.DRAFT
    
    def is_deletable(self):
        return self.status == self.STATES.DRAFT
    
    def get_form_field(self):
        return 'experiment'

    def get_children(self):
        return []
        
    def set_strategy_status_resubmitted(self, data=None):
        strategy = data['strategy']
        perform_action(strategy, 'resubmit')
        
    def best_crystal(self):
        # need to change to [id, score]
        if self.plan == Experiment.EXP_PLANS.RANK_AND_COLLECT_BEST:
            results = Result.objects.filter(experiment=self, crystal__in=self.crystals.all()).order_by('-score')
            if results:
                return [results[0].crystal.pk, results[0].score]
        
    def is_reviewable(self):
        if self.exp_status == Experiment.EXP_STATES.REVIEWED:
            return False
        return True

    def is_complete(self):
        """
        Checks experiment type, and depending on type, determines if it's fully completed or not. 
        Updates Exp Status if considered complete. 
        """
        if self.plan == Experiment.EXP_PLANS.RANK_AND_COLLECT_BEST:
            # complete if all crystals are "screened" and at least 1 is "collected"
            success_collected = False
            for crystal in self.crystal_set.all():
                if crystal.screen_status != Crystal.EXP_STATES.COMPLETED:
                    self.exp_status = Experiment.EXP_STATES.INCOMPLETE
                    return False
                if crystal.collect_status == Crystal.EXP_STATES.COMPLETED:
                    success_collected = True
            if success_collected:
                self.exp_status = Experiment.EXP_STATES.COMPLETE
            else:
                self.exp_status = Experiment.EXP_STATES.INCOMPLETE
            return success_collected
        elif self.plan == Experiment.EXP_PLANS.SCREEN_AND_CONFIRM:
            # complete if all crystals are "screened" or "collected"
            for crystal in self.crystal_set.all():
                if crystal.screen_status != Crystal.EXP_STATES.COMPLETED:
                    self.exp_status = Experiment.EXP_STATES.INCOMPLETE
                    return False
            self.exp_status = Experiment.EXP_STATES.COMPLETE
            return True
        elif self.plan == Experiment.EXP_PLANS.SCREEN_AND_COLLECT:
            # complete if all crystals are "screened" or "collected" 
            for crystal in self.crystal_set.all():
                if crystal.screen_status != Crystal.EXP_STATES.COMPLETED:
                    self.exp_status = Experiment.EXP_STATES.INCOMPLETE
                    return False
                if crystal.collect_status != Crystal.EXP_STATES.COMPLETED:
                    self.exp_status = Experiment.EXP_STATES.INCOMPLETE
                    return False    
            self.exp_status = Experiment.EXP_STATES.COMPLETE
            return True
        elif self.plan == Experiment.EXP_PLANS.COLLECT_FIRST_GOOD:
            # complete if 1 crystal is collected. 
            for crystal in self.crystal_set.all():
                if crystal.collect_status == Crystal.EXP_STATES.COMPLETED:
                    self.exp_status = Experiment.EXP_STATES.COMPLETE
                    return True
            self.exp_status = Experiment.EXP_STATES.INCOMPLETE
            return False
        elif self.plan == Experiment.EXP_PLANS.JUST_COLLECT:
            # complete if all crystals are "collected"
            for crystal in self.crystal_set.all():
                if crystal.collect_status != Crystal.EXP_STATES.COMPLETED:
                    self.exp_status = Experiment.EXP_STATES.INCOMPLETE
                    return False
            self.exp_status = Experiment.EXP_STATES.COMPLETE
            return True
        else:
            # should never get here.
            raise Exception('Invalid plan')  
        
        
    def json_dict(self):
        """ Returns a json dictionary of the Runlist """
        return {
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
            'crystals': [crystal.pk for crystal in self.crystals.all()],
            'best_crystal': self.best_crystal()
        }
        
     
class Crystal(models.Model):
    STATES = Enum(
        'Draft', 
        'Sent', 
        'On-site', 
        'Loaded',
        'Returned', 
        'Archived',
    )
    TRANSITIONS = {
        STATES.DRAFT: [STATES.SENT],
        STATES.SENT: [STATES.ON_SITE],
        STATES.ON_SITE: [STATES.RETURNED, STATES.LOADED],
        STATES.LOADED: [STATES.ON_SITE],
        STATES.RETURNED: [STATES.ARCHIVED],
    }
    ACTIONS = {
        'send': { 'status': STATES.SENT },
        'receive': { 'status': STATES.ON_SITE, 'methods': ['activate_associated_experiments',] },
        'load': { 'status': STATES.LOADED },
        'unload': { 'status': STATES.ON_SITE },
        'return': { 'status': STATES.RETURNED  },
        'archive': { 'status': STATES.ARCHIVED },
    }
    HELP = {
        'name': "Give the sample a name by which you can recognize it",
        'code': "If there is a datamatrix code on sample, please scan or input the value here",
        'pin_length': "18 mm pins are standard. Please make sure you discuss other sizes with Beamline staff before sending the sample!",
        'comments': 'Add extra notes for your own use here',
        'cocktail': '',
    }
    EXP_STATES = Enum(
        'Ignore',
        'Pending',
        'Completed',
    )
    project = models.ForeignKey(Project)
    name = models.CharField(max_length=60)
    code = models.SlugField(null=True, blank=True)
    crystal_form = models.ForeignKey(CrystalForm, null=True, blank=True)
    pin_length = models.IntegerField(max_length=2, default=18)
    loop_size = models.FloatField(null=True, blank=True)
    cocktail = models.ForeignKey(Cocktail, null=True, blank=True)
    container = models.ForeignKey(Container, null=True, blank=True)
    container_location = models.CharField(max_length=10, null=True, blank=True)
    comments = models.TextField(blank=True, null=True)
    created = models.DateTimeField('date created', auto_now_add=True, editable=False)
    modified = models.DateTimeField('date modified',auto_now=True, editable=False)
    status = models.IntegerField(max_length=1, choices=STATES.get_choices(), default=STATES.DRAFT)
    collect_status = models.IntegerField(max_length=1, choices=EXP_STATES.get_choices(), default=EXP_STATES.IGNORE)
    screen_status = models.IntegerField(max_length=1, choices=EXP_STATES.get_choices(), default=EXP_STATES.IGNORE)
    priority = models.IntegerField(default=0)
    staff_priority = models.IntegerField(default=0)
    experiment = models.ForeignKey(Experiment, null=True, blank=True)
    
    FIELD_TO_ENUM = {
        'status': STATES,
    }
    
    class Meta:
        unique_together = (
            ("project", "container", "container_location"),
        )
        
    def __unicode__(self):
        return self.name

    def best_screening(self):
        # need to change to [id, score]
        results = Result.objects.filter(crystal=self, kind='0').order_by('-score')
        if results:
            return results[0]
        return None
    
    def best_collection(self):
        # need to change to [id, score]
        results = Result.objects.filter(crystal=self, kind='1').order_by('-score')
        if results:
            return results[0]
        return None                
    
    def num_experiments(self):
        if self.experiment:
            return 1
        return 0

    def identity(self):
        return 'XT%03d%s' % (self.id, self.created.strftime(IDENTITY_FORMAT))
    identity.admin_order_field = 'pk'
    
    def barcode(self):
        return self.code or None
            
    def get_children(self):
        return []
    
    def activate_associated_experiments(self, data=None):
        """ Updates the status of the associated Experiment to 'Active' if all the Crystals are 'On-Site'
        Also sets all crystals collect and screen status correctly.
        """
        assert self.experiment
        all_crystals_received = True
#        for crystal in self.experiment.crystal_set.all():
#            all_crystals_received = all_crystals_received and crystal.status == Crystal.STATES.ON_SITE
#        if all_crystals_received:
        self.experiment.status = Experiment.STATES.ACTIVE
        self.experiment.save()
        if self.experiment.plan == Experiment.EXP_PLANS.RANK_AND_COLLECT_BEST:
            self.screen_status = Crystal.EXP_STATES.PENDING
            self.save()
            return
        if self.experiment.plan == Experiment.EXP_PLANS.COLLECT_FIRST_GOOD:
            return
        if self.experiment.plan == Experiment.EXP_PLANS.JUST_COLLECT:
            self.collect_status = Crystal.EXP_STATES.PENDING
            self.save()
            return
        self.screen_status = Crystal.EXP_STATES.PENDING
        if self.experiment.plan == Experiment.EXP_PLANS.SCREEN_AND_COLLECT:
            self.collect_status = Crystal.EXP_STATES.PENDING
        self.save()
    
    def is_editable(self):
        return self.status == self.STATES.DRAFT 
    
    def is_clonable(self):
        return True
    
    def is_deletable(self):
        return self.status == self.STATES.DRAFT
    
    def is_closable(self):
        return self.status == self.STATES.RETURNED 

    def json_dict(self):
        return {
            'project_id': self.project.pk,
            'container_id': self.container.pk,
            'id': self.pk,
            'name': self.name,
            'barcode': self.barcode(),
            'container_location': self.container_location,
            'comments': self.comments
        }
        
                    
def Experiment_pre_delete(sender, **kwargs):
    # After deletion, the instance have all reference fields nulled, so
    # we need to store the original crystals for use in Experiment_post_delete
    experiment = kwargs['instance']
    experiment.saved_crystals = [crystal for crystal in experiment.crystal_set.all()]    
pre_delete.connect(Experiment_pre_delete, sender=Experiment)
    
class Data(models.Model):
    DATA_TYPES = Enum(
        'Screening',   
        'Collection',
    )
    project = models.ForeignKey(Project)
    experiment = models.ForeignKey(Experiment, null=True, blank=True)
    crystal = models.ForeignKey(Crystal, null=True, blank=True)
    name = models.CharField(max_length=20)
    resolution = models.FloatField()
    start_angle = models.FloatField()
    delta_angle = models.FloatField()
    first_frame = models.IntegerField(default=1)
    #changed to frame_sets 
    frame_sets = models.CharField(max_length=200)
    #num_frames = models.IntegerField('No. Images')
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
    created = models.DateTimeField('date created', auto_now_add=True, editable=False)
    modified = models.DateTimeField('date modified',auto_now=True, editable=False)
    
    FIELD_TO_ENUM = {
        'kind': DATA_TYPES,
    }

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

        
    class Meta:
        verbose_name = 'Dataset'


class Result(models.Model):
    RESULT_TYPES = Enum(
        'Screening',   
        'Collection',
    )
    project = models.ForeignKey(Project)
    experiment = models.ForeignKey(Experiment, null=True, blank=True)
    crystal = models.ForeignKey(Crystal, null=True, blank=True)
    data = models.ForeignKey(Data)
    name = models.CharField(max_length=20)
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
    created = models.DateTimeField('date created', auto_now_add=True, editable=False)
    modified = models.DateTimeField('date modified',auto_now=True, editable=False)
    
    FIELD_TO_ENUM = {
        'kind': RESULT_TYPES,
    }
    
    def identity(self):
        return 'RT%03d%s' % (self.id, self.created.strftime(IDENTITY_FORMAT))
    identity.admin_order_field = 'pk'

    def __unicode__(self):
        return self.name

    class Meta:
        ordering = ['-score']
        verbose_name = 'Analysis Report'

class Strategy(models.Model):
    STATES = Enum(
        'Waiting', 
        'Rejected',
        'Resubmitted',
    )
    TRANSITIONS = {
        STATES.WAITING: [STATES.REJECTED, STATES.RESUBMITTED],
    }
    ACTIONS = {
        'reject': { 'status': STATES.REJECTED },
        'resubmit': { 'status': STATES.RESUBMITTED }
    }
    project = models.ForeignKey(Project)
    result = models.ForeignKey(Result, unique=True)
    attenuation = models.FloatField()
    name = models.CharField(max_length=20)
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
    status = models.IntegerField(max_length=1, choices=STATES.get_choices(), default=STATES.WAITING)
    created = models.DateTimeField('date created', auto_now_add=True, editable=False)
    modified = models.DateTimeField('date modified',auto_now=True, editable=False)
    
    FIELD_TO_ENUM = {
        'status': STATES,
    }

    def identity(self):
        return 'ST%03d%s' % (self.id, self.created.strftime(IDENTITY_FORMAT))
    identity.admin_order_field = 'pk'

    def __unicode__(self):
        return self.name

    def is_resubmittable(self):
        return self.status == self.STATES.WAITING and \
               self.result.experiment.status in [Experiment.STATES.ACTIVE, 
                                                 Experiment.STATES.PROCESSING, 
                                                 Experiment.STATES.PAUSED]
    
    def is_rejectable(self):
        return self.status == self.STATES.WAITING and \
               self.result.experiment.status in [Experiment.STATES.ACTIVE, 
                                                 Experiment.STATES.PROCESSING, 
                                                 Experiment.STATES.PAUSED]
    def is_strategy_type(self):
        return True

    class Meta:
        verbose_name_plural = 'Strategies'

class ScanResult(models.Model):
    SCAN_TYPES = Enum(
        'MAD Scan',   
        'Excitation Scan',
    )
    project = models.ForeignKey(Project)
    experiment = models.ForeignKey(Experiment, null=True, blank=True)
    crystal = models.ForeignKey(Crystal, null=True, blank=True)
    edge = models.CharField(max_length=20)
    details = JSONField()
    kind = models.IntegerField('Scan type',max_length=1, choices=SCAN_TYPES.get_choices())
    created = models.DateTimeField('date created', auto_now_add=True, editable=False)
    modified = models.DateTimeField('date modified',auto_now=True, editable=False)
    
    FIELD_TO_ENUM = {
        'kind': SCAN_TYPES,
    }
    
    def identity(self):
        return 'SC%03d%s' % (self.id, self.created.strftime(IDENTITY_FORMAT))
    identity.admin_order_field = 'pk'
    
    def __unicode__(self):
        return self.name


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

    is_editable = True

    def __unicode__(self):
        if len(self.message) > 23:
            return "%s:'%s'..." % (self.get_category_display(), self.message[:20])
        else:
            return "%s:'%s'" % (self.get_category_display(), self.message)
  
    class Meta:
        verbose_name = 'Feedback comment'

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
    
def delete(request, model, id, orphan_models):
    """ Deletes an instance of ``model`` with primary key ``id`` and orphans the 
    Models types given in ``orphan_models``. If ``orphan_models`` is empty, then a "cascading
    delete" occurs.
    
    @param model: a models.Model subclass (ie. Project, Crystal)
    @param id: the id/pk of the model instance
    @param orphan_models: a list of tuples of (models.Model, fk_field) of models to orphan by setting
                          model.fk_field = None prior to deletion, thus avoiding a cascade.
    @raise exception:  
    """
    obj = model.objects.get(id=id)
    for (orphan_model, orphan_field) in orphan_models:
        manager = getattr(obj, orphan_model.__name__.lower()+'_set')
        for orphan in manager.all():
            setattr(orphan, orphan_field, None)
            orphan.save()
            message = 'Related field (%s) set to NULL, since it was deleted.' % ( orphan_field)
            ActivityLog.objects.log_activity(request, orphan, ActivityLog.TYPE.MODIFY,  message)
    obj.delete()

def archive(model, id):
    """ Closes/archives an instance of ``model`` with primary key ``id``.
    
    @param model: a models.Model subclass (ie. Project, Crystal)
    @param id: the id/pk of the model instance
    @raise exception:  
    """
    obj = model.objects.get(id=id)
    perform_action(obj, 'archive')
    obj.save()
    
__all__ = [
    'ExcludeManagerWrapper',
    'FilterManagerWrapper',
    'OrderByManagerWrapper',
    'DistinctManagerWrapper',
    'Carrier',
    'Project',
    'Session',
    'Beamline',
    'Cocktail',
    'Crystal',
    'CrystalForm',
    'Shipment',
    'Container',
    'Dewar',
    'Experiment',
    'ScanResult',
    'Result',
    'Data',
    'Strategy',
    'SpaceGroup',
    'Feedback',
    'ActivityLog',
    'delete',
    'archive',
    'perform_action',
    ]   

