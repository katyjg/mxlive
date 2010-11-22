""" Django models tests """
import unittest

from django.db import models
from django.db import IntegrityError

from imm.lims.tests.test_utils import create_Beamline
from imm.lims.tests.test_utils import create_Laboratory
from imm.lims.tests.test_utils import create_Shipment
from imm.lims.tests.test_utils import create_Dewar
from imm.lims.tests.test_utils import create_Container
from imm.lims.tests.test_utils import create_Crystal
from imm.lims.tests.test_utils import create_Experiment
from imm.lims.tests.test_utils import create_Project
from imm.lims.tests.test_utils import create_Strategy
from imm.lims.tests.test_utils import DjangoTestCase

from imm.lims.models import Container
from imm.lims.models import Shipment
from imm.lims.models import Dewar
from imm.lims.models import Crystal
from imm.lims.models import Experiment
from imm.lims.models import delete
from imm.lims.models import ExcludeManagerWrapper
from imm.lims.models import FilterManagerWrapper
from imm.lims.models import perform_action
from imm.lims.models import archive
from imm.lims.models import change_status

class BeamlineTest(unittest.TestCase):
    """ Tests for BeamLine model """
    
    def test_defaults(self):
        beamline = create_Beamline()
        self.assertEqual(4.0, beamline.energy_lo)
        self.assertEqual(18.5, beamline.energy_hi)
        self.assertEqual('', beamline.name)
        self.assertEqual('', beamline.contact_phone)
        
class LaboratoryTest(unittest.TestCase):
    """ Tests for Laboratory model """
    
    def test_defaults(self):
        lab = create_Laboratory()
        
class ProjectTest(DjangoTestCase):
    """ Tests for Project model """
    
    def test_unique_User(self):
        self.set_up_default_project()
        self.assertRaises(IntegrityError, create_Project, lab=self.lab, user=self.user)
        
    def test_cascading_delete(self):
        self.set_up_default_experiment()
        
        self.assertNotEqual(0, Experiment.objects.count())
        self.assertNotEqual(0, Crystal.objects.count())
        self.assertNotEqual(0, Container.objects.count())
        self.assertNotEqual(0, Dewar.objects.count())
        
        self.project.delete()
        
        self.assertEqual(0, Experiment.objects.count())
        self.assertEqual(0, Crystal.objects.count())
        self.assertEqual(0, Container.objects.count())
        self.assertEqual(0, Dewar.objects.count())
        
        
class DewarTest(DjangoTestCase):
    """ Tests for Dewar model """
    
    def setUp(self):
        super(DewarTest, self).setUp()
        self.set_up_default_project()
    
    def test_code_max_length(self):
        a = create_Dewar(project=self.project)
        self.assertEqual('abc123', a.code)
        b = create_Dewar(project=self.project, code='a')
        self.assertEqual('a', b.code)
        c = create_Dewar(project=self.project, code='a' * 128)
        self.assertEqual('a' * 128, c.code)
        d = create_Dewar(project=self.project, code='a' * 129)
        self.assertEqual('a' * 129, d.code)
        
    def test_update_parent_shipment(self):
        self.set_up_default_dewar()
        self.assertEqual(Shipment.STATES.DRAFT, self.shipment.status)
        self.assertEqual(Dewar.STATES.DRAFT, self.dewar.status)
        
        # shipment no updated if not all Dewars are recvd
        self.dewar.receive_parent_shipment()
        self.reload_models()
        self.assertEqual(Shipment.STATES.DRAFT, self.shipment.status)
        self.assertEqual(Dewar.STATES.DRAFT, self.dewar.status)
        
        # shipment is updated if not all Dewars are recvd
        self.dewar.status = Dewar.STATES.ON_SITE
        self.dewar.save()
        self.dewar.receive_parent_shipment()
        self.reload_models()
        self.assertEqual(Shipment.STATES.ON_SITE, self.shipment.status)
        self.assertEqual(Dewar.STATES.ON_SITE, self.dewar.status)

        
