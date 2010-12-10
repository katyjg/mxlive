import unittest
import mocker
import datetime
import os

from django.conf import settings
from django.contrib.auth.models import User
from django.db import connection
from django.core.management.color import no_style
from django.core.management.sql import sql_flush
from django.http import HttpRequest
from django.http import HttpResponse
from django.db.models.query import QuerySet
from django.utils.datastructures import MultiValueDict

# DO NOT REMOVE
import imm.lims.admin
import imm.messaging.admin
# DO NOT REMOVE

from imm.lims.models import Beamline
from imm.lims.models import Laboratory
from imm.lims.models import Project
from imm.lims.models import Shipment
from imm.lims.models import Dewar
from imm.lims.models import Container
from imm.lims.models import Crystal
from imm.lims.models import Experiment
from imm.lims.models import Carrier
from imm.lims.models import Strategy
from imm.lims.models import Data
from imm.lims.models import Result
from imm.lims.models import SpaceGroup
from imm.lims.models import CrystalForm

from imm.staff.models import Runlist
from imm.staff.models import AutomounterLayout

TEST_FILES = os.path.join(os.path.dirname(__file__), 'xls/')

class DjangoTestCase(unittest.TestCase):
    
    def _flush_db_tables(self):
        """ Flushes all of the tables currently in the DB """
        sql_list = sql_flush(no_style(), connection, only_django=True)
        try:
            cursor = connection.cursor()
            for sql in sql_list:
                cursor.execute(sql)
        except Exception, e:
            raise e
        
    def setUp(self):
        """ Sets up the test class """
        self._flush_db_tables()
        self.user = None
        self.adminuser = None
        self.project = None
        self.shipment = None
        self.dewar = None
        self.container = None
        self.space_group = None
        self.crystal_form = None
        self.crystal = None
        self.experiment = None
        self.strategy = None
        self.data = None
        self.result = None
        self.runlist = None
        self.lab = None
        self.mock = None
    
    def tearDown(self):
        """ Tears down the test class """
        if self.mock:
            self.mock.restore()
        
    def mock_out_render_to_response(self):
        """ Mocks out django.shortcuts.render_to_response with self.render_to_response """
        self.mock = mocker.Mocker()
        render_to_response = self.mock.replace('django.shortcuts.render_to_response')
        render_to_response(mocker.ARGS, mocker.KWARGS)
        self.mock.call(self.render_to_response)
        self.mock.count(0, 100)
        self.mock.replay()
        
    def set_up_default_user(self):
        """ Sets up a default User
        """
        self.user = getattr(self, 'user', None) or create_User()
        
    def set_up_default_adminuser(self):
        """ Sets up a default User
        """
        self.adminuser = getattr(self, 'adminuser', None) or create_User(username=settings.ADMIN_MESSAGE_USERNAME, is_superuser=True)
        
    def set_up_default_laboratory(self):
        """ Sets up a default Laboratory
        """
        self.lab = getattr(self, 'lab', None) or create_Laboratory()
        
    def set_up_default_carrier(self):
        """ Sets up a default Carrier
        """
        self.carrier = getattr(self, 'carrier', None) or create_Carrier()
        
    def set_up_default_project(self):
        """ Sets up a default Project (and reqd User and Laboratory) so that @project_required
        decorator always works
        """
        self.set_up_default_user()
        self.set_up_default_laboratory()
        self.project = getattr(self, 'project', None) or create_Project(user=self.user, lab=self.lab)
        
    def set_up_default_shipment(self):
        """ Sets up a default Shipment """
        self.set_up_default_project()
        self.shipment = getattr(self, 'shipment', None) or create_Shipment(project=self.project)
        
    def set_up_default_dewar(self):
        """ Sets up a default Dewar
        """
        self.set_up_default_shipment()
        self.dewar = getattr(self, 'dewar', None) or create_Dewar(project=self.project, shipment=self.shipment, label='dewar123')
        
    def set_up_default_container(self):
        """ Sets up a default Container
        """
        self.set_up_default_dewar()
        self.container = getattr(self, 'container', None) or create_Container(project=self.project, dewar=self.dewar, label='container123')
        
    def set_up_default_space_group(self, name='SpaceGroup'):
        """ Sets up a default SpaceGroup
        """
        self.space_group = getattr(self, 'space_group', None) or create_SpaceGroup(name=name)
        
    def set_up_default_crystal_form(self):
        """ Sets up a default CrystalForm
        """
        self.set_up_default_project()
        self.set_up_default_space_group()
        self.crystal_form = getattr(self, 'crystal_form', None) or create_CrystalForm(project=self.project, space_group=self.space_group)
        
    def set_up_default_crystal(self):
        """ Sets up a default Crystal and all associated/valid Containers/Dewars etc.
        """
        self.set_up_default_container()
        self.set_up_default_crystal_form()
        self.crystal = getattr(self, 'crystal', None) or create_Crystal(project=self.project, container=self.container, container_location='A1', name='crystal123',
                                                                        code='abc123', crystal_form=self.crystal_form)
        #print self.crystal.crystal_form.space_group
        
    def set_up_default_experiment(self):
        """ Sets up a default Experiment.
        """
        self.set_up_default_crystal()
        self.experiment = getattr(self, 'experiment', None) or create_Experiment(project=self.project, name='experiment123')
