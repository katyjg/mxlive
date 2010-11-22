import unittest
import logging

from imm.lims.tests.test_utils import DjangoTestCase
from imm.lims.tests.test_utils import create_Runlist

from imm.lims.models import Shipment
from imm.lims.models import Container
from imm.lims.models import Crystal

from imm.lims.models import change_status
from imm.lims.models import perform_action
from imm.messaging.models import Message

from imm.staff.models import Runlist

class RunlistTest(DjangoTestCase):
    """ Test the Runlist model """
    
    def setUp(self):
        super(RunlistTest, self).setUp()
        self.set_up_default_adminuser()
        self.set_up_default_runlist()
    
    def test_required(self):
        a = Runlist()
        a.save()
        self.assertEqual([], list(a.experiments.all()))
        self.assertEqual([], list(a.containers.all()))
        
    def test_change_status(self):
        self.assertEqual(Runlist.STATES.PENDING, self.runlist.status)
        self.assertRaises(ValueError, change_status, self.runlist, Runlist.STATES.CLOSED)
        
        change_status(self.runlist, Runlist.STATES.LOADED)
        self.assertEqual(Runlist.STATES.LOADED, self.runlist.status)
        
        change_status(self.runlist, Runlist.STATES.COMPLETED)
        self.assertEqual(Runlist.STATES.COMPLETED, self.runlist.status)
        
        change_status(self.runlist, Runlist.STATES.CLOSED)
        self.assertEqual(Runlist.STATES.CLOSED, self.runlist.status)
        
        self.runlist.status = Runlist.STATES.COMPLETED
        change_status(self.runlist, Runlist.STATES.PENDING)
        self.assertEqual(Runlist.STATES.PENDING, self.runlist.status)
        
        self.assertRaises(KeyError, change_status, self.runlist, 999)
        
    def test_load(self):
        self.assertEqual(Runlist.STATES.PENDING, self.runlist.status)
        perform_action(self.shipment, 'send')
        perform_action(self.shipment, 'receive')
        perform_action(self.runlist, 'load')
        self.reload_models()
        self.assertEqual(Runlist.STATES.LOADED, self.runlist.status)
        
    def test_unload(self):
        self.assertEqual(Runlist.STATES.PENDING, self.runlist.status)
        perform_action(self.shipment, 'send')
        perform_action(self.shipment, 'receive')
        perform_action(self.runlist, 'load')
        self.reload_models()
        perform_action(self.runlist, 'unload')
        self.reload_models()
        self.assertEqual(Runlist.STATES.COMPLETED, self.runlist.status)
        
    def test_accept(self):
        self.assertEqual(Runlist.STATES.PENDING, self.runlist.status)
        perform_action(self.shipment, 'send')
        perform_action(self.shipment, 'receive')
        perform_action(self.runlist, 'load')
        self.reload_models()
        perform_action(self.runlist, 'unload')
        self.reload_models()
        self.assertEqual(0, Message.objects.count())
        perform_action(self.runlist, 'accept', {'message': 'message'})
        self.reload_models()
        self.assertEqual(1, Message.objects.count())
        self.assertEqual(Runlist.STATES.CLOSED, self.runlist.status)
        
    def test_reject(self):
        self.assertEqual(Runlist.STATES.PENDING, self.runlist.status)
        perform_action(self.shipment, 'send')
        perform_action(self.shipment, 'receive')
        perform_action(self.runlist, 'load')
        self.reload_models()
        perform_action(self.runlist, 'unload')
        self.reload_models()
        perform_action(self.runlist, 'reject')
        self.reload_models()
        self.assertEqual(Runlist.STATES.PENDING, self.runlist.status)
        
        
class RunlistLoadUnloadTest(DjangoTestCase):
    
    def setUp(self):
        super(RunlistLoadUnloadTest, self).setUp()
        self.set_up_default_adminuser()
        self.set_up_default_runlist()
         
    def test_load_invalid(self):
        self.assertEqual(Runlist.STATES.PENDING, self.runlist.status)
        self.assertRaises(ValueError, perform_action, self.runlist, 'unload')
        
    def test_unload_invalid(self):
        self.assertEqual(Runlist.STATES.PENDING, self.runlist.status)
        self.assertRaises(ValueError, perform_action, self.runlist, 'load')
    
    def test_load(self):
        perform_action(self.shipment, 'send')
        perform_action(self.shipment, 'receive')
        
        self.reload_models()
        
        self.assertEqual(Runlist.STATES.PENDING, self.runlist.status)
        self.assertEqual(Shipment.STATES.ON_SITE, self.shipment.status)
        self.assertEqual(Container.STATES.ON_SITE, self.container.status)
        self.assertEqual(Crystal.STATES.ON_SITE, self.crystal.status)
        
        perform_action(self.runlist, 'load')
        
        self.reload_models()
        
        self.assertEqual(Runlist.STATES.LOADED, self.runlist.status)
        self.assertEqual(Shipment.STATES.ON_SITE, self.shipment.status)
        self.assertEqual(Container.STATES.LOADED, self.container.status)
        self.assertEqual(Crystal.STATES.LOADED, self.crystal.status)
        
    def test_load_one_already_loaded(self):
        perform_action(self.shipment, 'send')
        perform_action(self.shipment, 'receive')
        
        self.reload_models()
        
        self.assertEqual(Runlist.STATES.PENDING, self.runlist.status)
        
        perform_action(self.runlist, 'load')
        
        self.assertEqual(Runlist.STATES.LOADED, self.runlist.status)
        
        runlist2 = create_Runlist(containers=[self.container], experiments=[self.experiment])
        
        # try to load another causes problems
        self.assertRaises(ValueError, perform_action, runlist2, 'load')
        
        # unload the other and retry
        perform_action(self.runlist, 'unload')
        perform_action(runlist2, 'load')
        
        runlist2 = Runlist.objects.get(pk=runlist2.pk)
        self.assertEqual(Runlist.STATES.LOADED, runlist2.status)
        
    def test_unload(self):
        perform_action(self.shipment, 'send')
        perform_action(self.shipment, 'receive')
        perform_action(self.runlist, 'load')
        
        self.reload_models()
        
        self.assertEqual(Runlist.STATES.LOADED, self.runlist.status)
        self.assertEqual(Shipment.STATES.ON_SITE, self.shipment.status)
        self.assertEqual(Container.STATES.LOADED, self.container.status)
        self.assertEqual(Crystal.STATES.LOADED, self.crystal.status)
        
        perform_action(self.runlist, 'unload')
        
        self.reload_models()
        
        self.assertEqual(Runlist.STATES.COMPLETED, self.runlist.status)
        self.assertEqual(Shipment.STATES.ON_SITE, self.shipment.status)
        self.assertEqual(Container.STATES.ON_SITE, self.container.status)
        self.assertEqual(Crystal.STATES.ON_SITE, self.crystal.status)
        