class CrystalTest(DjangoTestCase):
    """ Tests for Crystal model """
    
    def setUp(self):
        super(CrystalTest, self).setUp()
        self.set_up_default_project()
    
    def test_unique_together_null(self):
        # UNIQUE not enforce when Container/Location are NULL
        create_Crystal(project=self.project, name='crystal123')
        create_Crystal(project=self.project, name='crystal456')
        
    def test_unique_together_IntegrityError(self):
        self.set_up_default_container()
        create_Crystal(project=self.project, name='crystal123', container=self.container, container_location='1')
        self.assertRaises(IntegrityError, create_Crystal, project=self.project, name='crystal456', container=self.container, container_location='1')
        
    def test_update_associated_experiments_one_crystal(self):
        self.set_up_default_experiment()
        
        self.assertEqual(Crystal.STATES.DRAFT, self.crystal.status)
        self.assertEqual(Experiment.STATES.DRAFT, self.experiment.status)
        
        # nothing happens when DRAFT
        self.crystal.activate_associated_experiments()
        self.reload_models()
        self.assertEqual(Crystal.STATES.DRAFT, self.crystal.status)
        self.assertEqual(Experiment.STATES.DRAFT, self.experiment.status)
        
        # all Crystals are ON_SITE, update Experiment
        self.crystal.status = Crystal.STATES.ON_SITE
        self.crystal.save()
        self.crystal.activate_associated_experiments()
        self.reload_models()
        self.assertEqual(Crystal.STATES.ON_SITE, self.crystal.status)
        self.assertEqual(Experiment.STATES.ACTIVE, self.experiment.status)
        
    def test_update_associated_experiments_many_crystals(self):
        self.set_up_default_experiment()
        self.experiment.save()
        c2 = create_Crystal(project=self.project)
        c2.experiment = self.experiment
        c2.save()
        
        self.assertEqual(Crystal.STATES.DRAFT, self.crystal.status)
        self.assertEqual(Crystal.STATES.DRAFT, c2.status)
        self.assertEqual(Experiment.STATES.DRAFT, self.experiment.status)
        
        # nothing happens when DRAFT
        self.crystal.activate_associated_experiments()
        self.reload_models()
        self.assertEqual(Crystal.STATES.DRAFT, self.crystal.status)
        self.assertEqual(Crystal.STATES.DRAFT, c2.status)
        self.assertEqual(Experiment.STATES.DRAFT, self.experiment.status)
        
        # not all Crystals are ON_SITE, update Experiment should do nothing
        self.crystal.status = Crystal.STATES.ON_SITE
        self.crystal.save()
        self.crystal.activate_associated_experiments()
        self.reload_models()
        self.assertEqual(Crystal.STATES.ON_SITE, self.crystal.status)
        self.assertEqual(Crystal.STATES.DRAFT, c2.status)
        self.assertEqual(Experiment.STATES.DRAFT, self.experiment.status)
        
        # all Crystals are ON_SITE, update Experiment should update
        c2.status = Crystal.STATES.ON_SITE
        c2.save()
        self.crystal.activate_associated_experiments()
        self.reload_models()
        self.assertEqual(Crystal.STATES.ON_SITE, self.crystal.status)
        self.assertEqual(Crystal.STATES.ON_SITE, c2.status)
        self.assertEqual(Experiment.STATES.ACTIVE, self.experiment.status)
        
class StrategyTest(DjangoTestCase):
    """ Tests for Strategy model """
    
    def setUp(self):
        super(StrategyTest, self).setUp()
        self.set_up_default_strategy()
        
    def test_is_rejectable(self):
        self.assertFalse(self.strategy.is_rejectable())
        
        perform_action(self.shipment, 'send')
        perform_action(self.shipment, 'receive')
        self.reload_models()
        
        self.assertTrue(self.strategy.is_rejectable())
        
        perform_action(self.strategy, 'reject')
        
        self.assertFalse(self.strategy.is_rejectable())
        
    def test_is_resubmittable(self):
        self.assertFalse(self.strategy.is_resubmittable())
        
        perform_action(self.shipment, 'send')
        perform_action(self.shipment, 'receive')
        self.reload_models()
        
        self.assertTrue(self.strategy.is_resubmittable())
        
        perform_action(self.strategy, 'resubmit')
        
        self.assertFalse(self.strategy.is_resubmittable())

    def test_is_strategy_type(self):
        self.assertTrue(self.strategy.is_strategy_type)
        
    def test_unique_result(self):
        self.assertRaises(IntegrityError, create_Strategy, project=self.project, result=self.result)
        
