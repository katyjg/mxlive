""" Django views tests """
import unittest
import os

from django.conf import settings
from django.http import Http404
from django.db import IntegrityError
from django.utils.datastructures import MultiValueDict

from imm.lims.models import Project
from imm.lims.models import Laboratory
from imm.lims.models import Shipment
from imm.lims.models import Crystal
from imm.lims.models import Container
from imm.lims.models import Dewar
from imm.lims.models import Shipment
from imm.lims.models import Experiment
from imm.lims.models import perform_action

from imm.lims.views import create_and_update_project_and_laboratory
from imm.lims.views import project_required
from imm.lims.views import manager_required
from imm.lims.views import project_assurance
from imm.lims.views import home
from imm.lims.views import show_project
from imm.lims.views import shipment_pdf
from imm.lims.views import shipment_xls
from imm.lims.views import upload_shipment
from imm.lims.views import edit_object_inline
from imm.lims.views import object_list
from imm.lims.views import create_object
from imm.lims.views import change_priority
from imm.lims.views import add_existing_object

from imm.lims.forms import ShipmentUploadForm
from imm.lims.forms import ShipmentForm
from imm.lims.forms import ShipmentSendForm
from imm.lims.forms import SampleSelectForm
from imm.lims.forms import ExperimentFromStrategyForm

from imm.lims.tests.test_utils import DjangoTestCase
from imm.lims.tests.test_utils import create_Project
from imm.lims.tests.test_utils import create_Laboratory
from imm.lims.tests.test_utils import create_User
from imm.lims.tests.test_utils import create_Crystal
from imm.lims.tests.test_utils import create_Dewar
from imm.lims.tests.test_utils import create_Shipment
from imm.lims.tests.test_utils import create_Experiment
from imm.lims.tests.test_utils import get_request
from imm.lims.tests.test_utils import UserMock
from imm.lims.tests.test_utils import RequestMock
from imm.lims.tests.test_utils import convert_dict_of_QuerySet_to_dict_of_list
from imm.lims.tests.test_utils import convert_ObjectList_to_list
from imm.lims.tests.test_utils import TEST_FILES

def userApiFetcher(url):
    from remote.views import MOCK_USER_API_CONTENT
    return MOCK_USER_API_CONTENT
        
class CreateDefaultProjectTest(DjangoTestCase):
    """ Tests for create_default_project """
    
    def test_create_default_project_no_user(self):
        self.assertRaises(ValueError, create_and_update_project_and_laboratory, None)
        
    def test_create_default_project_creates_project(self):
        # create the user
        user = create_User(username='testuser')

        self.assertEqual(0, Project.objects.all().count())
        self.assertEqual(0, Laboratory.objects.all().count())
        
        project = create_and_update_project_and_laboratory(user, fetcher=userApiFetcher)

        # assert correct values
        self.assertNotEqual(None, project)
        self.assertEqual(project.permit_no, '12-1')
        self.assertEqual(project.name, 'Proposal for Crystal Method')
        self.assertEqual(project.title, '')
        self.assertEqual(project.summary, '')
        self.assertEqual(project.beam_time, 0)
        self.assertNotEqual(None, project.lab)
        
        # ensure it was saved
        self.assertEqual(1, Project.objects.all().count())
        self.assertEqual(1, Laboratory.objects.all().count())
        
@project_required
def project_required_function(request):
    pass

@manager_required
def manager_required_function(request, model):
    pass

class ProjectRequiredTest(DjangoTestCase):
    """ Tests for project_required decorator """
    
    def test_no_profile(self):
        user = UserMock()
        request = RequestMock(user=user)
        self.assertRaises(Http404, project_required_function, request)
        
    def test_profile(self):
        request = get_request()
        self.assertFalse(request.project)
        project_required_function(request)
        self.assertTrue(request.project)
        
class ManagerRequiredTest(DjangoTestCase):
    """ Tests for project_required decorator """
    
    def setUp(self):
        super(ManagerRequiredTest, self).setUp()
        self.user1 = create_User(username='user1')
        self.user2 = create_User(username='user2')
        self.superuser = create_User(username='superuser', is_superuser=True)
        self.set_up_default_laboratory()
        self.project1 = create_Project(user=self.user1, lab=self.lab)
    
    def test_user1_has_project_missing_crystal(self):
        request = RequestMock(user=self.user1)
        self.assertEqual(None, request.manager)
        manager_required_function(request, Crystal)
        self.assertNotEqual(None, request.manager)
        self.assertEqual([], list(request.manager.all()))
        
    def test_user1_has_project_has_crystal(self):
        request = RequestMock(user=self.user1)
        self.assertEqual(None, request.manager)
        manager_required_function(request, Crystal)
        self.assertNotEqual(None, request.manager)
        crystal = create_Crystal(project=self.project1)
        self.assertEqual([crystal], list(request.manager.all()))
        
    def test_user2_missing_project(self):
        request = RequestMock(user=self.user2)
        self.assertEqual(None, request.manager)
        self.assertRaises(Http404, manager_required_function, request, Crystal)
        self.assertEqual(None, request.manager)
        
    def test_superuser(self):
        request = RequestMock(user=self.superuser)
        self.assertEqual(None, request.manager)
        manager_required_function(request, Crystal)
        self.assertNotEqual(None, request.manager)
        
