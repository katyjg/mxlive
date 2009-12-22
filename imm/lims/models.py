# -*- coding: utf-8 -*-

from django.db import models
from django.contrib.auth.models import User
from django.contrib.contenttypes.models import ContentType
from imm.enum import Enum
from jsonfield import JSONField


IDENTITY_FORMAT = '.%y.%m.%d'
OBJECT_STATES = Enum(
    'ACTIVE', 
    'ARCHIVED', 
    'DELETED')

def cassette_loc_repr(pos):
    return "ABCDEFGHIJKL"[pos/8]+str(1+pos%8)
    
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
            
    
class Project(models.Model):
    user = models.ForeignKey(User, unique=True)
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

class BeamUsage(models.Model):
    project = models.ForeignKey(Project)
    start_time = models.DateTimeField(null=False, blank=False)
    end_time = models.DateTimeField(null=False, blank=False)
    description = models.CharField(max_length=200)
    

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
        
class Carrier(models.Model):
    name = models.CharField(max_length=60)
    phone_number = models.CharField(max_length=20)
    fax_number = models.CharField(max_length=20)
    code_regex = models.CharField(max_length=60)
    url = models.URLField()

    def __unicode__(self):
        return self.name
    
class Shipment(models.Model):
    STATES = Enum(
        'Draft', 
        'Sent', 
        'On-site', 
        'Returned', 
        'Archived',
    )
    HELP = {
        'label': "This should be an externally visible label",
        'code': "Barcode",
        'comments': "Use this field to jot notes related to this shipment for your own use",
    }
    project = models.ForeignKey(Project)
    label = models.CharField(max_length=60)
    comments = models.TextField(blank=True, null=True, max_length=200)
    tracking_code = models.CharField(blank=True, null=True, max_length=60)
    return_code = models.CharField(blank=True, null=True, max_length=60)
    date_shipped = models.DateTimeField(null=True, blank=True)
    date_received = models.DateTimeField(null=True, blank=True)
    date_returned = models.DateTimeField(null=True, blank=True)
    status = models.IntegerField(max_length=1, choices=STATES.get_choices(), default=STATES.DRAFT)
    carrier = models.ForeignKey(Carrier, null=True, blank=True)
    created = models.DateTimeField('date created', auto_now_add=True, editable=False)
    modified = models.DateTimeField('date modified',auto_now=True, editable=False)

    def num_dewars(self):
        return self.dewar_set.count()
    
    def is_empty(self):
        return self.dewar_set.count() == 0
    
    def __unicode__(self):
        return "%s" % (self.label)

    def identity(self):
        return 'SH%03d%s' % (self.id, self.created.strftime(IDENTITY_FORMAT))
    
class Dewar(models.Model):
    HELP = {
        'label': "This should be an externally visible label on the dewar",
        'code': "If there is a barcode on the dewar, please scan the value here",
        'comments': "Use this field to jot notes related to this shipment for your own use",
    }
    project = models.ForeignKey(Project)
    label = models.CharField(max_length=60, help_text=HELP['label'])
    code = models.CharField(max_length=150, blank=True, help_text=HELP['code'])
    comments = models.TextField(blank=True, null=True, help_text=HELP['comments'])
    storage_location = models.CharField(max_length=60, null=True, blank=True)
    shipment = models.ForeignKey(Shipment, blank=True, null=True)
    created = models.DateTimeField('date created', auto_now_add=True, editable=False)
    modified = models.DateTimeField('date modified',auto_now=True, editable=False)
    
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

class Container(models.Model):
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
        vc = []
        if self.kind == self.TYPE.CASSETTE:
            for x in vp: vc.append((cassette_loc_repr(x), x))
        else:
            for x in vp: vc.append((str(x), x))
        return tuple(vc)
            
    
    def location_is_valid(self, loc):
        if  self.kind == self.TYPE.CASSETTE:
            all_positions = ["ABCDEFGHIJKL"[x/8]+str(1+x%8) for x in range(self.capacity()) ]
        else:
            all_positions = [ str(x+1) for x in range(self.capacity()) ]
        return loc in all_positions
    
    def location_is_available(self, loc, id=None):
        occupied_positions = [xtl.container_location for xtl in self.crystal_set.all().exclude(pk=id) ]
        return loc not in occupied_positions
        
    def __unicode__(self):
        return self.label

    def identity(self):
        return 'CN%03d%s' % (self.id, self.created.strftime(IDENTITY_FORMAT))

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
    
    id = models.IntegerField(primary_key=True)
    name = models.CharField(max_length=20)
    crystal_system = models.CharField(max_length=1, choices=CS_CHOICES)
    lattice_type = models.CharField(max_length=1, choices=LT_CHOICES)
    
    def __unicode__(self):
        return '%s #%d %c%c ' % (self.name, self.id, self.crystal_system, self.lattice_type)
    
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
    
    def name(self):
        names = [c.acronym for c in self.constituents.all()]
        return '/'.join(names)
        
    def __unicode__(self):
        return self.name()

    def identity(self):
        return 'CT%03d%s' % (self.id, self.created.strftime(IDENTITY_FORMAT))

     
class Crystal(models.Model):
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
    
    class Meta:
        unique_together = (
            ("project", "container", "container_location"),
            ("project","name"),
        )
        
    def __unicode__(self):
        return '%s / %s' % (self.name, self.identity())

    def is_assigned(self):
        return self.container is not None

    def identity(self):
        return 'XT%03d%s' % (self.id, self.created.strftime(IDENTITY_FORMAT))

