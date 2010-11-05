import unittest
import logging

from imm.lims.tests.test_utils import DjangoTestCase
from imm.lims.tests.test_utils import create_User
from imm.lims.tests.test_utils import create_Shipment
from imm.lims.tests.test_utils import create_Container
from imm.lims.tests.test_utils import create_Crystal
from imm.lims.tests.test_utils import create_Runlist
from imm.lims.tests.test_utils import create_Experiment
from imm.lims.tests.test_utils import create_Data
from imm.lims.tests.test_utils import create_Result
from imm.lims.tests.test_utils import get_request
from imm.lims.tests.test_utils import convert_ObjectList_to_list

from imm.lims.views import edit_object_inline

from imm.staff.views import staff_home
from imm.staff.views import receive_shipment
from imm.staff.views import runlist_object_list
from imm.staff.views import runlist_create_object
from imm.staff.views import detailed_runlist

from imm.lims.models import Shipment
from imm.lims.models import Dewar
from imm.lims.models import Container
from imm.lims.models import Crystal
from imm.lims.models import Experiment
from imm.lims.models import perform_action

from imm.messaging.models import Message

from imm.staff.models import Runlist

from imm.staff.forms import ShipmentReceiveForm
from imm.staff.forms import ShipmentReturnForm
from imm.staff.forms import DewarReceiveForm
from imm.staff.forms import RunlistForm

from django.template import RequestContext
from django.http import Http404

from django.utils import simplejson

from jsonrpc.exceptions import InvalidRequestError
from jsonrpc.exceptions import MethodNotFoundError

class StaffHomeTest(DjangoTestCase):
    """ Test the /staff/ view """
    
    def setUp(self):
        super(StaffHomeTest, self).setUp()
        self.mock_out_render_to_response()
    
    def test_redirects_if_not_staff(self):
        request = self.get_request()
        request.user = create_User(username='testuser')
        response = staff_home(request)
        self.assertEqual(response.status_code, 302)
        self.assertEqual(response['Location'], '/lims/')
        
    def test_renders_if_staff(self):
        request = self.get_request()
        request.user = create_User(username='adminuser', is_superuser=True)
        response = staff_home(request)
        self.assertEqual(response.status_code, 200)
        self.assertEqual('lims/staff.html', response.rendered_args[0])
        rendered_data = response.rendered_args[1]
        self.assertEqual(['inbox'], rendered_data.keys())
        self.assertEqual([], convert_ObjectList_to_list(rendered_data['inbox']))
        