#        self.experiment.crystals.add(self.crystal)
        self.experiment.save()
        self.crystal.experiment = self.experiment
        self.crystal.save()
#        assert 0 < self.crystal.experiment_set.count()
        
    def set_up_default_data(self):
        """ Sets up a default Data.
        """
        self.set_up_default_experiment()
        self.set_up_default_crystal()
        self.data = getattr(self, 'data', None) or create_Data(project=self.project, experiment=self.experiment, crystal=self.crystal)
        
    def set_up_default_result(self):
        """ Sets up a default Result.
        """
        self.set_up_default_data()
        self.result = getattr(self, 'result', None) or create_Result(project=self.project, experiment=self.experiment, crystal=self.crystal, data=self.data)
        
    def set_up_default_strategy(self):
        """ Sets up a default Experiment.
        """
        self.set_up_default_result()
        self.strategy = getattr(self, 'strategy', None) or create_Strategy(project=self.project, result=self.result)
        
    def set_up_default_runlist(self):
        """ Sets up a default Experiment.
        """
        self.set_up_default_experiment()
        self.set_up_default_container()
        self.runlist = getattr(self, 'runlist', None) or create_Runlist(containers=[self.container], experiments=[self.experiment], name='runlist123')
        assert len(self.runlist.experiments.all()) == 1
        assert self.runlist.experiments.all()[0] == self.experiment
        
    def reload_models(self):
        """ Reloads the self.* Models from the database """
        if self.project:
            self.project = Project.objects.get(id=self.project.id)
        if self.shipment:
            self.shipment = Shipment.objects.get(id=self.shipment.id)
        if self.dewar:
            self.dewar = Dewar.objects.get(id=self.dewar.id)
        if self.container:
            self.container = Container.objects.get(id=self.container.id)
        if self.crystal:
            self.crystal = Crystal.objects.get(id=self.crystal.id)
        if self.experiment:
            self.experiment = Experiment.objects.get(id=self.experiment.id)
        if self.runlist:
            self.runlist = Runlist.objects.get(id=self.runlist.id)
        if self.strategy:
            self.strategy = Strategy.objects.get(id=self.strategy.id)
        if self.data:
            self.data = Data.objects.get(id=self.data.id)
        if self.result:
            self.result = Result.objects.get(id=self.result.id)
        if self.space_group:
            self.space_group = SpaceGroup.objects.get(id=self.space_group.id)
        if self.crystal_form:
            self.crystal_form = CrystalForm.objects.get(id=self.crystal_form.id)
            
    def get_request(self, data=None, is_superuser=False):
        """ Returns an HttpRequest with request.user initialized to self.user """
        request = HttpRequest()
        request.GET = MultiValueDict()
        request.POST = MultiValueDict()
        request.method = 'GET'
        request.META['REMOTE_ADDR'] = '127.0.0.1'
        if data:
            request.GET.update(data)
        request.user = self.user
        if is_superuser:
            request.user = self.adminuser
        request.project = None # DO NOT set to self.project !!!!
        return request
        
    def post_request(self, data=None, files=None, is_superuser=False):
        """ Returns an HttpRequest with request.user initialized to self.user """
        request = HttpRequest()
        request.GET = MultiValueDict()
        request.POST = MultiValueDict()
        request.method = 'POST'
        request.META['REMOTE_ADDR'] = '127.0.0.1'
        if data:
            request.POST.update(data)
        if files:
            request.FILES.update(files)
        request.user = self.user
        if is_superuser:
            request.user = self.adminuser
        request.project = None # DO NOT set to self.project !!!!
        return request
    
    def render_to_response(self, *args, **kwargs):
        """ Used when mocking render_to_reponse - it simply stores the rendered args/kwargs on the
        response, rather than actually going through the templating system
        """
        response = HttpResponse()
        response.rendered_args = args
        response.rendered_kwargs = kwargs
        return response
    
