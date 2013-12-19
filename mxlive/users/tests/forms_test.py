""" Django models tests """
import unittest
import os

from mxlive.users.tests.test_utils import DjangoTestCase
from mxlive.users.tests.test_utils import TEST_FILES
from mxlive.users.tests.test_utils import create_Crystal

from mxlive.users.forms import ShipmentUploadForm
from mxlive.users.forms import ShipmentSendForm
from mxlive.users.forms import ContainerForm
from mxlive.users.forms import SampleSelectForm
from mxlive.users.forms import ExperimentFromStrategyForm

from mxlive.users.models import Shipment
from mxlive.users.models import Crystal
from mxlive.users.models import Container
from mxlive.users.models import Experiment

class ShipmentSendFormTest(DjangoTestCase):
    """ Tests for ShipmentSendForm class """
    
    def setUp(self):
        super(ShipmentSendFormTest, self).setUp()
        self.set_up_default_project()
        
    def test_validation(self):
        form = ShipmentSendForm()
        self.assertFalse(form.is_bound)
        self.assertFalse(form.is_valid())
        self.assertEqual({}, form.errors)
        
        form = ShipmentSendForm({})
        self.assertTrue(form.is_bound)
        self.assertFalse(form.is_valid())
        self.assertEqual({'project': ['This field is required.'], 
                          'tracking_code': ['This field is required.'], 
                          'carrier': ['This field is required.']}, form.errors)

class ShipmentUploadFormTest(DjangoTestCase):
    """ Tests for ShipmentUploadForm class """
    
    def setUp(self):
        super(ShipmentUploadFormTest, self).setUp()
        self.set_up_default_project()
        self.set_up_default_space_group(name='P2(1)2(1)2(1)')
        
    def test_invalid_file(self):
        form = ShipmentUploadForm({'project': self.project.pk}, {'excel' : file(os.path.join(TEST_FILES, 'not_a_spreadsheet.txt'), 'r')})
        self.assertEqual({'excel': ['Invalid Excel spreadsheet.']}, form.errors)
        self.assertFalse(form.is_valid())
    
    def test_validation(self):
        # unbound form
        form = ShipmentUploadForm()
        self.assertFalse(form.is_valid())
        self.assertEqual({}, form.errors)
        
        # empty data dicts
        form = ShipmentUploadForm({}, {})
        self.assertFalse(form.is_valid())
        self.assertEqual({'project': ['This field is required.'], 
                          'excel': ['This field is required.']}, form.errors)
        
        # valid dicts, invalid excel file
        form = ShipmentUploadForm({'project': self.project.pk}, {'excel' : file(os.path.join(TEST_FILES, 'errors.xls'), 'r')})
        self.assertEqual({'excel': ['Invalid Experiment name "" in cell Groups!$A$1.', 
                                    'Invalid Experiment type "" in cell Groups!$B$1.', 
                                    'Invalid Experiment plan "" in cell Groups!$C$1.', 
                                    'and 7 more errors...']}, form.errors)
        self.assertFalse(form.is_valid())
        
        # valid everything
        form = ShipmentUploadForm({'project': self.project.pk}, {'excel' : file(os.path.join(TEST_FILES, 'test.xls'), 'r')})
        self.assertEqual({}, form.errors)
        self.assertTrue(form.is_valid())
        
        # contrived example
        form = ShipmentUploadForm({'project': self.project.pk, 'excel': 'test'}, {})
        self.assertEqual({'excel': ['This field is required.']}, form.errors) # not found in correct dict
        self.assertFalse(form.is_valid())
        
        # contrived example
        form = ShipmentUploadForm({'project': self.project.pk}, {'excel': 'test'})
        self.assertRaises(AttributeError, form.is_valid)
        
    def test_save(self):
        # invalid spreadsheet
        form = ShipmentUploadForm({'project': self.project.pk}, {'excel' : file(os.path.join(TEST_FILES, 'errors.xls'), 'r')})
        self.assertRaises(AssertionError, form.save)
        
        # valid spreadsheet
        self.assertEqual(0, Shipment.objects.count())
        self.assertEqual(0, Container.objects.count())
        self.assertEqual(0, Crystal.objects.count())
        form = ShipmentUploadForm({'project': self.project.pk}, {'excel' : file(os.path.join(TEST_FILES, 'test.xls'), 'r')})
        form.save()
        self.assertEqual(1, Shipment.objects.count())
        self.assertEqual(4, Container.objects.count())
        self.assertEqual(8, Crystal.objects.count())
        