class ShipmentDewarReceiveTest(DjangoTestCase):
    
    def setUp(self):
        super(ShipmentDewarReceiveTest, self).setUp()
        self.mock_out_render_to_response()
        self.set_up_default_crystal()
        perform_action(self.shipment, 'send')
        self.reload_models()
    
    def test_user_not_allowed(self):
        self.set_up_default_user()
        request = self.get_request()
        response = receive_shipment(request, Dewar, DewarReceiveForm, action='receive')
        self.assertEqual(response.status_code, 302)
        
        request = self.post_request()
        response = receive_shipment(request, Dewar, DewarReceiveForm, action='receive')
        self.assertEqual(response.status_code, 302)
        
    def test_adminuser_GET(self):
        request = self.get_request()
        request.user = create_User(username='adminuser', is_superuser=True)
        response = receive_shipment(request, Dewar, DewarReceiveForm, action='receive')
        self.assertEqual(response.status_code, 200)
        self.assertEqual('objforms/form_base.html', response.rendered_args[0])
        self.assertEqual({'action': '', 'save_label': 'Receive', 'title': 'Receive Shipment/Dewar'}, response.rendered_args[1]['info'])
        self.assertTrue(isinstance(response.rendered_args[1]['form'], DewarReceiveForm))
        self.assertTrue(isinstance(response.rendered_kwargs['context_instance'], RequestContext))
        
    def test_adminuser_POST_invalid(self):
        request = self.post_request()
        request.user = create_User(username='adminuser', is_superuser=True)
        response = receive_shipment(request, Dewar, DewarReceiveForm, action='receive')
        self.assertEqual(response.status_code, 200)
        self.assertFalse(response.rendered_args[1]['form'].is_valid())
        self.assertEqual({'code': ['This field is required.']}, response.rendered_args[1]['form'].errors)
        
    def test_adminuser_POST_not_found(self):
        request = self.post_request()
        request.user = create_User(username='adminuser', is_superuser=True)
        request.POST['code'] = '123'
        response = receive_shipment(request, Dewar, DewarReceiveForm, action='receive')
        self.assertEqual(response.status_code, 200)
        self.assertFalse(response.rendered_args[1]['form'].is_valid())
        self.assertEqual({'code': ['No Dewar found with matching tracking code. Did you scan the correct Shipment?']}, response.rendered_args[1]['form'].errors)
        
    def test_adminuser_POST_found(self):
        request = self.post_request()
        request.user = create_User(username='adminuser', is_superuser=True)
        request.POST['code'] = self.dewar.code
        response = receive_shipment(request, Dewar, DewarReceiveForm, action='receive')
        self.assertEqual(response.status_code, 200)
        self.assertEqual(request.user.get_and_delete_messages()[0], "Dewar %s successfully received" % ( self.dewar.identity()) )
        self.reload_models()
        self.assertEqual(Dewar.STATES.ON_SITE, self.dewar.status)
        
    def test_adminuser_POST_already_received(self):
        request = self.post_request()
        request.user = create_User(username='adminuser', is_superuser=True)
        request.POST['code'] = self.dewar.code
        response = receive_shipment(request, Dewar, DewarReceiveForm, action='receive')
        self.assertEqual(response.status_code, 200)
        self.assertEqual(request.user.get_and_delete_messages()[0], "Dewar %s successfully received" % ( self.dewar.identity()) )
        
        response = receive_shipment(request, Dewar, DewarReceiveForm, action='receive')
        self.assertEqual(response.status_code, 200)
        self.assertFalse(response.rendered_args[1]['form'].is_valid())
        self.assertEqual({'code': ['Dewar already received.']}, response.rendered_args[1]['form'].errors)
        
class ShipmentReceiveTest(DjangoTestCase):
    
    def setUp(self):
        super(ShipmentReceiveTest, self).setUp()
        self.mock_out_render_to_response()
        self.set_up_default_crystal()
        perform_action(self.shipment, 'send')
        self.reload_models()
        
    def _test_user_not_allowed(self):
        self.set_up_default_user()
        request = self.get_request()
        response = edit_object_inline(request, self.shipment.pk, Shipment, ShipmentReceiveForm, action='receive')
        self.assertEqual(response.status_code, 302)
        
        request = self.post_request()
        response = edit_object_inline(request, self.shipment.pk, Shipment, ShipmentReceiveForm, action='receive')
        self.assertEqual(response.status_code, 302)
        
    def test_adminuser_POST_invalid(self):
        request = self.post_request()
        request.user = create_User(username='adminuser', is_superuser=True)
        response = edit_object_inline(request, self.shipment.pk, Shipment, ShipmentReceiveForm, action='receive')
        self.assertEqual(response.status_code, 200)
        self.assertFalse(response.rendered_args[1]['form'].is_valid())
        self.assertEqual({'tracking_code': ['This field is required.']}, response.rendered_args[1]['form'].errors)
        
    def test_adminuser_POST_not_found(self):
        request = self.post_request()
        request.user = create_User(username='adminuser', is_superuser=True)
        request.POST['tracking_code'] = '123'
        response = edit_object_inline(request, self.shipment.pk, Shipment, ShipmentReceiveForm, action='receive')
        self.assertEqual(response.status_code, 200)
        self.assertFalse(response.rendered_args[1]['form'].is_valid())
        self.assertEqual({'tracking_code': ['Mismatched tracking code. Expected "ups123". Did you scan the correct Shipment?']}, response.rendered_args[1]['form'].errors)
        
    def test_adminuser_POST_found(self):
        request = self.post_request()
        request.user = create_User(username='adminuser', is_superuser=True)
        request.POST['tracking_code'] = self.shipment.tracking_code
        response = edit_object_inline(request, self.shipment.pk, Shipment, ShipmentReceiveForm, action='receive')
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.content, '')
        self.reload_models()
        self.assertEqual(Shipment.STATES.ON_SITE, self.shipment.status)
        
    def test_adminuser_POST_already_received(self):
        request = self.post_request()
        request.user = create_User(username='adminuser', is_superuser=True)
        request.POST['tracking_code'] = self.shipment.tracking_code
        response = edit_object_inline(request, self.shipment.pk, Shipment, ShipmentReceiveForm, action='receive')
        self.assertEqual(response.status_code, 200)
        response = edit_object_inline(request, self.shipment.pk, Shipment, ShipmentReceiveForm, action='receive')
        self.assertEqual(response.status_code, 200)
        self.assertFalse(response.rendered_args[1]['form'].is_valid())
        self.assertEqual({'tracking_code': ['Shipment already received.']}, response.rendered_args[1]['form'].errors)
    