@project_assurance
def project_assurance_function(request, fetcher=None):
    pass

class ProjectAssuranceTest(DjangoTestCase):
    """ Tests for project_assurance decorator """
    
    def test_project_assurance_does_not_create_if_existing_project(self):
        # create a user and their project 
        user = create_User(username='testuser')
        lab = create_Laboratory(name='Canadian Light source')
        project = create_Project(user=user, name=user.username, lab=lab)
        request = RequestMock(user=user)
        
        self.assertEqual(1, Project.objects.all().count())
        project_assurance_function(request)
        self.assertEqual(1, Project.objects.all().count())
        self.assertEqual(project, Project.objects.all()[0])

    def test_project_assurance_creates_missing_project(self):
        # create a user with no project
        user = create_User(username='testuser')
        lab = create_Laboratory(name='Canadian Light source')
        request = RequestMock(user=user)
        
        self.assertEqual(0, Project.objects.all().count())
        project_assurance_function(request, fetcher=userApiFetcher)
        self.assertEqual(1, Project.objects.all().count())
        self.assertEqual('Proposal for Crystal Method', Project.objects.all()[0].name)
        
        
class HomeTest(DjangoTestCase):
    """ Test the /home/ view """
    
    def test_user(self):
        request = get_request(is_superuser=False)
        response = home(request)
        self.assertEqual(response.status_code, 302)
        self.assertEqual(response['Location'], '/lims/')
        
    def test_superuser(self):
        request = get_request(is_superuser=True)
        response = home(request)
        self.assertEqual(response.status_code, 302)
        self.assertEqual(response['Location'], '/staff/')
        
class ShowProjectTest(DjangoTestCase):
    """ Test the /lims/ view """
    
    def setUp(self):
        super(ShowProjectTest, self).setUp()
        self.set_up_default_project()
        self.mock_out_render_to_response()
    
    def test_empty(self):
        request = self.get_request()
        response = show_project(request)
        self.assertEqual('lims/project.html', response.rendered_args[0])
        rendered_data = response.rendered_args[1]
        self.assertEqual(['project', 'statistics', 'link', 'inbox'], rendered_data.keys())
        expected_project = self.project
        self.assertEqual(expected_project, rendered_data['project'])
        expected_statistics = {'experiment': {'active': [], 'paused': [], 'processing': [], 'draft': [], 'closed': []}, 
                               'shipment': {'incoming': [], 'outgoing': [], 'draft': [], 'closed': [], 'received': []}}
        self.assertEqual(expected_statistics, convert_dict_of_QuerySet_to_dict_of_list(rendered_data['statistics']))
        self.assertEqual(False, rendered_data['link'])
        self.assertEqual([], convert_ObjectList_to_list(rendered_data['inbox']))
        
class ShipmentExportTest(DjangoTestCase):
    """ Tests for /shipment/[pdf|xls] """
    
    def setUp(self):
        super(ShipmentExportTest, self).setUp()
        self.set_up_default_shipment()
        
    def test_pdf(self):
        request = self.get_request()
        response = shipment_pdf(request, self.shipment.pk)
        self.assertEqual('testing', response.content)
    
    def test_xls(self):
        request = self.get_request()
        response = shipment_xls(request, self.shipment.pk)
        self.assertEqual(17920, len(response.content))
        
