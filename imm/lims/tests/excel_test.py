import unittest
import os
import tempfile
import random

from imm.lims.excel import LimsWorkbook
from imm.lims.excel import LimsWorkbookExport

from imm.lims.tests.test_utils import DjangoTestCase
from imm.lims.tests.test_utils import TEST_FILES

from imm.lims.tests import test_utils

from imm.lims.models import Experiment
from imm.lims.models import Dewar
from imm.lims.models import Crystal
from imm.lims.models import Constituent
from imm.lims.models import Cocktail
from imm.lims.models import Container
from imm.lims.models import Shipment
from imm.lims.models import SpaceGroup
from imm.lims.models import CrystalForm
from imm.lims.models import connectActivityLog
from imm.lims.models import disconnectActivityLog

class LimsWorkbookTest(DjangoTestCase):
    """ Tests for LimsSpreadsheet """
    def setUp(self):
        super(LimsWorkbookTest, self).setUp()
        self.set_up_default_project()
        self.set_up_default_space_group(name='P2(1)2(1)2(1)')
    
    def test_create(self):
        workbook = LimsWorkbook(os.path.join(TEST_FILES, 'test.xls'), self.project)
        
    def test_errors(self):
        workbook = LimsWorkbook(os.path.join(TEST_FILES, 'errors.xls'), self.project)
        errors = workbook.save()
        self.assertEqual(['Invalid Experiment name "" in cell Groups!$A$1.', 
                          'Invalid Experiment type "" in cell Groups!$B$1.', 
                          'Invalid Experiment plan "" in cell Groups!$C$1.', 
                          'Invalid Experiment R-factor "" in cell Groups!$I$1.', 
                          'Invalid Experiment I/Sigma "" in cell Groups!$J$1.', 
                          'Invalid Experiment resolution "" in cell Groups!$K$1.', 
                          'Invalid Crystal name "" in cell Crystals!$A$1.', 
                          'Invalid Group/Experiment name "" in cell Crystals!$C$1.', 
                          'Invalid Container name "" in cell Crystals!$D$1.', 
                          'Invalid Container location "" in cell Crystals!$F$1.'], errors)
        
    def test_save(self):
        workbook = LimsWorkbook(os.path.join(TEST_FILES, 'test.xls'), self.project)
        errors = workbook.save()
        self.assertEqual([], errors)
        self.assertEqual(1, Shipment.objects.count())
        self.assertEqual(5, Experiment.objects.count())
        self.assertEqual(1, Dewar.objects.count())
        self.assertEqual(8, Crystal.objects.count())
        self.assertEqual(2, Constituent.objects.count())
        self.assertEqual(3, Cocktail.objects.count())
        self.assertEqual(1, SpaceGroup.objects.count())
        self.assertEqual(2, CrystalForm.objects.count())
        self.assertEqual(['Insulin', 'Insulin/Lysozyme', 'Lysozyme'], sorted([c.name() for c in Cocktail.objects.all()]))
        
class LimsWorkbookExportTest(DjangoTestCase):
    
    def setUp(self):
        super(LimsWorkbookExportTest, self).setUp()
        self.set_up_default_experiment()
        
    def test_save(self):
        workbook = LimsWorkbookExport([self.experiment], [self.crystal])
        xls = workbook.save('/tmp/test.xls')
        