class ContainerFormTest(DjangoTestCase):
    """ Tests for ContainerForm class """
    
    def setUp(self):
        super(ContainerFormTest, self).setUp()
        self.set_up_default_container() # empty
        
    def test_invalid_kind(self):
        instance = self.container
        form = ContainerForm(data={'project': str(self.project.pk), 'label': 'label', 'kind' : 'invalid_kind'}, instance=instance)
        self.assertFalse(form.is_valid())
        self.assertEqual({'kind': ['Select a valid choice. invalid_kind is not one of the available choices.']}, form.errors)
        
    def test_no_crystals(self):
        instance = self.container
        form = ContainerForm(data={'project': str(self.project.pk), 'label': 'label', 'kind' : str(instance.kind + 1)}, instance=instance)
        self.assertTrue(form.is_valid())
        self.assertEqual({}, form.errors)
        
    def test_no_crystals_same_kind(self):
        instance = self.container
        form = ContainerForm(data={'project': str(self.project.pk), 'label': 'label', 'kind' : str(instance.kind)}, instance=instance)
        self.assertTrue(form.is_valid())
        self.assertEqual({}, form.errors)
        
    def test_crystals(self):
        instance = self.container
        create_Crystal(project=self.project, container=self.container)
        form = ContainerForm(data={'project': str(self.project.pk), 'label': 'label', 'kind' : str(instance.kind + 1)}, instance=instance)
        self.assertFalse(form.is_valid())
        self.assertEqual({'kind': [u'Cannot change kind of Container when Crystals are associated']}, form.errors)
        
    def test_crystals_same_kind(self):
        instance = self.container
        form = ContainerForm(data={'project': str(self.project.pk), 'label': 'label', 'kind' : str(instance.kind)}, instance=instance)
        self.assertTrue(form.is_valid())
        self.assertEqual({}, form.errors)
        