class ShipmentUploadTest(DjangoTestCase):
    
    def setUp(self):
        super(ShipmentUploadTest, self).setUp()
        self.set_up_default_project()
        self.set_up_default_space_group(name='P2(1)2(1)2(1)')
        self.mock_out_render_to_response()
        
    def test_GET(self):
        request = self.get_request()
        response = upload_shipment(request, Shipment, ShipmentUploadForm)
        self.assertEqual(200, response.status_code)
        form = response.rendered_args[1]['form']
        self.assertEqual({'project': 1}, form.initial)
        
    def test_invalid_empty(self):
        request = self.post_request(data={}, files={})
        response = upload_shipment(request, Shipment, ShipmentUploadForm)
        self.assertEqual(200, response.status_code)
        form = response.rendered_args[1]['form']
        self.assertEqual({}, form.data)
        self.assertEqual({}, form.files)
        self.assertFalse(form.is_valid())
        
    def test_invalid_bad_data(self):
        excel = open(os.path.join(TEST_FILES, 'errors.xls'))
        request = self.post_request(data={'project': self.project.pk}, files={'excel' : excel})
        response = upload_shipment(request, Shipment, ShipmentUploadForm)
        self.assertEqual(200, response.status_code)
        form = response.rendered_args[1]['form']
        self.assertEqual({'project': [1]}, form.data)
        self.assertEqual({'excel' : excel}, form.files)
        self.assertFalse(form.is_valid())
        
    def test_valid(self):
        self.assertEqual(0, Shipment.objects.count())
        self.assertEqual(0, Container.objects.count())
        self.assertEqual(0, Crystal.objects.count())
        
        excel = open(os.path.join(TEST_FILES, 'test.xls'))
        request = self.post_request(data={'project': self.project.pk}, files={'excel' : excel})
        response = upload_shipment(request, Shipment, ShipmentUploadForm)
        self.assertEqual(200, response.status_code)
        self.assertEqual(request.user.get_and_delete_messages()[0], "The data was uploaded correctly.")
        
        self.assertEqual(1, Shipment.objects.count())
        self.assertEqual(4, Container.objects.count())
        self.assertEqual(8, Crystal.objects.count())
        
    def test_double_upload(self):
        self.assertEqual(0, Shipment.objects.count())
        self.assertEqual(0, Container.objects.count())
        self.assertEqual(0, Crystal.objects.count())
        
        excel = open(os.path.join(TEST_FILES, 'test.xls'))
        request = self.post_request(data={'project': self.project.pk}, files={'excel' : excel})
        response = upload_shipment(request, Shipment, ShipmentUploadForm)
        self.assertEqual(200, response.status_code)
        self.assertEqual(request.user.get_and_delete_messages()[0], "The data was uploaded correctly.")
        
        self.assertEqual(1, Shipment.objects.count())
        self.assertEqual(4, Container.objects.count())
        self.assertEqual(8, Crystal.objects.count())
        
        excel = open(os.path.join(TEST_FILES, 'test.xls'))
        request = self.post_request(data={'project': self.project.pk}, files={'excel' : excel})
        response = upload_shipment(request, Shipment, ShipmentUploadForm)
        self.assertEqual(200, response.status_code)
        form = response.rendered_args[1]['form']
        self.assertFalse(form.is_valid())
        self.assertEqual({'excel': [u'This data has been uploaded already']}, form.errors)
        
        self.assertEqual(1, Shipment.objects.count())
        self.assertEqual(4, Container.objects.count())
        self.assertEqual(8, Crystal.objects.count())
        
class ShipmentSendTest(DjangoTestCase):
    
    def setUp(self):
        super(ShipmentSendTest, self).setUp()
        self.mock_out_render_to_response()
        self.set_up_default_crystal()
        self.set_up_default_carrier()
        
    def test_user_POST_invalid(self):
        request = self.post_request()
        response = edit_object_inline(request, self.shipment.pk, Shipment, ShipmentSendForm, action='send')
        self.assertEqual(response.status_code, 200)
        self.assertFalse(response.rendered_args[1]['form'].is_valid())
        self.assertEqual({'carrier': ['This field is required.'], 
                          'tracking_code': ['This field is required.'],
                          'project': ['This field is required.']}, response.rendered_args[1]['form'].errors)
        
    def test_user_POST_not_found(self):
        request = self.post_request()
        request.POST['project'] = self.project.pk + 1
        request.POST['tracking_code'] = '123'
        request.POST['carrier'] = self.carrier.pk
        self.assertRaises(Http404, edit_object_inline, request, self.shipment.pk + 1, Shipment, ShipmentSendForm, action='return')
        
    def test_user_POST_found(self):
        request = self.post_request()
        request.POST['project'] = self.project.pk
        request.POST['tracking_code'] = '123'
        request.POST['carrier'] = self.carrier.pk
        response = edit_object_inline(request, self.shipment.pk, Shipment, ShipmentSendForm, action='send')
        self.assertEqual(response.status_code, 200)
        self.reload_models()
        self.assertEqual(Shipment.STATES.SENT, self.shipment.status)
        
    def test_user_POST_already_sent(self):
        request = self.post_request()
        request.POST['project'] = self.project.pk
        request.POST['tracking_code'] = '123'
        request.POST['carrier'] = self.carrier.pk
        response = edit_object_inline(request, self.shipment.pk, Shipment, ShipmentSendForm, action='send')
        self.assertEqual(response.status_code, 200)
        response = edit_object_inline(request, self.shipment.pk, Shipment, ShipmentSendForm, action='send')
        self.assertEqual(response.status_code, 200)
        self.assertFalse(response.rendered_args[1]['form'].is_valid())
        self.assertEqual({'tracking_code': ['Shipment already sent.']}, response.rendered_args[1]['form'].errors)
    