def convert_dict_of_QuerySet_to_dict_of_list(data):
    """ iterates over a nested dict of dict of ... of QuerySet and converts the QuerySets to lists """
    ret = {}
    for key, value in data.items():
        if isinstance(value, dict):
            ret[key] = convert_dict_of_QuerySet_to_dict_of_list(value)
        elif isinstance(value, QuerySet):
            ret[key] = list(value)
        else:
            raise Exception()
    return ret

def convert_ObjectList_to_list(data):
    """ converts an ObjectList to a list """
    return list(data.query_set.all())
            
def create_instance(type, defaults, **kwargs):
    """Create a Instance using a common test interface
    """
    values = dict(defaults)
    values.update(kwargs)
    instance = type(**values)
    instance.save()
    return instance

def create_User(**kwargs):
    """Create a User using a common test interface
    """
    defaults = {}
    return create_instance(User, defaults, **kwargs)

def create_Carrier(**kwargs):
    """Create a Carrier using a common test interface
    """
    defaults = {'name': 'carrier'}
    return create_instance(Carrier, defaults, **kwargs)

def create_Beamline(**kwargs):
    """Create a Beamline using a common test interface
    """
    defaults = {}
    return create_instance(Beamline, defaults, **kwargs)

def create_Laboratory(**kwargs):
    """Create a Laboratory using a common test interface
    """
    defaults = {}
    return create_instance(Laboratory, defaults, **kwargs)

def create_Shipment(**kwargs):
    """Create a Shipment using a common test interface
    """
    defaults = {'tracking_code': 'ups123'}
    return create_instance(Shipment, defaults, **kwargs)

def create_Dewar(**kwargs):
    """Create a Dewar using a common test interface
    """
    defaults = {'code': 'abc123'}
    return create_instance(Dewar, defaults, **kwargs)

def create_Container(**kwargs):
    """Create a Container using a common test interface
    """
    defaults = {'kind' : Container.TYPE.CASSETTE}
    return create_instance(Container, defaults, **kwargs)

def create_SpaceGroup(**kwargs):
    """Create a SpaceGroup using a common test interface
    """
    defaults = {'lattice_type': 1, 
                'crystal_system': 1}
    return create_instance(SpaceGroup, defaults, **kwargs)

def create_CrystalForm(**kwargs):
    """Create a CrystalForm using a common test interface
    """
    defaults = {'name': 'CrystalForm',
                'cell_a': 0.00, 
                'cell_b': 1.00, 
                'cell_c': 2.00,
                'cell_alpha': 0.00, 
                'cell_beta': 1.00, 
                'cell_gamma': 2.00}
    return create_instance(CrystalForm, defaults, **kwargs)