class ShipmentTest(DjangoTestCase):
    """ Tests for Shipment model """
    
    def setUp(self):
        super(ShipmentTest, self).setUp()
        self.set_up_default_project()
        self.set_up_default_shipment()
    
    def test_shipping_errors_no_Dewars(self):
        self.assertEqual(["no Dewars"], self.shipment.shipping_errors())

    def test_shipping_errors_empty_Dewar(self):
        self.set_up_default_dewar()
        self.assertEqual(["empty Dewar (dewar123)"], self.shipment.shipping_errors())
        
    def test_shipping_errors_empty_Container(self):
        self.set_up_default_container()
        self.assertEqual(["empty Container (container123)"], self.shipment.shipping_errors())
        
    def test_no_shipping_errors_orphaned_Crystal(self):
        self.set_up_default_crystal()
        self.assertEqual([], self.shipment.shipping_errors())
        
    def test_shipping_errors_badly_orphaned_Crystal(self):
        self.set_up_default_experiment()
        create_Crystal(project=self.project, name='crystal456')
        self.assertEqual(["Crystal (crystal456) not in Container"], self.shipment.shipping_errors())
        
    def test_no_shipping_errors(self):
        self.set_up_default_experiment()
        self.assertEqual([], self.shipment.shipping_errors())
        
    def test_states(self):
        self.assertEqual(0, Shipment.STATES.DRAFT)
        self.assertEqual(1, Shipment.STATES.SENT)
        self.assertEqual(2, Shipment.STATES.ON_SITE)
        self.assertEqual(3, Shipment.STATES.RETURNED)
        self.assertEqual(4, Shipment.STATES.ARCHIVED)
        
    def test_setup_default_experiment_no_orphan_crystals(self):
        self.set_up_default_experiment()
        self.assertEqual(1, Experiment.objects.count())
        self.shipment.setup_default_experiment()
        self.assertEqual(1, Experiment.objects.count())
        
    def test_setup_default_experiment_orphan_crystals(self):
        self.set_up_default_experiment()
        self.assertEqual(1, Experiment.objects.count())
        crystal = create_Crystal(project=self.project, name='I have no Experiment')
        self.shipment.setup_default_experiment()
        self.assertEqual(2, Experiment.objects.count())
        self.assertTrue([crystal], Experiment.objects.get(name="Default Experiment").crystals)
        