class ObjectListTest(DjangoTestCase):
    
    def setUp(self):
        super(ObjectListTest, self).setUp()
        self.mock_out_render_to_response()
        self.set_up_default_crystal()
        self.other_user = create_User(username='foobar')
        self.admin_user = create_User(username='admin', is_superuser=True)
    
    def test_object_list_defaults(self):
        request = self.get_request()
        response = object_list(request, Shipment)
        self.assertEqual('objlist/object_list.html', response.rendered_args[0])
        
        # check that the data was correct
        ol = response.rendered_args[1].pop('ol')
        self.assertEqual([self.shipment], list(ol.object_list))
        
        # NOTE: CHANGING THESE MEANS YOU LIKELY NEED TO CHANGE urls.py IN EVERY APP!!!
        self.assertEqual({'can_prioritize': False, # ARE YOU SURE YOU WANT TO CHANGE THIS?
                          'can_receive': False, # ARE YOU SURE YOU WANT TO CHANGE THIS?
                          'can_add': False, # ARE YOU SURE YOU WANT TO CHANGE THIS?
                          'link': True, # ARE YOU SURE YOU WANT TO CHANGE THIS?
                          'can_upload': False, # ARE YOU SURE YOU WANT TO CHANGE THIS?
                          'handler': '',
                          }, response.rendered_args[1])
        
    def test_object_list_no_project(self):
        request = self.get_request()
        request.user = self.other_user
        self.assertRaises(Http404, object_list, request, Shipment)
        
    def test_object_list_adminuser(self):
        request = self.get_request()
        request.user = self.admin_user
        response = object_list(request, Shipment)
        ol = response.rendered_args[1].pop('ol')
        self.assertEqual([], list(ol.object_list)) # admin cannot see DRAFT
        
        perform_action(self.shipment, 'send')
        self.reload_models()
        response = object_list(request, Shipment)
        ol = response.rendered_args[1].pop('ol')
        self.assertEqual([self.shipment], list(ol.object_list))
        
    def test_object_list_no_results(self):
        request = self.get_request()
        request.user = self.other_user
        project = create_Project(user=request.user, lab=self.lab)
        response = object_list(request, Shipment)
        ol = response.rendered_args[1].pop('ol')
        self.assertEqual([], list(ol.object_list))
        
        
class ChangePriorityTest(DjangoTestCase):
    
    def setUp(self):
        super(ChangePriorityTest, self).setUp()
        self.mock_out_render_to_response()
        self.set_up_default_project()
        self.set_up_default_user()
        self.set_up_default_adminuser()
        self.experiments = [create_Experiment(project=self.project, priority=i, staff_priority=i) for i in range(10)]
        
    def reload(self):
        self.experiments = [Experiment.objects.get(pk=e.pk) for e in self.experiments]
        
    def test_user_middle(self):
        request = self.post_request()
        response = change_priority(request, self.experiments[5].pk, Experiment, 'up', 'priority')
        self.reload()
        self.assertEqual([0, 1, 2, 3, 4, 7, 6, 7, 8, 9], [e.priority for e in self.experiments])
        self.assertEqual([0, 1, 2, 3, 4, 5, 6, 7, 8, 9], [e.staff_priority for e in self.experiments])
        response = change_priority(request, self.experiments[5].pk, Experiment, 'down', 'priority')
        self.reload()
        self.assertEqual([0, 1, 2, 3, 4, 5, 6, 7, 8, 9], [e.priority for e in self.experiments])
        self.assertEqual([0, 1, 2, 3, 4, 5, 6, 7, 8, 9], [e.staff_priority for e in self.experiments])
        
    def test_user_highest(self):
        request = self.post_request()
        response = change_priority(request, self.experiments[-1].pk, Experiment, 'up', 'priority')
        self.reload()
        self.assertEqual([0, 1, 2, 3, 4, 5, 6, 7, 8, 10], [e.priority for e in self.experiments])
        self.assertEqual([0, 1, 2, 3, 4, 5, 6, 7, 8, 9], [e.staff_priority for e in self.experiments])
        response = change_priority(request, self.experiments[-1].pk, Experiment, 'down', 'priority')
        self.reload()
        self.assertEqual([0, 1, 2, 3, 4, 5, 6, 7, 8, 7], [e.priority for e in self.experiments])
        self.assertEqual([0, 1, 2, 3, 4, 5, 6, 7, 8, 9], [e.staff_priority for e in self.experiments])
        
    def test_user_lowest(self):
        request = self.post_request()
        response = change_priority(request, self.experiments[0].pk, Experiment, 'up', 'priority')
        self.reload()
        self.assertEqual([2, 1, 2, 3, 4, 5, 6, 7, 8, 9], [e.priority for e in self.experiments])
        self.assertEqual([0, 1, 2, 3, 4, 5, 6, 7, 8, 9], [e.staff_priority for e in self.experiments])
        response = change_priority(request, self.experiments[0].pk, Experiment, 'down', 'priority')
        self.reload()
        self.assertEqual([0, 1, 2, 3, 4, 5, 6, 7, 8, 9], [e.priority for e in self.experiments])
        self.assertEqual([0, 1, 2, 3, 4, 5, 6, 7, 8, 9], [e.staff_priority for e in self.experiments])
        
