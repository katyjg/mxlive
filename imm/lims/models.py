# -*- coding: utf-8 -*-
import datetime

from django.db import models
from django.contrib.auth.models import User
from django.contrib.contenttypes.models import ContentType
from imm.enum import Enum
from jsonfield import JSONField
import logging

from django.db.models.signals import post_save
from django.db.models.signals import pre_delete
from django.db.models.signals import pre_save
from django.db.models.signals import post_delete
from django.core.exceptions import ObjectDoesNotExist

IDENTITY_FORMAT = '.%y.%m.%d'
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

    
class Laboratory(models.Model):
    name = models.CharField(max_length=600)
    address = models.CharField(max_length=600)
    city = models.CharField(max_length=180)
    postal_code = models.CharField(max_length=30)
    country = models.CharField(max_length=180)
    contact_phone = models.CharField(max_length=60)
    contact_fax = models.CharField(max_length=60)
    organisation = models.CharField(max_length=600, blank=True, null=True)
    created = models.DateTimeField('date created', auto_now_add=True, editable=False)
    modified = models.DateTimeField('date modified',auto_now=True, editable=False)

    def __unicode__(self):
        return self.name
    
    class Meta:
        verbose_name_plural = 'Laboratories'
        
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
    results from the query_set. All it does it proxy all requests to the wrapped manager EXCEPT
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
        
class Project(models.Model):
    user = models.ForeignKey(User, unique=True)
    permit_no = models.CharField(max_length=20)
    name = models.SlugField()
    title = models.CharField(max_length=200)
    summary = models.TextField()
    beam_time = models.FloatField()
    lab = models.ForeignKey(Laboratory)
    start_date = models.DateField()
    end_date = models.DateField()
    created = models.DateTimeField('date created', auto_now_add=True, editable=False)
    modified = models.DateTimeField('date modified',auto_now=True, editable=False)
    
    def identity(self):
        return 'PR%03d%s' % (self.id, self.created.strftime(IDENTITY_FORMAT))
        
    def __unicode__(self):
        return self.name


class Session(models.Model):
    project = models.ForeignKey(Project)
    beamline = models.ForeignKey(Beamline)
    start_time = models.DateTimeField(null=False, blank=False)
    end_time = models.DateTimeField(null=False, blank=False)
    comments = models.TextField()
    

class Constituent(models.Model):
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
    project = models.ForeignKey(Project)
    name = models.CharField(max_length=60)
    acronym = models.SlugField(max_length=20) 
    source = models.IntegerField(max_length=1, choices=SOURCES.get_choices(), default=SOURCES.UNKNOWN)
    kind = models.IntegerField('type', max_length=1, choices=TYPES.get_choices(), default=TYPES.PROTEIN)
    is_radioactive = models.BooleanField()
    is_contaminant = models.BooleanField()
    is_toxic = models.BooleanField()
    is_oxidising = models.BooleanField()
    is_explosive = models.BooleanField()
    is_corrosive = models.BooleanField()
    is_inflamable = models.BooleanField()
    is_biological_hazard = models.BooleanField()
    hazard_details = models.TextField(blank=True)
    created = models.DateTimeField('date created', auto_now_add=True, editable=False)
    modified = models.DateTimeField('date modified',auto_now=True, editable=False)
    
    FIELD_TO_ENUM = {
        'source': SOURCES,
        'kind': TYPES,
    }

    def get_hazard_designation(self):
        HD_DICT = {
            '☢': self.is_radioactive ,
            '⚠': self.is_contaminant,
            '☠': self.is_toxic,
            'O': self.is_oxidising,
            '☄': self.is_explosive,
            'C': self.is_corrosive,
            'F': self.is_inflamable,
            '☣': self.is_biological_hazard,
        }

        hd = [ k for k,v in HD_DICT.items() if v ]
        return ''.join(hd)
        
    def __unicode__(self):
        return "%s - %s" % (self.acronym, self.name)
        
    def identity(self):
        return 'CO%03d%s' % (self.id, self.created.strftime(IDENTITY_FORMAT))
    
    def _cocktail(self, cocktail):
        self.cocktail_set.add(cocktail)
    
    cocktail = property(None, _cocktail)
        