class ModelsTest(DjangoTestCase):
    
    def setUp(self):
        super(ModelsTest, self).setUp()
        self.set_up_default_project()
        self.set_up_default_shipment()
        self.set_up_default_dewar()
        
    def test_delete_Dewar_shipment(self):
        delete(Shipment, self.shipment.id, [(Dewar, 'shipment')])
        self.assertEqual(1, Dewar.objects.count())
        
    def test_delete_nothing(self):
        delete(Shipment, self.shipment.id, [])
        self.assertEqual(0, Dewar.objects.count())
        
    def test_delete_invalid_pk(self):
        self.assertRaises(Shipment.DoesNotExist, delete, Shipment, -999, [])
        
    def test_archive(self):
        self.set_up_default_crystal()
        perform_action(self.shipment, 'send')
        self.reload_models()
        perform_action(self.shipment, 'receive')
        self.reload_models()
        perform_action(self.shipment, 'return')
        self.reload_models()
        archive(Shipment, self.shipment.id)
        self.reload_models()
        self.assertEqual(Shipment.STATES.ARCHIVED, self.shipment.status)
        self.assertEqual(Dewar.STATES.ARCHIVED, self.dewar.status)
        self.assertEqual(Container.STATES.ARCHIVED, self.container.status)
        self.assertEqual(Crystal.STATES.ARCHIVED, self.crystal.status)
        
    def test_archive_shipment(self):
        self.set_up_default_crystal()
        self.assertEqual(Shipment.STATES.DRAFT, self.shipment.status)
        self.assertEqual(Dewar.STATES.DRAFT, self.dewar.status)
        self.assertEqual(Container.STATES.DRAFT, self.container.status)
        self.assertEqual(Crystal.STATES.DRAFT, self.crystal.status)
        self.assertEqual(self.container, self.crystal.container)
        perform_action(self.shipment, 'send')
        self.reload_models()
        perform_action(self.shipment, 'receive')
        self.reload_models()
        perform_action(self.shipment, 'return')
        self.reload_models()
        perform_action(self.shipment, 'archive') # archive it
        self.reload_models() # requery db to avoid using in-memory objects
        self.assertEqual(Shipment.STATES.ARCHIVED, self.shipment.status)
        self.assertEqual(Dewar.STATES.ARCHIVED, self.dewar.status)
        self.assertEqual(Container.STATES.ARCHIVED, self.container.status)
        self.assertEqual(Crystal.STATES.ARCHIVED, self.crystal.status)
        self.assertEqual(self.container, self.crystal.container)
        
    def test_send_shipment(self):
        self.set_up_default_crystal()
        self.assertEqual(Shipment.STATES.DRAFT, self.shipment.status)
        self.assertEqual(Dewar.STATES.DRAFT, self.dewar.status)
        self.assertEqual(Container.STATES.DRAFT, self.container.status)
        self.assertEqual(Crystal.STATES.DRAFT, self.crystal.status)
        self.assertEqual(self.container, self.crystal.container)
        self.assertEqual(None, self.shipment.date_shipped)
        perform_action(self.shipment, 'send') # send it
        self.reload_models() # requery db to avoid using in-memory objects
        self.assertEqual(Shipment.STATES.SENT, self.shipment.status)
        self.assertEqual(Dewar.STATES.SENT, self.dewar.status)
        self.assertEqual(Container.STATES.SENT, self.container.status)
        self.assertEqual(Crystal.STATES.SENT, self.crystal.status)
        self.assertEqual(self.container, self.crystal.container)
        self.assertNotEqual(None, self.shipment.date_shipped)
        
    def test_receive_shipment(self):
        self.set_up_default_crystal()
        self.assertEqual(Shipment.STATES.DRAFT, self.shipment.status)
        self.assertEqual(Dewar.STATES.DRAFT, self.dewar.status)
        self.assertEqual(Container.STATES.DRAFT, self.container.status)
        self.assertEqual(Crystal.STATES.DRAFT, self.crystal.status)
        self.assertEqual(self.container, self.crystal.container)
        self.assertEqual(None, self.shipment.date_received)
        perform_action(self.shipment, 'send')
        self.reload_models()
        perform_action(self.shipment, 'receive') # receive it
        self.reload_models() # requery db to avoid using in-memory objects
        self.assertEqual(Shipment.STATES.ON_SITE, self.shipment.status)
        self.assertEqual(Dewar.STATES.ON_SITE, self.dewar.status)
        self.assertEqual(Container.STATES.ON_SITE, self.container.status)
        self.assertEqual(Crystal.STATES.ON_SITE, self.crystal.status)
        self.assertEqual(self.container, self.crystal.container)
        self.assertNotEqual(None, self.shipment.date_received)
        
    def test_return_shipment(self):
        self.set_up_default_crystal()
        self.assertEqual(Shipment.STATES.DRAFT, self.shipment.status)
        self.assertEqual(Dewar.STATES.DRAFT, self.dewar.status)
        self.assertEqual(Container.STATES.DRAFT, self.container.status)
        self.assertEqual(Crystal.STATES.DRAFT, self.crystal.status)
        self.assertEqual(self.container, self.crystal.container)
        self.assertEqual(None, self.shipment.date_returned)
        perform_action(self.shipment, 'send')
        self.reload_models()
        perform_action(self.shipment, 'receive')
        self.reload_models()
        perform_action(self.shipment, 'return') # return it
        self.reload_models() # requery db to avoid using in-memory objects
        self.assertEqual(Shipment.STATES.RETURNED, self.shipment.status)
        self.assertEqual(Dewar.STATES.RETURNED, self.dewar.status)
        self.assertEqual(Container.STATES.RETURNED, self.container.status)
        self.assertEqual(Crystal.STATES.RETURNED, self.crystal.status)
        self.assertEqual(self.container, self.crystal.container)
        self.assertNotEqual(None, self.shipment.date_returned)
        
    def test_change_status(self):
        self.assertEqual(Shipment.STATES.DRAFT, self.shipment.status)
        self.assertRaises(ValueError, change_status, self.shipment, Shipment.STATES.RETURNED)
        change_status(self.shipment, Shipment.STATES.SENT)
        self.assertEqual(Shipment.STATES.SENT, self.shipment.status)
        self.assertRaises(KeyError, change_status, self.shipment, 999)
        
class ExcludeManagerWrapperTest(DjangoTestCase):
    
    def setUp(self):
        super(ExcludeManagerWrapperTest, self).setUp()
        self.set_up_default_project()
        self.set_up_default_shipment()
        self.set_up_default_crystal()
        
    def test(self):
        # without excludes, all the results are returned
        self.assertEqual([self.shipment], list(self.project.shipment_set.all()))
        self.assertEqual([self.dewar], list(self.project.dewar_set.all()))
        self.assertEqual([self.container], list(self.project.container_set.all()))
        self.assertEqual([self.crystal], list(self.project.crystal_set.all()))
        # with the excludes, no results are returned
        self.assertEqual([], list(ExcludeManagerWrapper(self.project.shipment_set, status__exact=self.shipment.status).all()))
        self.assertEqual([], list(ExcludeManagerWrapper(self.project.dewar_set, status__exact=self.dewar.status).all()))
        self.assertEqual([], list(ExcludeManagerWrapper(self.project.container_set, status__exact=self.container.status).all()))
        self.assertEqual([], list(ExcludeManagerWrapper(self.project.crystal_set, name__exact=self.crystal.name).all()))
        