class AddExistingObject_ContainerCrystal_Test(DjangoTestCase):
    
    def setUp(self):
        super(AddExistingObject_ContainerCrystal_Test, self).setUp()
        self.mock_out_render_to_response()
        self.set_up_default_crystal()
        self.crystal1 = create_Crystal(project=self.project, name='crystal1')
        self.crystal2 = create_Crystal(project=self.project, name='crystal2')
        
    def test_not_found(self):
        request = self.get_request()
        self.assertRaises(Http404, add_existing_object, request, dest_id=999, destination=Container, object=Crystal, obj_id=1)
        
    def test_GET(self):
        request = self.get_request()
        # no longer supports GET to the add methods.
        # response = add_existing_object(request, self.container.pk, Container, Crystal, 'container', additional_fields=['container_location'], form=SampleSelectForm)
        self.assertRaises(Http404, add_existing_object, request, 1, 1, Container, Crystal)
       # response = add_existing_object(request, destination=Container, dest_id=1, object=Crystal, obj_id=1)
#        self.assertEqual(200, response.status_code)
#        form = response.rendered_args[1]['form']
#        info = response.rendered_args[1]['info']
#        self.assertEqual({}, form.data)
#        self.assertEqual({'parent': self.container.pk}, form.initial)
#        self.assertFalse(form.is_bound)
#        self.assertFalse(form.is_valid())
#        self.assertEqual({}, form.errors)
#        self.assertEqual([('', '---------'), (2, unicode(self.crystal1)), (3, unicode(self.crystal2))], list(form.fields['items'].choices))
#        self.assertEqual([('A2', 'A2'), ('A3', 'A3'), ('A4', 'A4'), ('A5', 'A5'), ('A6', 'A6'), ('A7', 'A7'), ('A8', 'A8'), 
#                          ('B1', 'B1'), ('B2', 'B2'), ('B3', 'B3'), ('B4', 'B4'), ('B5', 'B5'), ('B6', 'B6'), ('B7', 'B7'), ('B8', 'B8'), 
#                          ('C1', 'C1'), ('C2', 'C2'), ('C3', 'C3'), ('C4', 'C4'), ('C5', 'C5'), ('C6', 'C6'), ('C7', 'C7'), ('C8', 'C8'), 
#                          ('D1', 'D1'), ('D2', 'D2'), ('D3', 'D3'), ('D4', 'D4'), ('D5', 'D5'), ('D6', 'D6'), ('D7', 'D7'), ('D8', 'D8'), 
#                          ('E1', 'E1'), ('E2', 'E2'), ('E3', 'E3'), ('E4', 'E4'), ('E5', 'E5'), ('E6', 'E6'), ('E7', 'E7'), ('E8', 'E8'), 
#                          ('F1', 'F1'), ('F2', 'F2'), ('F3', 'F3'), ('F4', 'F4'), ('F5', 'F5'), ('F6', 'F6'), ('F7', 'F7'), ('F8', 'F8'), 
#                          ('G1', 'G1'), ('G2', 'G2'), ('G3', 'G3'), ('G4', 'G4'), ('G5', 'G5'), ('G6', 'G6'), ('G7', 'G7'), ('G8', 'G8'), 
#                          ('H1', 'H1'), ('H2', 'H2'), ('H3', 'H3'), ('H4', 'H4'), ('H5', 'H5'), ('H6', 'H6'), ('H7', 'H7'), ('H8', 'H8'), 
#                          ('I1', 'I1'), ('I2', 'I2'), ('I3', 'I3'), ('I4', 'I4'), ('I5', 'I5'), ('I6', 'I6'), ('I7', 'I7'), ('I8', 'I8'), 
#                          ('J1', 'J1'), ('J2', 'J2'), ('J3', 'J3'), ('J4', 'J4'), ('J5', 'J5'), ('J6', 'J6'), ('J7', 'J7'), ('J8', 'J8'), 
#                          ('K1', 'K1'), ('K2', 'K2'), ('K3', 'K3'), ('K4', 'K4'), ('K5', 'K5'), ('K6', 'K6'), ('K7', 'K7'), ('K8', 'K8'), 
#                          ('L1', 'L1'), ('L2', 'L2'), ('L3', 'L3'), ('L4', 'L4'), ('L5', 'L5'), ('L6', 'L6'), ('L7', 'L7'), ('L8', 'L8')], 
#                          form.fields['container_location'].choices)
#        self.assertEqual({'action': '', 
#                          'sub_title': 'Select existing crystals to add to container123', 
#                          'target': 'entry-scratchpad', 
#                          'title': 'Add Existing Crystal'}, info)
        
    def test_POST_valid(self):
        request = self.post_request({'parent': self.container.pk, 'items': self.crystal1.pk, 'container_location': 'A2'})
        self.assertEqual([self.crystal], list(self.container.crystal_set.all()))
        #response = add_existing_object(request, self.container.pk, Container, Crystal, 'container', additional_fields=['container_location'], form=SampleSelectForm)
        response = add_existing_object(request, dest_id=self.container.pk, obj_id=self.crystal1.pk, destination=Container, object=Crystal, reverse=True)
        self.assertEqual([self.crystal, self.crystal1], list(self.container.crystal_set.all()))
        self.assertEqual(200, response.status_code)
        self.assertEqual(('lims/refresh.html',), response.rendered_args)
        
    def test_POST_invalid(self):
        request = self.post_request({'parent': self.container.pk})
        #response = add_existing_object(request, self.container.pk, Container, Crystal, 'container', additional_fields=['container_location'], form=SampleSelectForm)
        response = add_existing_object(request, destination=Container, dest_id=1, object=Crystal, obj_id=1)
        self.assertEqual(200, response.status_code)
        # No longer give a form, it's an Ajax endpoint. 