def create_Crystal(**kwargs):
    """Create a Crystal using a common test interface
    """
    defaults = {}
    return create_instance(Crystal, defaults, **kwargs)

def create_Runlist(**kwargs):
    """Create a Runlist using a common test interface
    """
    automounter = AutomounterLayout()
    automounter.save()
    defaults = {'automounter': automounter}
    containers = kwargs.pop('containers', [])
    experiments = kwargs.pop('experiments', [])
    
    instance = create_instance(Runlist, defaults, **kwargs)
    for e in experiments:
        instance.experiments.add(e)
    for c in containers:
        instance.containers.add(c)
    instance.save()
    return instance

def create_Experiment(**kwargs):
    """Create a Experiment using a common test interface
    """
    defaults = {'kind' : Experiment.EXP_TYPES.NATIVE,
                'r_meas' : 1.1,
                'i_sigma' : 1.1,
                'resolution' : 1.1}
    crystals = kwargs.pop('crystals', [])
    instance = create_instance(Experiment, defaults, **kwargs)
    instance.save()
    for c in crystals:
        c.experiment = instance
        c.save()
    return instance

def create_Project(**kwargs):
    """Create a Project using a common test interface
    """
    defaults = {'beam_time' : 0,
                'start_date' : datetime.datetime.now(),
                'end_date' : datetime.datetime.now()}
    return create_instance(Project, defaults, **kwargs)

def create_Data(**kwargs):
    """Create a Data using a common test interface
    """
    defaults = {'resolution': 1,
                'start_angle': 1,
                'delta_angle': 1,
                'frame_sets': '1-2',
                'exposure_time': 1,
                'two_theta': 1,
                'wavelength': 1,
                'detector_size': 1,
                'pixel_size': 1,
                'beam_x': 1,
                'beam_y': 1}
    return create_instance(Data, defaults, **kwargs)

def create_Result(**kwargs):
    """Create a Result using a common test interface
    """
    defaults = {'score': 1,
                'space_group_id': 1,
                'cell_a': 1,
                'cell_b': 1,
                'cell_c': 1,
                'cell_alpha': 1,
                'cell_beta': 1,
                'cell_gamma': 1,
                'resolution': 1,
                'reflections': 1,
                'unique': 1,
                'multiplicity': 1,
                'completeness': 1,
                'mosaicity': 1,
                'i_sigma': 1,
                'r_meas': 1,
                'r_mrgdf': 1,
                'sigma_spot': 1,
                'sigma_angle': 1,
                'ice_rings': 1,
                'kind': Result.RESULT_TYPES.SCREENING,
                'details': 1}
    return create_instance(Result, defaults, **kwargs)

def create_Strategy(**kwargs):
    """Create a Strategy using a common test interface
    """
    defaults = {'attenuation': 1,
                'exp_resolution': 1,
                'exp_completeness': 1,
                'exp_multiplicity': 1,
                'exp_i_sigma': 1,
                'exp_r_factor': 1}
    return create_instance(Strategy, defaults, **kwargs)

class ProjectMock(object):
    """ Mock object for lims.Project """
    pass

class UserMock(object):
    """ Mock object for django.contrib.auth.models.User """
    def __init__(self, user_id=None, username=None, profile=None, is_authenticated=True, is_superuser=False):
        self.username = username
        self.profile = profile
        self.is_superuser = is_superuser
        self._is_authenticated = is_authenticated
        self.is_saved = False
        self.user_id = user_id
        
    def get_profile(self):
        if not self.profile:
            raise Project.DoesNotExist
        return self.profile
    
    def is_authenticated(self):
        return self._is_authenticated
    
    def save(self):
        self.is_saved = True

class RequestMock(object):
    """ Mock object for django.http.Request """
    def __init__(self, user=None):
        self.user = user
        self.project = None
        self.manager = None
        
def get_request(is_superuser=False):
    """ Return a Request Mock """
    project = ProjectMock()
    user = UserMock(profile=project, is_superuser=is_superuser)
    request = RequestMock(user=user)
    return request
    
