import unittest
import logging

from mxlive.users.tests.test_utils import DjangoTestCase
from mxlive.users.tests.test_utils import create_Runlist

from mxlive.users.models import Shipment
from mxlive.users.models import Container
from mxlive.users.models import Crystal

from mxlive.users.models import change_status
from mxlive.users.models import perform_action

from mxlive.staff.models import Runlist
from mxlive.staff.models import AutomounterLayout

class AutomounterLayoutTest(DjangoTestCase):
    """ Test the Automounter model """
    
    def setUp(self):
        super(AutomounterLayoutTest, self).setUp()
        self.set_up_default_adminuser()
        self.set_up_default_runlist()
        
    def test_adds(self):
        auto = AutomounterLayout()
        auto.save()
        a = Runlist(automounter=auto)
        a.save()
        
        # to create a container, I need a project
        c = Container()
        c.kind = Container.TYPE.UNI_PUCK
        c.project = self.container.project
        c.save()
        
        # confirm adding puck takes first available slot
        self.assertEqual(None, a.automounter.get_position(c))
        self.assertTrue(a.automounter.add_container(c))
        self.assertEqual('L1', a.automounter.get_position(c))
        logging.critical(a.automounter.json_dict())
        
        c2 = Container()
        c2.kind = Container.TYPE.UNI_PUCK
        c2.project = self.container.project
        c2.save()
        
        #second puck takes second available spot
        self.assertEqual(None, a.automounter.get_position(c2))
        self.assertTrue(a.automounter.add_container(c2))
        self.assertEqual('L2', a.automounter.get_position(c2))
        logging.critical(a.automounter.json_dict())
        
        c3 = Container()
        c3.kind = Container.TYPE.CASSETTE
        c3.project = self.container.project
        c3.save()
        
        # adding a cassette will take 4 spots, must use up all of M
        self.assertEqual(None, a.automounter.get_position(c3))
        self.assertTrue(a.automounter.add_container(c3))
        self.assertEqual('M1', a.automounter.get_position(c3))
        logging.critical(a.automounter.json_dict())
        
        c4 = Container()
        c4.kind = Container.TYPE.UNI_PUCK
        c4.project = self.container.project
        c4.save()
        
        # next puck takes next avail spot
        self.assertEqual(None, a.automounter.get_position(c4))
        self.assertTrue(a.automounter.add_container(c4))
        self.assertEqual('L3', a.automounter.get_position(c4))
        logging.critical(a.automounter.json_dict())
        
        c5 = Container()
        c5.kind = Container.TYPE.UNI_PUCK
        c5.project = self.container.project
        c5.save()
        
        # next puck takes next avail spot
        self.assertEqual(None, a.automounter.get_position(c5))
        self.assertTrue(a.automounter.add_container(c5))
        self.assertEqual('L4', a.automounter.get_position(c5))
        logging.critical(a.automounter.json_dict())
        
        c6 = Container()
        c6.kind = Container.TYPE.UNI_PUCK
        c6.project = self.container.project
        c6.save()
        
        # next puck takes next avail spot
        self.assertEqual(None, a.automounter.get_position(c6))
        self.assertTrue(a.automounter.add_container(c6))
        logging.critical(a.automounter.json_dict())
        self.assertEqual('R1', a.automounter.get_position(c6))
        logging.critical(a.automounter.json_dict())
        
    def test_add_remove(self):
        auto = AutomounterLayout()
        auto.save()
        a = Runlist(automounter=auto)
        a.save()
        
        c = Container()
        c.kind = Container.TYPE.UNI_PUCK
        c.project = self.container.project
        c.save()
        
        self.assertFalse(a.automounter.remove_container(c))
        self.assertTrue(a.automounter.add_container(c))
        self.assertTrue(a.automounter.remove_container(c))
        self.assertFalse(a.automounter.remove_container(c))
        
        c.kind = Container.TYPE.CASSETTE
        
        self.assertFalse(a.automounter.remove_container(c))
        self.assertTrue(a.automounter.add_container(c))
        self.assertTrue(a.automounter.remove_container(c))
        self.assertFalse(a.automounter.remove_container(c))
        
    def test_add_full(self):
        auto = AutomounterLayout()
        auto.save()
        a = Runlist(automounter=auto)
        a.save()
        
        for i in range(3):
            c = Container()
            c.kind = Container.TYPE.CASSETTE
            c.project = self.container.project
            c.save()
            
            self.assertTrue(a.automounter.add_container(c))
        
        c2 = Container()
        c2.kind = Container.TYPE.UNI_PUCK
        c2.project = self.container.project
        c2.save()
        
        self.assertFalse(a.automounter.add_container(c2))
        
    def test_add_container_to_runlist(self):
        auto = AutomounterLayout()
        auto.save()
        a = Runlist(automounter=auto)
        a.save()
        
        c = Container()
        c.label = 'test'
        c.kind = Container.TYPE.UNI_PUCK
        c.project = self.container.project
        c.save()
        self.assertEqual(a.num_containers(), 0)
        
        a.containers.add(c)
        a.save()
        
        self.assertEqual(a.num_containers(), 1)
        self.assertEqual ('test', a.container_list())
        self.assertEqual('L1', a.automounter.get_position(c))
        
        self.assertTrue(False)
        
        
        
class RunlistTest(DjangoTestCase):
    """ Test the Runlist model """
    
    def setUp(self):
        super(RunlistTest, self).setUp()
        self.set_up_default_adminuser()
        self.set_up_default_runlist()
    
    def test_required(self):
        auto = AutomounterLayout()
        auto.save()
        a = Runlist(automounter=auto)
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
        