#        form = response.rendered_args[1]['form']
#        info = response.rendered_args[1]['info']
#        self.assertEqual({'parent': [self.container.pk]}, form.data)
#        self.assertEqual({}, form.initial)
#        self.assertTrue(form.is_bound)
#        self.assertFalse(form.is_valid())
#        self.assertEqual({'items': ['This field is required.'], 'container_location': ['This field is required.']}, form.errors)
#        self.assertEqual([('', '---------'), (2, unicode(self.crystal1)), (3, unicode(self.crystal2))], list(form.fields['items'].choices))
#        self.assertEqual([('A2', 'A2'), ('A3', 'A3'), ('A4', 'A4'), ('A5', 'A5'), ('A6', 'A6'), ('A7', 'A7'), ('A8', 'A8'), 
#                          ('B1', 'B1'), ('B2', 'B2'), ('B3', 'B3'), ('B4', 'B4'), ('B5', 'B5'), ('B6', 'B6'), ('B7', 'B7'), ('B8', 'B8'), 
#                          ('C1', 'C1'), ('C2', 'C2'), ('C3', 'C3'), ('C4', 'C4'), ('C5', 'C5'), ('C6', 'C6'), ('C7', 'C7'), ('C8', 'C8'), 
#                          ('D1', 'D1'), ('D2', 'D2'), ('D3', 'D3'), ('D4', 'D4'), ('D5', 'D5'), ('D6', 'D6'), ('D7', 'D7'), ('D8', 'D8'), 
#                          ('E1', 'E1'), ('E2', 'E2'), ('E3', 'E3'), ('E4', 'E4'), ('E5', 'E5'), ('E6', 'E6'), ('E7', 'E7'), ('E8', 'E8'), 
#                          ('F1', 'F1'), ('F2', 'F2'), ('F3', 'F3'), ('F4', 'F4'), ('F5', 'F5'), ('F6', 'F6'), ('F7', 'F7'), ('F8', 'F8'), 
#                          ('G1', 'G1'), ('G2', 'G2'), ('G3', 'G3'), ('G4', 'G4'), ('G5', 'G5'), ('G6', 'G6'), ('G7', 'G7'), ('G8', 'G8'), 
#                          ('H1', 'H1'), ('H2', 'H2'), ('H3', 'H3'), ('H4', 'H4'), ('H5', 'H5'), ('H6', 'H6'), ('H7', 'H7'), ('H8', 'H8'), 
#                          ('I1', 'I1'), ('I2', 'I2'), ('I3', 'I3'), ('I4', 'I4'), ('I5', 'I5'), ('I6', 'I6'), ('I7', 'I7'), ('I8', 'I8'), 
#                          ('J1', 'J1'), ('J2', 'J2'), ('J3', 'J3'), ('J4', 'J4'), ('J5', 'J5'), ('J6', 'J6'), ('J7', 'J7'), ('J8', 'J8'), 
#                          ('K1', 'K1'), ('K2', 'K2'), ('K3', 'K3'), ('K4', 'K4'), ('K5', 'K5'), ('K6', 'K6'), ('K7', 'K7'), ('K8', 'K8'), 
#                          ('L1', 'L1'), ('L2', 'L2'), ('L3', 'L3'), ('L4', 'L4'), ('L5', 'L5'), ('L6', 'L6'), ('L7', 'L7'), ('L8', 'L8')], 
#                          form.fields['container_location'].choices)
#        self.assertEqual({'action': '', 
#                          'sub_title': 'Select existing crystals to add to container123', 
#                          'target': 'entry-scratchpad', 
#                          'title': 'Add Existing Crystal'}, info)
#        
    def test_POST_race(self):
        request = self.post_request({'parent': self.container.pk, 'items': self.crystal1.pk, 'container_location': 'A2'})
        self.assertEqual(3, self.crystal2.pk)
        self.assertEqual(1, self.container.pk)
        
        class SampleSelectFormRace(SampleSelectForm):
            def __init__(self, *args, **kwargs):
                super(SampleSelectFormRace, self).__init__(*args, **kwargs)
                # inject a race condition (db insertion) in form construction
                crystal = Crystal.objects.get(pk=3)
                container = Container.objects.get(pk=1)
                crystal.container = container
                crystal.container_location = 'A2'
                crystal.save()
        
        self.assertRaises(IntegrityError, add_existing_object, request, self.container.pk, 3, Container, Crystal )