class LimsWorkbookRoundTripTest(DjangoTestCase):
    
    def setUp(self):
        super(LimsWorkbookRoundTripTest, self).setUp()
        disconnectActivityLog()
        self.set_up_default_space_group(name="SpaceGroup")
        
    def tearDown(self):
        super(LimsWorkbookRoundTripTest, self).tearDown()
        connectActivityLog()
        
    def _export_import(self, experiments, crystals):
        # write out the data to Excel
        workbook1 = LimsWorkbookExport(experiments, crystals)
        temp = tempfile.mkstemp(dir='/tmp', suffix='.xls')
        temp_name = temp[1]
        errors1 = workbook1.save(temp_name)
        assert not errors1, errors1
        
        # clear the database (keeping self.* in-memory models)
        self._flush_db_tables()
        self.space_group = None
        self.set_up_default_space_group(name="SpaceGroup") # this needs to exist prior to import
        
        # read in the Excel data, creating a new database
        workbook2 = LimsWorkbook(temp_name, self.project)
        errors2 = workbook2.save()
        assert not errors2, errors2
        
    def test_simple(self):
        self.set_up_default_experiment()
        
        self._export_import([self.experiment], [self.crystal])
        
        # make sure that the old matches the new
        shipment = Shipment.objects.get(label="Uploaded Shipment")
        experiment = Experiment.objects.get(name=self.experiment.name)
        dewar = Dewar.objects.get(label="Default Dewar")
        container = Container.objects.get(label=self.container.label)
        crystal = Crystal.objects.get(name=self.crystal.name)
        space_group = SpaceGroup.objects.get(name="SpaceGroup")
        crystal_form = CrystalForm.objects.get(project=self.project)
        
        # experiment
        self.assertEqual(experiment.name, self.experiment.name)
        self.assertEqual(experiment.kind, self.experiment.kind)
        self.assertEqual(experiment.plan, self.experiment.plan)
        self.assertEqual(experiment.absorption_edge, self.experiment.absorption_edge)
        self.assertEqual(experiment.r_meas, self.experiment.r_meas)
        self.assertEqual(experiment.i_sigma, self.experiment.i_sigma)
        self.assertEqual(experiment.resolution, self.experiment.resolution)
        
        # containers
        self.assertEqual(container.label, self.container.label)
        self.assertEqual(container.kind, self.container.kind)
        
        # crystals
        self.assertEqual(crystal.name, self.crystal.name)
        self.assertEqual(crystal.comments, self.crystal.comments)
        self.assertEqual(crystal.code, self.crystal.code)
        self.assertEqual(crystal.crystal_form, crystal_form)
        
        # dewars - NOTE: these are NOT equal; the Dewar gets lost in the export
        self.assertNotEqual(dewar.label, self.dewar.label)
        
        # links
        self.assertEqual([crystal], list(experiment.crystals.all()))
        self.assertEqual(container, crystal.container)
        self.assertEqual(container.dewar, dewar)
        self.assertEqual(shipment, dewar.shipment)
        
        # spacegroup
        self.assertEqual(space_group.name, self.space_group.name)
        
        # crystal form
        self.assertEqual(0.0, crystal_form.cell_a)
        self.assertEqual(1.0, crystal_form.cell_b)
        self.assertEqual(2.0, crystal_form.cell_c)
        self.assertEqual(crystal_form.cell_a, self.crystal_form.cell_a)
        self.assertEqual(crystal_form.cell_b, self.crystal_form.cell_b)
        self.assertEqual(crystal_form.cell_c, self.crystal_form.cell_c)
        self.assertEqual(crystal_form.cell_alpha, self.crystal_form.cell_alpha)
        self.assertEqual(crystal_form.cell_beta, self.crystal_form.cell_beta)
        self.assertEqual(crystal_form.cell_gamma, self.crystal_form.cell_gamma)
        self.assertEqual(crystal_form.space_group, self.crystal_form.space_group)
        
    def test_complex(self):
        self.set_up_default_project()
        
        num_experiments, num_containers, num_crystals = 5, 10, 20
        
        kinds = [c[0] for c in Experiment.EXP_TYPES.get_choices()]
        plans = [c[0] for c in Experiment.EXP_PLANS.get_choices()]
        experiments1 = [test_utils.create_Experiment(project=self.project,
                                                    name='Experiment-%d' % i,
                                                    kind=kinds[i % len(kinds)],
                                                    plan=plans[i % len(plans)]) for i in range(num_experiments)]
        
        kinds = [c[0] for c in Container.TYPE.get_choices()]
        containers1 = [test_utils.create_Container(project=self.project,
                                                  label='Container-%d' % i,
                                                  kind=kinds[i % len(kinds)]) for i in range(num_containers)]
        
        crystals1, assigned_containers = [], set([])
        for i in range(num_crystals):
            crystal = test_utils.create_Crystal(project=self.project,
                                                name='Crystal-%d' % i,
                                                container=random.choice(containers1))
            assigned_containers.add(crystal.container.pk)
            while crystal.container.num_crystals() >= crystal.container.capacity():
                crystal.container = random.choice(containers1)
                crystal.save()
            crystal.container_location = crystal.container.valid_locations()[crystal.container.num_crystals()]
            crystals1.append(crystal)
            
        tmp_crystals = list(crystals1)
        for experiment in experiments1:
            random.shuffle(tmp_crystals)
            crystal_form = None
            if random.randint(0, 100) < 50:
                space_group = None
                if random.randint(0, 100) < 50:
                    space_group = random.choice(SpaceGroup.objects.all())
                crystal_form = CrystalForm(project=self.project, space_group=space_group,
                                           cell_a=1.0, cell_b=1.0, cell_c=1.0,
                                           cell_alpha=1.0, cell_beta=1.0, cell_gamma=1.0)
                crystal_form.save()
            for crystal_index in range(num_crystals/num_experiments):
                crystal = tmp_crystals.pop()
                crystal.crystal_form = crystal_form
                crystal.save()
                experiment.crystals.add(crystal)
            experiment.save()
            
        space_group = list(SpaceGroup.objects.all())
        crystal_form = list(CrystalForm.objects.all())
        
        self._export_import(experiments1, crystals1)
        
        shipment2 = Shipment.objects.get(label="Uploaded Shipment")
        experiments2 = list(Experiment.objects.all())
        containers2 = list(Container.objects.all())
        crystals2 = list(Crystal.objects.all())
        dewar2 = Dewar.objects.get(label="Default Dewar")
        space_group2 = list(SpaceGroup.objects.all())
        crystal_form2 = list(CrystalForm.objects.all())
        
        self.assertEqual(num_experiments, len(experiments1))
        self.assertEqual(num_experiments, len(experiments2))
        self.assertEqual(num_containers, len(containers1))
        self.assertEqual(len(assigned_containers), len(containers2))
        self.assertEqual(num_crystals, len(crystals1))
        self.assertEqual(num_crystals, len(crystals2))
        self.assertEqual(len(space_group), len(space_group2))
        self.assertEqual(len(crystal_form), len(crystal_form2))
        
        # all Containers into the default Dewar
        for container2 in containers2:
            self.assertEqual(dewar2, container2.dewar)
            
        self.assertEqual(shipment2, dewar2.shipment)