class SampleSelectFormTest(DjangoTestCase):
    
    def setUp(self):
        super(SampleSelectFormTest, self).setUp()
        self.set_up_default_container() # empty
        self.crystal1 = create_Crystal(project=self.project, name='crystal1')
        self.crystal2 = create_Crystal(project=self.project, name='crystal2')
        
    def test_no_parent(self):
        self.assertRaises(Container.DoesNotExist, SampleSelectForm)
        
    def test_no_data(self):
        form = SampleSelectForm(initial={'parent': self.container.pk})
        self.assertFalse(form.is_bound)
        self.assertFalse(form.is_valid())
        self.assertEqual({}, form.errors)
        self.assertEqual([('A1', 'A1'), ('A2', 'A2'), ('A3', 'A3'), ('A4', 'A4'), ('A5', 'A5'), ('A6', 'A6'), ('A7', 'A7'), ('A8', 'A8'), 
                          ('B1', 'B1'), ('B2', 'B2'), ('B3', 'B3'), ('B4', 'B4'), ('B5', 'B5'), ('B6', 'B6'), ('B7', 'B7'), ('B8', 'B8'), 
                          ('C1', 'C1'), ('C2', 'C2'), ('C3', 'C3'), ('C4', 'C4'), ('C5', 'C5'), ('C6', 'C6'), ('C7', 'C7'), ('C8', 'C8'), 
                          ('D1', 'D1'), ('D2', 'D2'), ('D3', 'D3'), ('D4', 'D4'), ('D5', 'D5'), ('D6', 'D6'), ('D7', 'D7'), ('D8', 'D8'), 
                          ('E1', 'E1'), ('E2', 'E2'), ('E3', 'E3'), ('E4', 'E4'), ('E5', 'E5'), ('E6', 'E6'), ('E7', 'E7'), ('E8', 'E8'), 
                          ('F1', 'F1'), ('F2', 'F2'), ('F3', 'F3'), ('F4', 'F4'), ('F5', 'F5'), ('F6', 'F6'), ('F7', 'F7'), ('F8', 'F8'), 
                          ('G1', 'G1'), ('G2', 'G2'), ('G3', 'G3'), ('G4', 'G4'), ('G5', 'G5'), ('G6', 'G6'), ('G7', 'G7'), ('G8', 'G8'), 
                          ('H1', 'H1'), ('H2', 'H2'), ('H3', 'H3'), ('H4', 'H4'), ('H5', 'H5'), ('H6', 'H6'), ('H7', 'H7'), ('H8', 'H8'), 
                          ('I1', 'I1'), ('I2', 'I2'), ('I3', 'I3'), ('I4', 'I4'), ('I5', 'I5'), ('I6', 'I6'), ('I7', 'I7'), ('I8', 'I8'), 
                          ('J1', 'J1'), ('J2', 'J2'), ('J3', 'J3'), ('J4', 'J4'), ('J5', 'J5'), ('J6', 'J6'), ('J7', 'J7'), ('J8', 'J8'), 
                          ('K1', 'K1'), ('K2', 'K2'), ('K3', 'K3'), ('K4', 'K4'), ('K5', 'K5'), ('K6', 'K6'), ('K7', 'K7'), ('K8', 'K8'), 
                          ('L1', 'L1'), ('L2', 'L2'), ('L3', 'L3'), ('L4', 'L4'), ('L5', 'L5'), ('L6', 'L6'), ('L7', 'L7'), ('L8', 'L8')], 
                         form.fields['container_location'].choices)
        
    def test_invalid(self):
        form = SampleSelectForm({'parent': self.container.pk})
        self.assertTrue(form.is_bound)
        self.assertFalse(form.is_valid())
        self.assertEqual({'items': ['This field is required.'], 'container_location': ['This field is required.']}, form.errors)
        
    def test_valid(self):
        form = SampleSelectForm({'parent': self.container.pk, 'items': self.crystal1.pk, 'container_location': 'A1'})
        form.fields['items'].queryset = Crystal.objects.all()
        self.assertTrue(form.is_bound)
        self.assertTrue(form.is_valid())
        self.assertEqual({}, form.errors)
        
    def test_port_already_assigned(self):
        self.crystal2.container = self.container
        self.crystal2.container_location = 'A1'
        self.crystal2.save()
        form = SampleSelectForm({'parent': self.container.pk, 'items': self.crystal1.pk, 'container_location': 'A1'})
        form.fields['items'].queryset = Crystal.objects.all()
        self.assertTrue(form.is_bound)
        self.assertFalse(form.is_valid())
        self.assertEqual({'container_location': ['Select a valid choice. A1 is not one of the available choices.']}, form.errors)
        