class ShipmentReturnTest(DjangoTestCase):
    
    def setUp(self):
        super(ShipmentReturnTest, self).setUp()
        self.mock_out_render_to_response()
        self.set_up_default_crystal()
        self.set_up_default_carrier()
        perform_action(self.shipment, 'send')
        self.reload_models()
        perform_action(self.shipment, 'receive')
        self.reload_models()
        
    def _test_user_not_allowed(self):
        self.set_up_default_user()
        request = self.get_request()
        response = edit_object_inline(request, self.shipment.pk, Shipment, ShipmentReturnForm, action='return')
        self.assertEqual(response.status_code, 302)
        
        request = self.post_request()
        response = edit_object_inline(request, self.shipment.pk, Shipment, ShipmentReturnForm, action='return')
        self.assertEqual(response.status_code, 302)
        
    def test_adminuser_POST_invalid(self):
        request = self.post_request()
        request.user = create_User(username='adminuser', is_superuser=True)
        response = edit_object_inline(request, self.shipment.pk, Shipment, ShipmentReturnForm, action='return')
        self.assertEqual(response.status_code, 200)
        self.assertFalse(response.rendered_args[1]['form'].is_valid())
        self.assertEqual({'carrier': ['This field is required.'], 'return_code': ['This field is required.']}, response.rendered_args[1]['form'].errors)
        
    def test_adminuser_POST_not_found(self):
        request = self.post_request()
        request.user = create_User(username='adminuser', is_superuser=True)
        request.POST['return_code'] = '123'
        request.POST['carrier'] = self.carrier.pk
        self.assertRaises(Http404, edit_object_inline, request, self.shipment.pk + 1, Shipment, ShipmentReturnForm, action='return')
        
    def test_adminuser_POST_found(self):
        request = self.post_request()
        request.user = create_User(username='adminuser', is_superuser=True)
        request.POST['return_code'] = '123'
        request.POST['carrier'] = self.carrier.pk
        response = edit_object_inline(request, self.shipment.pk, Shipment, ShipmentReturnForm, action='return')
        self.assertEqual(response.status_code, 200)
        self.reload_models()
        self.assertEqual(Shipment.STATES.RETURNED, self.shipment.status)
        
    def test_adminuser_POST_already_returned(self):
        request = self.post_request()
        request.user = create_User(username='adminuser', is_superuser=True)
        request.POST['return_code'] = '123'
        request.POST['carrier'] = self.carrier.pk
        response = edit_object_inline(request, self.shipment.pk, Shipment, ShipmentReturnForm, action='return')
        self.assertEqual(response.status_code, 200)
        response = edit_object_inline(request, self.shipment.pk, Shipment, ShipmentReturnForm, action='return')
        self.assertEqual(response.status_code, 200)
        self.assertFalse(response.rendered_args[1]['form'].is_valid())
        self.assertEqual({'return_code': ['Shipment already returned.']}, response.rendered_args[1]['form'].errors)
    
class RunlistObjectListTest(DjangoTestCase):
    
    def setUp(self):
        super(RunlistObjectListTest, self).setUp()
        self.mock_out_render_to_response()
        self.set_up_default_experiment()
        self.set_up_default_adminuser()
        self.set_up_default_user()
        