class Carrier(models.Model):
    name = models.CharField(max_length=60)
    phone_number = models.CharField(max_length=20)
    fax_number = models.CharField(max_length=20)
    code_regex = models.CharField(max_length=60)
    url = models.URLField()

    def __unicode__(self):
        return self.name
    
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
    logging.info("Changing status of '%s.%s': '%s' -> '%s'" % (instance.__class__, instance.pk, instance.STATES[instance.status], instance.STATES[status]))
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
    
    def accept(self):
        return "dewar"
    
    def num_dewars(self):
        return self.dewar_set.count()
    
    def is_empty(self):
        return self.dewar_set.count() == 0
    
    def __unicode__(self):
        return "%s" % (self.label)

    def identity(self):
        return 'SH%03d%s' % (self.id, self.created.strftime(IDENTITY_FORMAT))
    
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
        for crystal in self.project.crystal_set.all():
            if not crystal.is_assigned():
                errors.append("Crystal (%s) not in Container" % crystal.name)
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
            experiment = Experiment(project=self.project, name='Default Experiment')
            experiment.save()
            for unassociated_crystal in unassociated_crystals:
                unassociated_crystal.experiment = experiment
                unassociated_crystal.save()
#            experiment.save()
    
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
    
    def is_xlsable(self):
        return self.is_sendable() or self.status >= self.STATES.SENT
    
    def is_closable(self):
        return self.status == self.STATES.RETURNED 
    
    def is_receivable(self):
        return self.status == self.STATES.SENT 
    
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
        'label': "This should be an externally visible label on the dewar",
        'code': "If there is a barcode on the dewar, please scan the value here",
        'comments': "Use this field to jot notes related to this shipment for your own use",
    }
    project = models.ForeignKey(Project)
    label = models.CharField(max_length=60, help_text=HELP['label'])
    code = models.CharField(max_length=128, blank=True, help_text=HELP['code'])
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

    def identity(self):
        return 'DE%03d%s' % (self.id, self.created.strftime(IDENTITY_FORMAT))
    
    def barcode(self):
        return self.code or self.label
    
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
        'Basket', 
        'Carousel',
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
            self.TYPE.BASKET: 8,
            self.TYPE.CAROUSEL: 8,
        }
        return _cap[self.kind]
        
    def is_assigned(self):
        return self.dewar is not None
    
    def get_location_choices(self):
        vp = self.valid_locations()
        return tuple([(a,a) for a in vp])
            
    def valid_locations(self):
        if self.kind == self.TYPE.CASSETTE:
            all_positions = ["ABCDEFGHIJKL"[x/8]+str(1+x%8) for x in range(self.capacity()) ]
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
        for location in self.valid_locations():
            xtl = None
            for crystal in self.crystal_set.all():
                if crystal.container_location == location:
                    xtl = crystal
            retval.append((location, xtl))
        return retval
        
    def __unicode__(self):
        return self.label

    def identity(self):
        return 'CN%03d%s' % (self.id, self.created.strftime(IDENTITY_FORMAT))
    
    def barcode(self):
        return self.code or self.label
    
    def get_children(self):
        return self.crystal_set.all()
    
    def is_editable(self):
        return self.status == self.STATES.DRAFT 
    
    def get_form_field(self):
        return 'container'
    
    def json_dict(self):
        return {
            'project_id': self.project.pk,
            'id': self.pk,
            'name': self.label,
            'type': Container.TYPE[self.kind],
            'load_position': 'TODO',
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
        return '%s %c%c ' % (self.name, self.crystal_system, self.lattice_type)
    
class CrystalForm(models.Model):
    project = models.ForeignKey(Project)
    name = models.CharField(max_length=60)
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
        return "%s" % (self.name)

    def identity(self):
        return 'CF%03d%s' % (self.id, self.created.strftime(IDENTITY_FORMAT))
    
    class Meta:
        verbose_name = 'Crystal Form'


        
class Cocktail(models.Model):
    project = models.ForeignKey(Project)
    constituents = models.ManyToManyField(Constituent)
    comments = models.TextField(blank=True, null=True)
    created = models.DateTimeField('date created', auto_now_add=True, editable=False)
    modified = models.DateTimeField('date modified',auto_now=True, editable=False)
    
    NAME_JOIN_STRING = '/'
    
    def name(self):
        names = sorted([c.acronym for c in self.constituents.all()])
        return self.NAME_JOIN_STRING.join(names)
        
    def __unicode__(self):
        return self.name()

    def identity(self):
        return 'CT%03d%s' % (self.id, self.created.strftime(IDENTITY_FORMAT))


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
        'Closed',
    )  
    TRANSITIONS = {
        STATES.DRAFT: [STATES.ACTIVE],
        STATES.ACTIVE: [STATES.PROCESSING],
        STATES.PROCESSING: [STATES.PAUSED],
        STATES.PAUSED: [STATES.CLOSED],
    }

    ACTIONS = {
        'resubmit': { 'status': STATES.ACTIVE, 'methods': ['set_strategy_status_resubmitted',] },
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
    created = models.DateTimeField('date created', auto_now_add=True, editable=False)
    modified = models.DateTimeField('date modified',auto_now=True, editable=False)
#    crystals = models.ManyToManyField(Crystal)
    priority = models.IntegerField(default=0)
    staff_priority = models.IntegerField(default=0)
    
    FIELD_TO_ENUM = {
        'status': STATES,
        'kind': EXP_TYPES,
        'plan': EXP_PLANS,
    }
    
    def get_crystals(self):
        return Crystal.objects.filter(experiment=self)
    
    crystals = property(get_crystals)
    
    def accept(self):
        return "crystal"
    
    def num_crystals(self):
        return self.crystals.count()
    
    def update_priority(self):
        """ Updates the priority/staff_priority of all associated Containers """
        for crystal in self.crystals.all():
            if crystal.container:
                crystal.container.update_priority()
                crystal.container.save()
    
    def __unicode__(self):
        return self.identity()

    def identity(self):
        return 'EX%03d%s' % (self.id, self.created.strftime(IDENTITY_FORMAT))    
    
    def is_editable(self):
        return self.status == self.STATES.DRAFT
    
    def get_form_field(self):
        return 'experiment'

    def get_children(self):
        return []

    def set_strategy_status_resubmitted(self, data=None):
        strategy = data['strategy']
        perform_action(strategy, 'resubmit')
        
    def best_crystal(self):
        if self.plan == Experiment.EXP_PLANS.RANK_AND_COLLECT_BEST:
            results = Result.objects.filter(experiment=self, crystal__in=self.crystals.all()).order_by('-score')
            if results:
                return results[0].crystal.pk
        
    def json_dict(self):
        """ Returns a json dictionary of the Runlist """
        return {
            'project_id': self.project.pk,
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
    priority = models.IntegerField(default=0)
    staff_priority = models.IntegerField(default=0)
    experiment = models.ForeignKey(Experiment, null=True, blank=True)
    
    FIELD_TO_ENUM = {
        'status': STATES,
    }
    
    class Meta:
        unique_together = (
            ("project", "container", "container_location"),
            ("project","name"),
        )
        
    def __unicode__(self):
        return '%s / %s' % (self.name, self.identity())

    def is_assigned(self):
        return self.container is not None
    
    def num_experiments(self):
        if self.experiment:
            return 1
        return 0

    def identity(self):
        return 'XT%03d%s' % (self.id, self.created.strftime(IDENTITY_FORMAT))
    
    def barcode(self):
        return self.code or self.name
    
    def get_children(self):
        return []
    
    def activate_associated_experiments(self, data=None):
        """ Updates the status of the associated Experiment to 'Active' if all the Crystals are 'On-Site'
        """
        assert self.experiment
        all_crystals_received = True
        for crystal in self.experiment.crystal_set.all():
            all_crystals_received = all_crystals_received and crystal.status == Crystal.STATES.ON_SITE
        if all_crystals_received:
            self.experiment.status = Experiment.STATES.ACTIVE
            self.experiment.save()
#        
#        for experiment in self.experiment_set.all():
#            all_crystals_received = True
#            for crystal in experiment.crystals.all():
#                all_crystals_received = all_crystals_received and crystal.status == Crystal.STATES.ON_SITE
#            if all_crystals_received:
#                experiment.status = Experiment.STATES.ACTIVE
#                experiment.save()
                
    def is_editable(self):
        return self.status == self.STATES.DRAFT 
    
    def is_deletable(self):
        return self.status == self.STATES.DRAFT
    
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
        
#    def _experiment(self, experiment):
#        self.experiment_set.add(experiment)
#    
#    experiment = property(None, _experiment)

        
# The following set of pre/post save/delete methods are responsible for updating the priority of
# a Runlist Container to the maximum priority of the associated Experiments. Container.priority/staff_priority 
# are currently calculated values, so it might have made sense to use a SQL view for lims_container
# rather than adding the fields directly. It is pretty easy to anticipate a scenario where this is not
# always the case, so we added the field to Container, and keep the entities up-to-date whenever Experiment
# instances are saved.
        
def Experiment_post_save(sender, **kwargs):
    experiment = kwargs['instance']
    experiment.update_priority() # does the actual work
    
def Experiment_pre_delete(sender, **kwargs):
    experiment = kwargs['instance']
    # After deletion, the instance has all reference fields nulled, so
    # we need to store the original crystals for use in Experiment_post_delete
    experiment.saved_crystals = [crystal for crystal in experiment.crystals.all()]
    
def Experiment_post_delete(sender, **kwargs):
    experiment = kwargs['instance']
    for crystal in experiment.saved_crystals:
        try:
            crystal.container.update_priority() # does the actual work 
            crystal.container.save()
        except ObjectDoesNotExist:
            pass # ie. Project.delete() called resulting in cascading delete of everything
        
post_save.connect(Experiment_post_save, sender=Experiment)
pre_delete.connect(Experiment_pre_delete, sender=Experiment)
post_delete.connect(Experiment_post_delete, sender=Experiment)
    
class Data(models.Model):
    DATA_TYPES = Enum(
        'Screening',   
        'Collection',
    )
    project = models.ForeignKey(Project)
    experiment = models.ForeignKey(Experiment)
    crystal = models.ForeignKey(Crystal)
    name = models.CharField(max_length=20)
    distance = models.FloatField()
    start_angle = models.FloatField()
    delta_angle = models.FloatField()
    first_frame = models.IntegerField(default=1)
    num_frames = models.IntegerField('No. Images')
    exposure_time = models.FloatField()
    two_theta = models.FloatField()
    wavelength = models.FloatField()
    detector = models.CharField(max_length=20)
    detector_size = models.IntegerField()
    pixel_size = models.FloatField()
    beam_x = models.FloatField()
    beam_y = models.FloatField()
    url = models.CharField(max_length=200)
    kind = models.IntegerField('Data type',max_length=1, choices=DATA_TYPES.get_choices(), default=DATA_TYPES.SCREENING)
    created = models.DateTimeField('date created', auto_now_add=True, editable=False)
    modified = models.DateTimeField('date modified',auto_now=True, editable=False)
    
    FIELD_TO_ENUM = {
        'kind': DATA_TYPES,
    }

    def __unicode__(self):
        return '%s, %d images' % (self.name, self.num_frames)
    
    def total_angle(self):
        return self.delta_angle * self.num_frames
        
    class Meta:
        verbose_name_plural = 'Datasets'
        
    def thumbUrls(self):
        urls = []
        for i in range(self.num_frames):
            urls.append("%s/%s/images/frame_thumb.png" % (self.url, self.pk))
        return urls
    
    def mediumUrls(self):
        urls = []
        for i in range(self.num_frames):
            urls.append("%s/%s/images/frame_medium.png" % (self.url, self.pk))
        return urls
   

class Result(models.Model):
    RESULT_TYPES = Enum(
        'Screening',   
        'Collection',
    )
    project = models.ForeignKey(Project)
    experiment = models.ForeignKey(Experiment)
    crystal = models.ForeignKey(Crystal)
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

    def __unicode__(self):
        return self.identity()

    def is_resubmittable(self):
        for strategy in self.strategy_set.all():
            if strategy.is_resubmittable():
                return True
        return False

    def get_results_link(self):
        strategy = self.strategy_set.all()[0]
        experimentName = RESUMBITTED_LABEL + strategy.name + '_' + strategy.result.crystal.name
        link = "resubmit/?%s=%d&%s=%d&%s=%s&%s=%f&%s=%f&%s=%f&%s=%f&%s=%f&%s=%f&%s=%f&%s=%s&%s=%d" % \
        ('project',       strategy.project.pk,
         'strategy',      strategy.pk,
         'name',          experimentName,
         'delta_angle',   strategy.delta_angle,
         'total_angle',   strategy.total_angle,
         'energy',        strategy.energy,
         'resolution',    strategy.exp_resolution,
         'multiplicity',  strategy.exp_multiplicity,
         'i_sigma',       strategy.exp_i_sigma,
         'r_meas',        strategy.exp_r_factor,
         'crystals',      strategy.result.crystal.pk,
         'plan',          self.experiment.EXP_PLANS.JUST_COLLECT # all resubmitted experiments must use this type
        )
        return link

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

    def __unicode__(self):
        return self.identity()

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
    experiment = models.ForeignKey(Experiment)
    crystal = models.ForeignKey(Crystal)
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
    
    def __unicode__(self):
        return self.identity()

    
class ActivityLogManager(models.Manager):
    def log_activity(self, project_id, user_id, ip_number, content_type_id, object_id, object_repr, action_type, description=''):
        e = self.model(None, None, project_id, user_id,  ip_number, content_type_id, str(object_id), object_repr, action_type, description)
        e.save()
    
class ActivityLog(models.Model):
    TYPE = Enum('Login', 'Logout', 'Task','Create', 'Modify','Delete', 'Archive')
    created = models.DateTimeField('date/time', auto_now_add=True, editable=False)
    project = models.ForeignKey(Project)
    user = models.ForeignKey(User)
    ip_number = models.IPAddressField('IP Address')
    content_type = models.ForeignKey(ContentType, blank=True, null=True)
    object_id = models.CharField(max_length=20, blank=True, null=True)
    object_repr = models.CharField(max_length=200, blank=True, null=True)
    action_type = models.IntegerField(max_length=1, choices=TYPE.get_choices() )
    description = models.TextField(blank=True)
    
    objects = ActivityLogManager()

    class Meta:
        ordering = ('-created',)
    
    def __unicode__(self):
        return str(self.created)
    
def delete(model, id, orphan_models):
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
    'Laboratory',
    'Project',
    'Session',
    'Beamline',
    'Constituent',
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
    'ActivityLog',
    'Carrier',
    'delete',
    'archive',
    'perform_action',
    ]   

def ActivityLog_pre_save(sender, **kwargs):
    """ pre_save handler """
    # values in the current (to be saved) instance
    instance = kwargs['instance']
    instanceVars = vars(instance)
    
    try:
        # values in the existing (already in db) instance
        existingInstance = sender._default_manager.get(pk=instance.pk)
        existingInstanceVars = vars(existingInstance)
        
        # flag to indicate an ActivityLog MODIFY or CREATED entity
        instance._ActivityLog_type = None
        changes = {}
        
        # iterate of the dictionaries to see if anything notable has changed
        for key in set(instanceVars.keys() + existingInstanceVars.keys()):
            if key in ['created', 'modified'] or key.startswith('_') or key.startswith('tmp_'):
                continue
            if instanceVars.get(key) != existingInstanceVars.get(key):
                changes[key] = (existingInstanceVars.get(key), instanceVars.get(key))
                
        # if there are changes, construct a message for the ActivityLog entry that shows the changes
        # to each field in the format "field": "oldValue" -> "newValue"
        if changes:
            instance._ActivityLog_type = ActivityLog.TYPE.MODIFY
            messages = []
            for key, value in changes.items():
                value = list(value)
                for i, v in enumerate(value):
                    if isinstance(v, basestring):
                        value[i] = '"%s"' % v
                    elif hasattr(sender, 'FIELD_TO_ENUM'):
                        if sender.FIELD_TO_ENUM.has_key(key):
                            value[i] = '"%s"' % sender.FIELD_TO_ENUM[key][v]
                messages.append('%s: %s -> %s' % (key, value[0], value[1]))
            instance._ActivityLog_message = ','.join(messages)
            
    except sender.DoesNotExist:
        # this is a new entity, create a simple ActivityLog entry
        instance._ActivityLog_type = ActivityLog.TYPE.CREATE
        instance._ActivityLog_message = 'Created'
        
def ActivityLog_post_save(sender, **kwargs):
    """ post_save handler """
    # if the instance was created of changed, then create an ActivityLog entry
    instance = kwargs['instance']
    if instance._ActivityLog_type is not None:
        project = instance.project
        ActivityLog.objects.log_activity(
                project.pk,
                project.user.pk,
                '0.0.0.0', # no access to request object, just use a dummy IP address
                ContentType.objects.get_for_model(sender).id,
                instance.pk, 
                str(instance), 
                instance._ActivityLog_type,
                instance._ActivityLog_message,
                )
        
ACTIVITY_LOG_MODELS = [Constituent, Cocktail, Crystal, CrystalForm, Shipment, Container,  Dewar,
                       Experiment, ScanResult, Result, Data, Strategy]

def connectActivityLog():
    """ Hooks ActivityLog_post_save to all relevant models """
    for modelClass in ACTIVITY_LOG_MODELS:
        pre_save.connect(ActivityLog_pre_save, sender=modelClass)
        post_save.connect(ActivityLog_post_save, sender=modelClass)
        
def disconnectActivityLog():
    """ Unhooks ActivityLog_post_save from all relevant models """
    for modelClass in ACTIVITY_LOG_MODELS:
        pre_save.disconnect(ActivityLog_pre_save, sender=modelClass)
        post_save.disconnect(ActivityLog_post_save, sender=modelClass)
        
connectActivityLog()
    