class FilterManagerWrapperTest(DjangoTestCase):
    
    def setUp(self):
        super(FilterManagerWrapperTest, self).setUp()
        self.set_up_default_project()
        self.set_up_default_shipment()
        self.set_up_default_crystal()
        
    def test(self):
        # without excludes, all the results are returned
        self.assertEqual([self.shipment], list(self.project.shipment_set.all()))
        self.assertEqual([self.dewar], list(self.project.dewar_set.all()))
        self.assertEqual([self.container], list(self.project.container_set.all()))
        self.assertEqual([self.crystal], list(self.project.crystal_set.all()))
        # with the excludes, no results are returned
        self.assertEqual([], list(FilterManagerWrapper(self.project.shipment_set, status__in=[self.shipment.status+1]).all()))
        self.assertEqual([], list(FilterManagerWrapper(self.project.dewar_set, status__in=[self.dewar.status+1]).all()))
        self.assertEqual([], list(FilterManagerWrapper(self.project.container_set, status__in=[self.container.status+1]).all()))
        self.assertEqual([], list(FilterManagerWrapper(self.project.crystal_set, name__in=[self.crystal.name+'1']).all()))
        
class PriorityTest(DjangoTestCase):
    
    def setUp(self):
        super(PriorityTest, self).setUp()
        self.set_up_default_experiment()
        self.experiment2 = create_Experiment(project=self.project, crystals=[self.crystal])
        
    def reload_models(self):
        super(PriorityTest, self).reload_models()
        try:
            self.experiment2 = Experiment.objects.get(pk=self.experiment2.pk)
        except Experiment.DoesNotExist:
            self.experiment2 = None
        
    def test_container_priority_is_max_of_experiments(self):
        
        self.assertEqual(self.experiment.staff_priority, 0)
        self.assertEqual(self.experiment2.staff_priority, 0)
        self.assertEqual(self.container.staff_priority, 0)
        
        self.experiment.update_priority()
        self.reload_models()
        
        self.assertEqual(self.experiment.staff_priority, 0)
        self.assertEqual(self.experiment2.staff_priority, 0)
        self.assertEqual(self.container.staff_priority, 0)
        
        self.experiment.staff_priority = 1
        self.experiment.update_priority()
        self.experiment.save()
        self.reload_models()
        
        self.assertEqual(self.experiment.staff_priority, 1)
        self.assertEqual(self.experiment2.staff_priority, 0)
        self.container.update_priority()
        self.assertEqual(self.container.staff_priority, 1)
        
        self.experiment2.staff_priority = 2
        self.experiment2.save()
        self.reload_models()
        
        self.assertEqual(self.experiment.staff_priority, 1)
        self.assertEqual(self.experiment2.staff_priority, 2)
        self.assertEqual(self.container.staff_priority, 2)
        
        self.experiment2.delete()
        self.reload_models()
        
        self.assertEqual(self.experiment.staff_priority, 1)
        self.assertEqual(self.container.staff_priority, 1)
        
        
class ResultTest(DjangoTestCase):
    """
    Tests for Result model
    """
    def setUp(self):
        super(ResultTest, self).setUp()
        self.set_up_default_strategy()
        self.set_up_default_result()

    def test_is_resubmittable(self):
        self.assertFalse(self.strategy.is_resubmittable())
        self.assertFalse(self.result.is_resubmittable())

        perform_action(self.shipment, 'send')
        perform_action(self.shipment, 'receive')
        self.reload_models()

        self.assertTrue(self.result.is_resubmittable())

        perform_action(self.strategy, 'resubmit')

        self.assertFalse(self.result.is_resubmittable())

    def test_get_results_link(self):

        link = self.result.get_results_link()

        expected_link = "resubmit/?%s=%d&%s=%d&%s=%s&%s=%f&%s=%f&%s=%f&%s=%f&%s=%f&%s=%f&%s=%f&%s=%s&%s=%d" % \
        ('project',       self.strategy.project.pk,
         'strategy',      self.strategy.pk,
         'name',          'Resubmitted_'+ self.strategy.name + '_' + self.strategy.result.crystal.name,
         'delta_angle',   self.strategy.delta_angle,
         'total_angle',   self.strategy.total_angle,
         'energy',        self.strategy.energy,
         'resolution',    self.strategy.exp_resolution,
         'multiplicity',  self.strategy.exp_multiplicity,
         'i_sigma',       self.strategy.exp_i_sigma,
         'r_meas',        self.strategy.exp_r_factor,
         'crystals',      self.strategy.result.crystal.pk,
         'plan',          self.result.experiment.EXP_PLANS.JUST_COLLECT 
        )

        self.assertEqual(expected_link, link)