class CreateObjectTest(DjangoTestCase):
    
    def setUp(self):
        super(CreateObjectTest, self).setUp()
        self.mock_out_render_to_response()
        self.set_up_default_experiment()
        self.set_up_default_adminuser()
        self.set_up_default_user()
        
    def test_GET(self):
        request = self.get_request(is_superuser=True)
        response = runlist_create_object(request, Runlist, RunlistForm)
        self.assertEqual(200, response.status_code)
        form = response.rendered_args[1]['form']
        self.assertFalse(form.is_bound)
        self.assertFalse(form.is_valid())
        self.assertEqual({}, form.errors)
        
    def test_GET_unknown_arg(self):
        request = self.get_request(is_superuser=True)
        request.GET['foo'] = 'bar'
        response = runlist_create_object(request, Runlist, RunlistForm)
        self.assertEqual(200, response.status_code)
        form = response.rendered_args[1]['form']
        self.assertFalse(form.is_bound)
        self.assertFalse(form.is_valid())
        self.assertEqual({}, form.errors)
        self.assertEqual({}, form.initial)
        
    def test_GET_initial_arg(self):
        request = self.get_request(is_superuser=True)
        request.GET['container'] = '1'
        response = runlist_create_object(request, Runlist, RunlistForm)
        self.assertEqual(200, response.status_code)
        form = response.rendered_args[1]['form']
        self.assertFalse(form.is_bound)
        self.assertFalse(form.is_valid())
        self.assertEqual({}, form.errors)
        self.assertEqual({'containers': ['1']}, form.initial)
        
    def test_POST_invalid_data(self):
        request = self.post_request(is_superuser=True)
        response = runlist_create_object(request, Runlist, RunlistForm)
        self.assertEqual(200, response.status_code)
        form = response.rendered_args[1]['form']
        self.assertTrue(form.is_bound)
        self.assertFalse(form.is_valid())
        self.assertEqual({'name': ['This field is required.'], 'experiments': ['This field is required.'], 'containers': ['This field is required.']}, form.errors)
        
    def test_POST(self):
        request = self.post_request(is_superuser=True)
        request.POST['name'] = 'name'
        request.POST['containers'] = '1'
        request.POST['experiments'] = '1'
        self.assertEqual(0, Runlist.objects.count())
        response = runlist_create_object(request, Runlist, RunlistForm)
        self.assertEqual(200, response.status_code)
        self.assertEqual(request.user.get_and_delete_messages()[0], "New Runlist created." )
        
        self.assertEqual(1, Runlist.objects.count())
        runlist = Runlist.objects.get(pk=1)
        self.assertEqual([self.experiment], list(runlist.experiments))
        self.assertEqual([self.container], list(runlist.containers.all()))
        
class DetailedRunlistTest(DjangoTestCase):
    
    def setUp(self):
        super(DetailedRunlistTest, self).setUp()
        self.set_up_default_adminuser()
        
    def get_request(self):
        return super(DetailedRunlistTest, self).get_request(data={'username': self.adminuser.username, 'password': 'foo'}, is_superuser=True)
        
    def test_no_runlist(self):
        request = self.get_request()
        self.assertRaises(MethodNotFoundError, detailed_runlist, request, -1)
    
    def test_runlist_not_loaded(self):
        self.set_up_default_runlist()
        request = self.get_request()
        self.assertRaises(InvalidRequestError, detailed_runlist, request, self.runlist.pk)
        
    def _filter(self, retval):
        for data in retval:
            for container_pk, container in data['containers'].items():
                for key in container.keys():
                    if key not in ['crystals', 'id']:
                        container.pop(key)
            for crystal_pk, crystal in data['crystals'].items():
                for key in crystal.keys():
                    if key not in ['id']:
                        crystal.pop(key)
            for experiment in data['experiments']:
                for key in experiment.keys():
                    if key not in ['crystals', 'id', 'best_crystal']:
                        experiment.pop(key)
        return retval
        
    def _test(self, multiple_experiments=False, multiple_crystals=False, multiple_containers=False, multiple_runlists=False):
        self.set_up_default_runlist()
        
        if multiple_containers:
            container2 = create_Container(project=self.project, dewar=self.dewar, label='container2')
            if multiple_crystals:
                crystal2 = create_Crystal(project=self.project, container=container2, name='crystal2')
                if multiple_experiments:
                    experiment2 = create_Experiment(project=self.project, crystals=[crystal2], name='experiment2')
                    crystal2.experiment = experiment2
                    crystal2.save()
                else:
#                    self.experiment.crystals.add(crystal2)
                    crystal2.experiment = self.experiment
                    crystal2.save()
