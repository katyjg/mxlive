""" Django models tests """
import unittest

from mxlive.users.tests.test_utils import DjangoTestCase
from mxlive.users.tests.test_utils import create_Container
from mxlive.users.tests.test_utils import create_Experiment

from mxlive.users.models import Container

from mxlive.staff.forms import ContainerSelectForm
from mxlive.staff.forms import ExperimentSelectForm

class ExperimentSelectFormTest(DjangoTestCase):
    """ Tests for ExperimentSelectFormTest class """
    
    def setUp(self):
        super(ExperimentSelectFormTest, self).setUp()
        self.set_up_default_project()
        self.experiments = [create_Experiment(project=self.project, name='Experiment-%d' % i) for i in range(5)]

    def test_clean_empty(self):
        form = ExperimentSelectForm({})
        self.assertFalse(form.is_valid())
        self.assertEqual({'experiment': ['Please select an Experiment.']}, form.errors)
        
    def test_clean_valid(self):
        form = ExperimentSelectForm({'experiment': [e.pk for e in self.experiments]})
        self.assertTrue(form.is_valid())
        self.assertEqual({}, form.errors)
        self.assertEqual('', form.primary_error_message())

class ContainerSelectFormTest(DjangoTestCase):
    """ Tests for ContainerSelectFormTest class """
    
    def setUp(self):
        super(ContainerSelectFormTest, self).setUp()
        self.set_up_default_project()
        self.set_up_default_experiment()
        self.cassettes = [create_Container(project=self.project, kind=Container.TYPE.CASSETTE, label='Cassette-%d' % i) for i in range(4)]
        self.pucks = [create_Container(project=self.project, kind=Container.TYPE.UNI_PUCK, label='Puck-%d' % i) for i in range(13)]
        self.baskets = [create_Container(project=self.project, kind=Container.TYPE.BASKET, label='Basket-%d' % i) for i in range(1)]
        
    def test_clean_empty(self):
        form = ContainerSelectForm({})
        self.assertFalse(form.is_valid())
        self.assertEqual({'container': ['Please select a Container.'], 'experiment': ['Please select an Experiment.']}, form.errors)
        
    def test_clean_wrong_type(self):
        
        # invalid container type
        form = ContainerSelectForm({'experiment': [self.experiment.pk], 
                                    'container': [c.pk for c in self.cassettes + self.pucks + self.baskets]})
        self.assertFalse(form.is_valid())
        self.assertEqual({'__all__': ['Container "Basket-0" has an invalid type "Basket".']}, form.errors)
        self.assertEqual('Container "Basket-0" has an invalid type "Basket".', form.primary_error_message())
        
    def test_clean_far_too_many_cassettes(self):
        
        # for too many cassettes
        form = ContainerSelectForm({'experiment': [self.experiment.pk], 
                                    'container': [c.pk for c in self.cassettes]})
        self.assertFalse(form.is_valid())
        self.assertEqual({'__all__': ['Cannot have more than 3 Containers of type "Cassette".']}, form.errors)
        self.assertEqual('Cannot have more than 3 Containers of type "Cassette".', form.primary_error_message())
        
    def test_clean_far_too_many_pucks(self):
        
        # far too many pucks
        form = ContainerSelectForm({'experiment': [self.experiment.pk], 
                                    'container': [c.pk for c in self.pucks]})
        self.assertFalse(form.is_valid())
        self.assertEqual({'__all__': ['Cannot have more than 12 Containers of type "Uni-Puck".']}, form.errors)
        self.assertEqual('Cannot have more than 12 Containers of type "Uni-Puck".', form.primary_error_message())
        
    def test_clean_too_many_pucks(self):
        
        # too many pucks
        form = ContainerSelectForm({'experiment': [self.experiment.pk], 
                                    'container': [c.pk for c in self.cassettes[:1] + self.pucks[:9]]})
        self.assertFalse(form.is_valid())
        self.assertEqual({'__all__': ['Too many Containers of type "Uni-Puck".']}, form.errors)
        self.assertEqual('Too many Containers of type "Uni-Puck".', form.primary_error_message())
        
    def test_clean_valid_cassettes(self):
        
        # OK
        form = ContainerSelectForm({'experiment': [self.experiment.pk], 
                                    'container': [c.pk for c in self.cassettes[:3]]})
        self.assertTrue(form.is_valid())
        self.assertEqual({}, form.errors)
        self.assertEqual('', form.primary_error_message())
        
    def test_clean_valid_pucks(self):
        
        # OK
        form = ContainerSelectForm({'experiment': [self.experiment.pk], 
                                    'container': [c.pk for c in self.pucks[:12]]})
        self.assertTrue(form.is_valid())
        self.assertEqual({}, form.errors)
        self.assertEqual('', form.primary_error_message())
        
    def test_clean_valid_cassettes_and_pucks(self):
        
        # OK
        form = ContainerSelectForm({'experiment': [self.experiment.pk], 
                                    'container': [c.pk for c in self.cassettes[:1] + self.pucks[:8]]})
        self.assertTrue(form.is_valid())
        self.assertEqual({}, form.errors)
        self.assertEqual('', form.primary_error_message())
        
        
        