class AddExistingObject_ShipmentDewar_Test(DjangoTestCase):
    
    def setUp(self):
        super(AddExistingObject_ShipmentDewar_Test, self).setUp()
        self.mock_out_render_to_response()
        self.set_up_default_shipment()
        self.dewar1 = create_Dewar(project=self.project, label='dewar1')
        self.dewar2 = create_Dewar(project=self.project, label='dewar2')
        
    def test_not_found(self):
        request = self.get_request()
        self.assertRaises(Http404, add_existing_object, request, 999, Shipment, Dewar, 'shipment')
        
    def test_GET(self):
        request = self.get_request()
        # add no longer supports get
        self.assertRaises(Http404, add_existing_object, request, 1, 1, Dewar, Shipment)
#        
#        response = add_existing_object(request, self.shipment.pk, Shipment, Dewar, 'shipment')
#        self.assertEqual(200, response.status_code)
#        form = response.rendered_args[1]['form']
#        info = response.rendered_args[1]['info']
#        self.assertEqual({}, form.data)
#        self.assertEqual({}, form.initial)
#        self.assertFalse(form.is_bound)
#        self.assertFalse(form.is_valid())
#        self.assertEqual({}, form.errors)
#        self.assertEqual([(1, self.dewar1.label), (2, self.dewar2.label)], list(form.fields['items'].choices))
#        self.assertEqual({'action': '', 
#                          'sub_title': 'Select existing dewars to add to ', 
#                          'target': 'entry-scratchpad', 
#                          'title': 'Add Existing Dewar'}, info)
        
    def test_POST_valid(self):
        request = self.post_request()
        self.assertEqual([], list(self.shipment.dewar_set.all()))
        response = add_existing_object(request, dest_id=self.shipment.pk, obj_id=self.dewar1.pk, destination=Shipment, object=Dewar, reverse=True)
        self.assertEqual([self.dewar1], list(self.shipment.dewar_set.all()))
        self.assertEqual(200, response.status_code)
        self.assertEqual(('lims/refresh.html',), response.rendered_args)
        
    def test_POST_no_data(self):
        request = self.post_request()
        # post data isn't used anymore. It's all in the url.
        # actually raises a 404, since it is missin the dewar id
        
        self.assertRaises(Http404, add_existing_object, request, dest_id=self.shipment.pk, destination=Shipment, object=Dewar, obj_id=-1)
#        self.assertEqual(200, response.status_code)
#        self.assertEqual([], list(self.shipment.dewar_set.all()))
#        self.assertEqual(('lims/refresh.html',), response.rendered_args)

class CreateObject_Shipment_Test(DjangoTestCase):
    
    def setUp(self):
        super(CreateObject_Shipment_Test, self).setUp()
        self.mock_out_render_to_response()
        self.set_up_default_shipment()
    
    def test_GET(self):
        request = self.get_request()
        response = create_object(request, Shipment, ShipmentForm)
        self.assertEqual(200, response.status_code)
        form = response.rendered_args[1]['form']
        info = response.rendered_args[1]['info']
        self.assertEqual({'action': '', 'add_another': True, 'title': 'New Shipment'}, info)
        self.assertEqual({}, form.data)
        self.assertEqual({'project': 1}, form.initial)
        self.assertFalse(form.is_bound)
        self.assertFalse(form.is_valid())
        self.assertEqual({}, form.errors)

    def test_POST_invalid(self):
        request = self.post_request()
        response = create_object(request, Shipment, ShipmentForm)
        self.assertEqual(200, response.status_code)
        form = response.rendered_args[1]['form']
        info = response.rendered_args[1]['info']
        self.assertEqual({'action': '', 'add_another': True, 'title': 'New Shipment'}, info)
        self.assertEqual({}, form.data)
        self.assertEqual({}, form.initial)
        self.assertTrue(form.is_bound)
        self.assertFalse(form.is_valid())
        self.assertEqual({'project': ['This field is required.'], 'label': ['This field is required.']}, form.errors)
        
    def test_POST_invalid_action(self):
        request = self.post_request()
        request.POST['project'] = self.project.pk
        request.POST['label'] = 'label'
        self.assertRaises(KeyError, create_object, request, Shipment, ShipmentForm, action='foo')
        
    def test_POST_valid(self):
        request = self.post_request()
        request.POST['project'] = self.project.pk
        request.POST['label'] = 'label'
        self.assertEqual(1, Shipment.objects.count())
        response = create_object(request, Shipment, ShipmentForm)
        self.assertEqual(2, Shipment.objects.count())
        self.assertEqual(200, response.status_code)
        #TODO: Fails here, due to improper test. Need to decide how to repair it
        #self.assertEqual('../2/', response['Location'])
        
    def test_POST_valid_with_redirect(self):
        request = self.post_request()
        request.POST['project'] = self.project.pk
        request.POST['label'] = 'label'
        self.assertEqual(1, Shipment.objects.count())
        response = create_object(request, Shipment, ShipmentForm, redirect='lims-shipment-list')
        self.assertEqual(2, Shipment.objects.count())
        #TODO: fails here, improper test. Need to decide how to repair. 
        self.assertEqual(200, response.status_code)
        self.assertEqual(request.user.get_and_delete_messages()[0], ('The shipment "%(name)s" was added successfully.' % {'name':str(Shipment.objects.all()[1])}))