#                    self.experiment.save()
            else:
                raise ValueError()
            
        else:
            if multiple_crystals:
                crystal2 = create_Crystal(project=self.project, container=self.container, name='crystal2')
                if multiple_experiments:
                    experiment2 = create_Experiment(project=self.project, crystals=[crystal2], name='experiment2')
                    crystal2.experiment = experiment2
                    crystal2.save()
                else:
#                    self.experiment.crystals.add(crystal2)
                    crystal2.experiment = self.experiment
                    crystal2.save()
#                    self.experiment.save()
            else:
                if multiple_experiments:
                    raise ValueError()
                else:
                    pass # 1 container/crystal/experiment
                
        if multiple_runlists:
            if multiple_containers:
                runlist2 = create_Runlist(name='runlist2', containers=[container2], experiments=[self.experiment])
            else:
                runlist2 = create_Runlist(name='runlist2', containers=[self.container], experiments=[self.experiment])
        else:
            if multiple_containers:
                self.runlist.containers.add(container2)
                self.runlist.save()
            else:
                self.runlist.containers.add(self.container)
                self.runlist.save()
                
        perform_action(self.shipment, 'send')
        perform_action(self.shipment, 'receive')
        perform_action(self.runlist, 'load')
        
        request = self.get_request()
        
        response = detailed_runlist(request, self.runlist.pk)
        retval = [response]
        
        if multiple_runlists:
        
            perform_action(self.runlist, 'unload')
            perform_action(runlist2, 'load')
            
            response2 = detailed_runlist(request, runlist2.pk)
            retval = [response, response2]
            
        return self._filter(retval)
    
    # 0 'multiple'
    
    def test__single_experiment__single_crystal__single_container__single_runlist(self):
        results = self._test()
        self.assertEqual(
            [{'containers': {1: {'crystals': [1], 'id': 1}},
              'crystals': {1: {'id': 1}},
              'experiments': [{'crystals': [1], 'id': 1, 'best_crystal': None}]}], 
            results
        )
        
    # 1 'multiple'
        
    # test removed, as a crystal may now only be in a single experiment    
#    def test__multiple_experiments__single_crystal__single_container__single_runlist(self):
#        results = self._test(multiple_experiments=True)
#        self.assertEqual(
#            [{'containers': {1: {'crystals': [1], 'id': 1}},
#              'crystals': {1: {'id': 1}},
#              'experiments': [{'crystals': [1], 'id': 1, 'best_crystal': None}, 
#                              {'crystals': [1], 'id': 2, 'best_crystal': None}]}], 
#            results
#        )
        
    def test__single_experiment__multiple_crystals__single_container__single_runlist(self):
        results = self._test(multiple_crystals=True)
        self.assertEqual(
            [{'containers': {1: {'crystals': [1, 2], 'id': 1}},
              'crystals': {1: {'id': 1}, 2: {'id': 2}},
              'experiments': [{'crystals': [1, 2], 'id': 1, 'best_crystal': None}]}], 
            results
        )
    
    def test__single_experiment__single_crystal__multiple_containers__single_runlist(self):
        self.assertRaises(ValueError, self._test, multiple_containers=True)
    
    def test__single_experiment__single_crystal__single_container__multiple_runlists(self):
        results = self._test(multiple_runlists=True)
        self.assertEqual(
            [{'containers': {1: {'crystals': [1], 'id': 1}},
              'crystals': {1: {'id': 1}},
              'experiments': [{'crystals': [1], 'id': 1, 'best_crystal': None}]},
              {'containers': {1: {'crystals': [1], 'id': 1}},
              'crystals': {1: {'id': 1}},
              'experiments': [{'crystals': [1], 'id': 1, 'best_crystal': None}]}], 
            results
        )
    
    # 2 'multiple'
    
    def test__multiple_experiments__multiple_crystals__single_container__single_runlist(self):
        results = self._test(multiple_experiments=True, multiple_crystals=True)
        self.assertEqual(
            [{'containers': {1: {'crystals': [1, 2], 'id': 1}},
              'crystals': {1: {'id': 1}, 2: {'id': 2}},
              'experiments': [{'crystals': [1], 'id': 1, 'best_crystal': None}, 
                              {'crystals': [2], 'id': 2, 'best_crystal': None}]}], 
            results
        )
    
    def test__multiple_experiments__single_crystal__multiple_containers__single_runlist(self):
        self.assertRaises(ValueError, self._test, multiple_experiments=True, multiple_containers=True)
    
    # test removed, as this case can no longer happen