class ExperimentFromStrategyFormTest(DjangoTestCase):
    """ Test for ExperimentFromStrategyForm class """

    def setUp(self):
        super(ExperimentFromStrategyFormTest, self).setUp()
        self.set_up_default_strategy()
        self.set_up_default_result()

    def test_validation(self):
        form = ExperimentFromStrategyForm()
        self.assertFalse(form.is_bound)
        self.assertFalse(form.is_valid())
        self.assertEqual({}, form.errors)

        form = ExperimentFromStrategyForm({})
        self.assertTrue(form.is_bound)
        self.assertFalse(form.is_valid())
        self.assertEqual({'project': ['This field is required.'],
                          'strategy': ['This field is required.'],
                          'name': ['This field is required.'],
                          'kind': ['This field is required.'],
                          'plan': ['This field is required.'],
                          'crystals': ['This field is required.']
                         },form.errors)

    def test_required_fields_provided(self):
        form = ExperimentFromStrategyForm(
                {'project': self.strategy.project.pk, 'strategy': self.strategy.pk, \
                 'name': 'Resubmitted'+self.strategy.name+'_'+self.strategy.result.crystal.name, \
                 'kind': Experiment.EXP_TYPES.NATIVE, 'plan': Experiment.EXP_PLANS.JUST_COLLECT, \
                 'crystals': self.strategy.result.crystal.pk})
        self.assertTrue(form.is_bound)
        self.assertTrue(form.is_valid())
        self.assertEqual({}, form.errors)

    def test_form_with_valid_crystals_have_expected_queryset(self):
        form = ExperimentFromStrategyForm(
                {'project': self.strategy.project.pk, 'strategy': self.strategy.pk, \
                 'name': 'Resubmitted'+self.strategy.name+'_'+self.strategy.result.crystal.name, \
                 'kind': Experiment.EXP_TYPES.NATIVE, 'plan': Experiment.EXP_PLANS.JUST_COLLECT, \
                 'crystals': self.strategy.result.crystal.pk})

        self.assertEqual(self.strategy.result.crystal, form.fields['crystals'].queryset.all()[0])
        # There should only be one cystal in queryset list since it's populated from strategy.result.crystal
        # (which is only one crystal)
        self.assertEqual(1, len(form.fields['crystals'].queryset.all()))

    def test_form_with_valid_crystals_have_expected_choices(self):
        form = ExperimentFromStrategyForm(
                {'project': self.strategy.project.pk, 'strategy': self.strategy.pk, \
                 'name': 'Resubmitted'+self.strategy.name+'_'+self.strategy.result.crystal.name, \
                 'kind': Experiment.EXP_TYPES.NATIVE, 'plan': Experiment.EXP_PLANS.JUST_COLLECT, \
                 'crystals': self.strategy.result.crystal.pk})
        import datetime
        today = datetime.date.today()
        self.assertEqual([(1, u'crystal123 / XT001.%02d.%02d.%02d' % (today.year-2000, today.month, today.day))], 
                         form.fields['crystals'].choices)
        # There should only be one cystal in choices list since it's populated from strategy.result.crystal
        # (which is only one crystal)
        self.assertEqual(1, len(form.fields['crystals'].choices))

    def test_plan_is_just_collect(self):
        form = ExperimentFromStrategyForm(
                {'project': self.strategy.project.pk, 'strategy': self.strategy.pk, \
                 'name': 'Resubmitted'+self.strategy.name+'_'+self.strategy.result.crystal.name, \
                 'kind': Experiment.EXP_TYPES.NATIVE, 'plan': Experiment.EXP_PLANS.JUST_COLLECT, \
                 'crystals': self.strategy.result.crystal.pk})

        self.assertEqual([(4, u'Just collect')], form.fields['plan'].choices)

    def test_no_crystals(self):
        form = ExperimentFromStrategyForm(
                {'project': self.strategy.project.pk, 'strategy': self.strategy.pk, \
                 'name': 'Resubmitted'+self.strategy.name+'_'+self.strategy.result.crystal.name, \
                 'kind': Experiment.EXP_TYPES.NATIVE, 'plan': Experiment.EXP_PLANS.JUST_COLLECT })
        self.assertTrue(form.is_bound)
        self.assertFalse(form.is_valid())
        self.assertEqual({'crystals': [u'This field is required.']}, form.errors)

    def test_crystals_invalid(self):
        form = ExperimentFromStrategyForm(
                {'project': self.strategy.project.pk, 'strategy': self.strategy.pk, \
                 'name': 'Resubmitted'+self.strategy.name+'_'+self.strategy.result.crystal.name, \
                 'kind': Experiment.EXP_TYPES.NATIVE, 'plan': Experiment.EXP_PLANS.JUST_COLLECT, \
                 'crystals': 0})
        self.assertTrue(form.is_bound)
        self.assertFalse(form.is_valid())
        self.assertEqual({'crystals': [u'Select a valid choice. That choice is not one of the available choices.']}, \
                          form.errors)

    def test_crystals_are_None(self):
        form = ExperimentFromStrategyForm(
                {'project': self.strategy.project.pk, 'strategy': self.strategy.pk, \
                 'name': 'Resubmitted'+self.strategy.name+'_'+self.strategy.result.crystal.name, \
                 'kind': Experiment.EXP_TYPES.NATIVE, 'plan': Experiment.EXP_PLANS.JUST_COLLECT, \
                 'crystals': None})
        self.assertTrue(form.is_bound)
        self.assertFalse(form.is_valid())
        self.assertEqual({'crystals': [u'This field is required.']}, form.errors)