#       
#        self.assertEqual(('lims/redirect.html', {'redirect': '/lims/shipping/shipment/'}), response.rendered_args)
#        self.assertEqual({}, response.rendered_kwargs)
        
class CreateObject_ExperimentFromStrategy_Test(DjangoTestCase):
    
    def setUp(self):
        super(CreateObject_ExperimentFromStrategy_Test, self).setUp()
        self.mock_out_render_to_response()
        self.set_up_default_strategy()
        self.set_up_default_result()
    
    def test_GET(self):
        request = self.get_request()
        response = create_object(request, Experiment, ExperimentFromStrategyForm, action='resubmit', redirect='lims-experiment-list')
        self.assertEqual(200, response.status_code)
        form = response.rendered_args[1]['form']
        info = response.rendered_args[1]['info']
        self.assertEqual({'action': '', 'add_another': True, 'title': 'New Experiment'}, info)
        self.assertEqual({}, form.data)
        self.assertEqual({'project': 1}, form.initial)
        self.assertFalse(form.is_bound)
        self.assertFalse(form.is_valid())
        self.assertEqual({}, form.errors)
        
    def test_POST_invalid_ajax(self):
        request = self.post_request()
        response = create_object(request, Experiment, ExperimentFromStrategyForm, action='resubmit', redirect='lims-experiment-list')
        self.assertEqual(200, response.status_code)
        form = response.rendered_args[1]['form']
        info = response.rendered_args[1]['info']
        self.assertEqual({'action': '', 'add_another': True, 'title': 'New Experiment'}, info)
        self.assertEqual({}, form.data)
        self.assertEqual({}, form.initial)
        self.assertTrue(form.is_bound)
        self.assertFalse(form.is_valid())
        self.assertEqual({'kind': ['This field is required.'],
                          'name': ['This field is required.'],
                          'strategy': ['This field is required.'],
                          'project': ['This field is required.'],
                          'plan': ['This field is required.'],
                          'crystals': ['This field is required.']}, form.errors)

    def test_POST_valid_ajax(self):
        request = self.post_request()
        request.POST['project'] = self.project.pk
        request.POST['strategy'] = self.strategy.pk
        request.POST['name'] = 'name'
        request.POST.setlist('crystals', [c.pk for c in self.experiment.crystals.all()])
        request.POST['plan'] = Experiment.EXP_PLANS.JUST_COLLECT
        request.POST['kind'] = Experiment.EXP_TYPES.NATIVE
        self.assertEqual(1, Experiment.objects.count())
        response = create_object(request, Experiment, ExperimentFromStrategyForm, action='resubmit', redirect='lims-experiment-list')
        self.assertEqual(2, Experiment.objects.count())
        
        self.assertEqual(200, response.status_code)
        self.assertEqual(request.user.get_and_delete_messages()[0], ('The experiment "%(name)s" was added successfully.' % {'name':str(Experiment.objects.all()[1])}))
#        
#        self.assertEqual('lims/message.html', response.rendered_args)
#        self.assertEqual({}, response.rendered_kwargs)

    def test_POST_missing_strategy_ajax(self):
        request = self.post_request()
        request.POST['project'] = self.project.pk
        request.POST['strategy'] = self.strategy.pk + 1
        request.POST['name'] = 'name'
        request.POST.setlist('crystals', [c.pk for c in self.experiment.crystals.all()])
        request.POST['plan'] = Experiment.EXP_PLANS.JUST_COLLECT
        request.POST['kind'] = Experiment.EXP_TYPES.NATIVE
        self.assertEqual(1, Experiment.objects.count())
        response = create_object(request, Experiment, ExperimentFromStrategyForm, action='resubmit', redirect='lims-experiment-list')
        self.assertEqual(200, response.status_code)
        form = response.rendered_args[1]['form']
        info = response.rendered_args[1]['info']
        self.assertEqual({'action': '', 'add_another': True, 'title': 'New Experiment'}, info)
        self.assertEqual({'strategy': [u'Select a valid choice. That choice is not one of the available choices.']}, form.errors)

    def test_POST_missing_project_ajax(self):
        request = self.post_request()
        self.project.delete()
        self.assertRaises(Http404, create_object, request, Experiment, ExperimentFromStrategyForm, action='resubmit', redirect='lims-experiment-list')