#    def test__multiple_experiments__single_crystal__single_container__multiple_runlists(self):
#        results = self._test(multiple_experiments=True, multiple_runlists=True)
#        self.assertEqual(
#            [{'containers': {1: {'crystals': [1], 'id': 1}},
#              'crystals': {1: {'id': 1}},
#              'experiments': [{'crystals': [1], 'id': 1, 'best_crystal': None}, 
#                              {'crystals': [1], 'id': 2, 'best_crystal': None}]},
#             {'containers': {1: {'crystals': [1], 'id': 1}},
#              'crystals': {1: {'id': 1}},
#              'experiments': [{'crystals': [1], 'id': 1, 'best_crystal': None}, 
#                              {'crystals': [1], 'id': 2, 'best_crystal': None}]}], 
#            results
#        )
#    
    # should be possible, but need to check on 
    def test__single_experiment__multiple_crystals__multiple_containers__single_runlist(self):
        results = self._test(multiple_crystals=True, multiple_containers=True)
        self.assertEqual(
            [{'containers': {1: {'crystals': [1], 'id': 1}, 2: {'crystals': [2], 'id': 2}},
              'crystals': {1: {'id': 1}, 2: {'id': 2}},
              'experiments': [{'crystals': [1,2], 'id': 1, 'best_crystal': None}]}], 
            results
        )
    
    def test__single_experiment__multiple_crystals__single_container__multiple_runlists(self):
        results = self._test(multiple_crystals=True, multiple_runlists=True)
        self.assertEqual(
            [{'containers': {1: {'crystals': [1, 2], 'id': 1}},
              'crystals': {1: {'id': 1}, 2: {'id': 2}},
              'experiments': [{'crystals': [1, 2], 'id': 1, 'best_crystal': None}]},
             {'containers': {1: {'crystals': [1, 2], 'id': 1}},
              'crystals': {1: {'id': 1}, 2: {'id': 2}},
              'experiments': [{'crystals': [1, 2], 'id': 1, 'best_crystal': None}]}], 
            results
        )
    
    def test__single_experiment__single_crystal__multiple_containers__multiple_runlists(self):
        self.assertRaises(ValueError, self._test, multiple_experiments=True, multiple_containers=True)
    
    # 3 'multiple'
    
    def test__multiple_experiments__multiple_crystals__mutiple_containers__single_runlist(self):
        results = self._test(multiple_experiments=True, multiple_crystals=True, multiple_containers=True)
        self.assertEqual(
            [{'containers': {1: {'crystals': [1], 'id': 1}, 2: {'crystals': [2], 'id': 2}},
              'crystals': {1: {'id': 1}, 2: {'id': 2}},
              'experiments': [{'crystals': [1], 'id': 1, 'best_crystal': None}, 
                              {'crystals': [2], 'id': 2, 'best_crystal': None}]}], 
            results
        )
    
    def test__multiple_experiments__multiple_crystals__single_container__multiple_runlists(self):
        results = self._test(multiple_experiments=True, multiple_crystals=True, multiple_runlists=True)
        self.assertEqual(
            [{'containers': {1: {'crystals': [1, 2], 'id': 1}},
              'crystals': {1: {'id': 1}, 2: {'id': 2}},
              'experiments': [{'crystals': [1], 'id': 1, 'best_crystal': None}, 
                              {'crystals': [2], 'id': 2, 'best_crystal': None}]},
             {'containers': {1: {'crystals': [1, 2], 'id': 1}},
              'crystals': {1: {'id': 1}, 2: {'id': 2}},
              'experiments': [{'crystals': [1], 'id': 1, 'best_crystal': None}, 
                              {'crystals': [2], 'id': 2, 'best_crystal': None}]}], 
            results
        )
    
    def test__multiple_experiments__single_crystal__mutiple_containers__multiple_runlists(self):
        self.assertRaises(ValueError, self._test, multiple_experiments=True, multiple_containers=True)
        
    def test__single_experiment__multiple_crystals__multiple_containers__multiple_runlists(self):
        results = self._test(multiple_crystals=True, multiple_containers=True, multiple_runlists=True)
        self.assertEqual(
            [{'containers': {1: {'crystals': [1], 'id': 1}},
              'crystals': {1: {'id': 1}},
              'experiments': [{'crystals': [1,2], 'id': 1, 'best_crystal': None}]},
             {'containers': {2: {'crystals': [2], 'id': 2}},
              'crystals': {2: {'id': 2}},
              'experiments': [{'crystals': [1,2], 'id': 1, 'best_crystal': None}]}], 
            results
        )
        
    # 4 'multiple'
    
    def test__multiple_experiments__multiple_crystals__multiple_containers__multiple_runlists(self):
        results = self._test(multiple_experiments=True, multiple_crystals=True, multiple_containers=True, multiple_runlists=True)
        self.assertEqual(
            [{'containers': {1: {'crystals': [1], 'id': 1}},
              'crystals': {1: {'id': 1}},
              'experiments': [{'crystals': [1], 'id': 1, 'best_crystal': None}]}, 
             {'containers': {2: {'crystals': [2], 'id': 2}},
              'crystals': {2: {'id': 2}},
              'experiments': [{'crystals': [2], 'id': 2, 'best_crystal': None}]}], 
            results
        )
        
    def test_best_crystal_in_same_runlist(self):
        self.set_up_default_runlist()
        
        crystal2 = create_Crystal(project=self.project, name='crystal2', container=self.container)