class Experiment(models.Model):
    EXP_TYPES = Enum(
        'Native',   
        'MAD',
        'SAD',
    )
    EXP_PLANS = Enum(
        'Rank and collect best',
        'Rank and confirm',
        'Collect first good',
        'Screen and confirm',
        'Screen and collect'
    )
    STATES = Enum(
        'Draft', 
        'Active',
        'Processing', 
        'Paused', 
        'Closed',
    )  
    project = models.ForeignKey(Project)
    name = models.CharField(max_length=60)
    hi_res = models.FloatField(null=True, blank=True)
    lo_res = models.FloatField(null=True, blank=True)
    i_sigma = models.FloatField('I/Sigma', null=True, blank=True)
    r_meas =  models.FloatField(null=True, blank=True)
    multiplicity = models.IntegerField(null=True, blank=True)
    energy = models.DecimalField(null=True, max_digits=10, decimal_places=4, blank=True)
    kind = models.IntegerField('exp. type',max_length=1, choices=EXP_TYPES.get_choices(), default=EXP_TYPES.NATIVE)
    absorption_edge = models.CharField(max_length=5, null=True, blank=True)
    plan = models.IntegerField(max_length=1, choices=EXP_PLANS.get_choices(), default=EXP_PLANS.SCREEN_AND_CONFIRM)
    comments = models.TextField(blank=True, null=True)
    status = models.IntegerField(max_length=1, choices=STATES.get_choices(), default=STATES.DRAFT)
    created = models.DateTimeField('date created', auto_now_add=True, editable=False)
    modified = models.DateTimeField('date modified',auto_now=True, editable=False)
    crystals = models.ManyToManyField(Crystal)
    
    def num_crystals(self):
        return self.crystals.count()
    
    def __unicode__(self):
        return self.identity()

    def identity(self):
        return 'EX%03d%s' % (self.id, self.created.strftime(IDENTITY_FORMAT))
    
class Strategy(models.Model):
    STATES = Enum(
        'Waiting', 
        'Rejected',
        'Accepted', 
        'Collected',
    )  
    project = models.ForeignKey(Project)
    attenuation = models.FloatField()
    distance = models.FloatField(default=200.0)
    start_angle = models.FloatField(default=0.0)
    delta_angle = models.FloatField(default=1.0)
    total_angle = models.FloatField(default=180.0)
    exposure_time = models.FloatField(default=1.0)
    two_theta = models.FloatField(default=0.0)
    energy = models.FloatField(default=12.658)
    status = models.IntegerField(max_length=1, choices=STATES.get_choices(), default=STATES.WAITING)
    created = models.DateTimeField('date created', auto_now_add=True, editable=False)
    modified = models.DateTimeField('date modified',auto_now=True, editable=False)

    def identity(self):
        return 'ST%03d%s' % (self.id, self.created.strftime(IDENTITY_FORMAT))

    def __unicode__(self):
        return self.identity()
    

class Result(models.Model):
    RESULT_TYPES = Enum(
        'Screening',   
        'Collection',
    )
    project = models.ForeignKey(Project)
    experiment = models.ForeignKey(Experiment)
    crystal = models.ForeignKey(Crystal)
    name = models.CharField(max_length=200)
    score = models.FloatField()
    space_group = models.ForeignKey(SpaceGroup)
    cell_a = models.FloatField(' a')
    cell_b = models.FloatField(' b')
    cell_c = models.FloatField(' c')
    cell_alpha = models.FloatField(' alpha')
    cell_beta = models.FloatField(' beta')
    cell_gamma = models.FloatField(' gamma')
    resolution = models.FloatField()
    reflections = models.IntegerField()
    unique = models.IntegerField()
    multiplicity = models.FloatField()
    completeness = models.FloatField()
    mosaicity = models.FloatField()
    i_sigma = models.FloatField('I/Sigma')
    r_meas =  models.FloatField('R-meas')
    r_mrgd = models.FloatField('R-mrgd-F')
    sigma_spot = models.FloatField('Sigma(spot)')
    sigma_angle = models.FloatField('Sigma(angle)')
    ice_rings = models.IntegerField()
    url = models.CharField(max_length=200)
    strategy = models.ForeignKey(Strategy)
    kind = models.IntegerField('Result type',max_length=1, choices=RESULT_TYPES.get_choices())
    details = JSONField()
    created = models.DateTimeField('date created', auto_now_add=True, editable=False)
    modified = models.DateTimeField('date modified',auto_now=True, editable=False)
    
    def identity(self):
        return 'RT%03d%s' % (self.id, self.created.strftime(IDENTITY_FORMAT))
    
    
class ActivityLogManager(models.Manager):
    def log_activity(self, project_id, user_id, ip_number, content_type_id, object_id, object_repr, action_type, description=''):
        e = self.model(None, None, project_id, user_id,  ip_number, content_type_id, str(object_id), object_repr, action_type, description)
        e.save()
    
class ActivityLog(models.Model):
    TYPE = Enum('Login', 'Logout', 'Task','Create', 'Modify','Delete')
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

from django.contrib import databrowse
_databrowse_model_list = [Project, 
            Laboratory, 
            Constituent, 
            Carrier,
            Shipment,
            Dewar,
            Container,
            SpaceGroup,
            CrystalForm,
            Cocktail,
            Crystal,
            Experiment,
            Result,
            ActivityLog,
            Strategy,
            ]
            
for mod in _databrowse_model_list:
    databrowse.site.register(mod)
    
__all__ = [
    'Laboratory',
    'Project',
    'BeamUsage',
    'Constituent',
    'Cocktail',
    'Crystal',
    'CrystalForm',
    'Shipment',
    'Container',
    'Dewar',
    'Experiment',
    'Result',
    'Strategy',
    'SpaceGroup',
    'ActivityLog',
    'Carrier',
    ]   