#        self.experiment.crystals.add(crystal2)
        self.experiment.save()
        crystal2.experiment = self.experiment
        crystal2.save()
        data2 = create_Data(project=self.project, experiment=self.experiment, crystal=crystal2)
        result2 = create_Result(project=self.project, experiment=self.experiment, crystal=crystal2, data=data2)
        
        perform_action(self.shipment, 'send')
        perform_action(self.shipment, 'receive')
        perform_action(self.runlist, 'load')
        
        request = self.get_request()
        
        response = detailed_runlist(request, self.runlist.pk)
        self.assertEqual({'containers': {1: {'crystals': [1, 2], 'id': 1}},
                          'crystals': {1: {'id': 1}, 2: {'id': 2}},
                          'experiments': [{'crystals': [1,2], 'id': 1, 'best_crystal': None}]}, 
                         self._filter([response])[0])
        
        self.experiment.plan = Experiment.EXP_PLANS.RANK_AND_COLLECT_BEST
        self.experiment.save()
        
        response = detailed_runlist(request, self.runlist.pk)
        self.assertEqual({'containers': {1: {'crystals': [1, 2], 'id': 1}},
                          'crystals': {1: {'id': 1}, 2: {'id': 2}},
                          'experiments': [{'crystals': [1,2], 'id': 1, 'best_crystal': 2}]}, 
                         self._filter([response])[0])
        
    def test_best_crystal_in_another_runlist(self):
        self.set_up_default_runlist()
        
        container2 = create_Container(project=self.project, label='container2')
        crystal2 = create_Crystal(project=self.project, name='crystal2', container=container2)
#        self.experiment.crystals.add(crystal2)
        self.experiment.save()
        crystal2.experiment = self.experiment
        crystal2.save()
        data2 = create_Data(project=self.project, experiment=self.experiment, crystal=crystal2)
        result2 = create_Result(project=self.project, experiment=self.experiment, crystal=crystal2, data=data2)
        runlist2 = create_Runlist(name='runlist2', containers=[container2])
        
        perform_action(self.shipment, 'send')
        perform_action(self.shipment, 'receive')
        perform_action(self.runlist, 'load')
        
        request = self.get_request()
        
        response = detailed_runlist(request, self.runlist.pk)
        self.assertEqual({'containers': {1: {'crystals': [1], 'id': 1}},
                          'crystals': {1: {'id': 1}},
                          'experiments': [{'crystals': [1,2], 'id': 1, 'best_crystal': None}]}, 
                         self._filter([response])[0])
        
        self.experiment.plan = Experiment.EXP_PLANS.RANK_AND_COLLECT_BEST
        self.experiment.save()
        
        response = detailed_runlist(request, self.runlist.pk)
        self.assertEqual({'containers': {1: {'crystals': [1], 'id': 1}},
                          'crystals': {1: {'id': 1}},
                          'experiments': [{'crystals': [1,2], 'id': 1, 'best_crystal': 2}]}, 
                         self._filter([response])[0])