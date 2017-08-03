import os
import re
import sys
from django.utils import dateformat, timezone

import xlrd
import xlutils.copy
import xlutils.save
import xlwt
from ..models import *

COLUMN_MAP = dict([(index, 'ABCDEFGHIJKLMNOPQRSTUVWXYZ'[index]) for index in range(26)])

EXPERIMENT_SHEET_NUM = 1
EXPERIMENT_SHEET_NAME = 'Groups'
EXPERIMENT_NAME = 0
EXPERIMENT_NAME_ERROR = 'Invalid Group/Experiment name "%s" in cell Groups!$' + COLUMN_MAP[EXPERIMENT_NAME] + '$%d.'
EXPERIMENT_KIND = 1
EXPERIMENT_KIND_ERROR = 'Invalid Group/Experiment type "%s" in cell Groups!$' + COLUMN_MAP[EXPERIMENT_KIND] + '$%d.'
EXPERIMENT_PLAN = 2
EXPERIMENT_PLAN_ERROR = 'Invalid Group/Experiment plan "%s" in cell Groups!$' + COLUMN_MAP[EXPERIMENT_PLAN] + '$%d.'
EXPERIMENT_PRIORITY = 3
EXPERIMENT_PRIORITY_ERROR = 'Invalid Priority "%s" in cell Groups!$' + COLUMN_MAP[EXPERIMENT_PRIORITY] + '$%d.'
EXPERIMENT_ABSORPTION_EDGE = 4
EXPERIMENT_ABSORPTION_EDGE_ERROR = 'Invalid Group/Experiment absorption-edge "%s" in cell Groups!$' + COLUMN_MAP[EXPERIMENT_ABSORPTION_EDGE] + '$%d.'
EXPERIMENT_ENERGY = 5
EXPERIMENT_TOTAL_ANGLE = 6
EXPERIMENT_DELTA_ANGLE = 7
EXPERIMENT_R_MEAS = 8
EXPERIMENT_R_MEAS_ERROR = 'Invalid Group/Experiment R-factor "%s" in cell Groups!$' + COLUMN_MAP[EXPERIMENT_R_MEAS] + '$%d.'
EXPERIMENT_I_SIGMA = 9
EXPERIMENT_I_SIGMA_ERROR = 'Invalid Group/Experiment I/Sigma "%s" in cell Groups!$' + COLUMN_MAP[EXPERIMENT_I_SIGMA] + '$%d.'
EXPERIMENT_RESOLUTION = 10
EXPERIMENT_RESOLUTION_ERROR = 'Invalid Group/Experiment resolution "%s" in cell Groups!$' + COLUMN_MAP[EXPERIMENT_RESOLUTION] + '$%d.'
EXPERIMENT_SPACE_GROUP = 11
EXPERIMENT_SPACE_GROUP_ERROR = 'Invalid Group/Experiment space-group "%s" in cell Groups!$' + COLUMN_MAP[EXPERIMENT_RESOLUTION] + '$%d.'
EXPERIMENT_DUPLICATE_ERROR = 'Multiple groups named "%s"'
EXPERIMENT_CELL_A = 12
EXPERIMENT_CELL_B = 13
EXPERIMENT_CELL_C = 14
EXPERIMENT_CELL_ALPHA = 15
EXPERIMENT_CELL_BETA = 16
EXPERIMENT_CELL_GAMMA = 17
EXPERIMENT_COMMENTS = 18
EXPERIMENT_COMMENTS_ERROR = 'Strange character found in cell Groups!$' + COLUMN_MAP[EXPERIMENT_COMMENTS] + '$%d.'

CRYSTAL_SHEET_NUM = 0
CRYSTAL_SHEET_NAME = 'Crystals'
CRYSTAL_NAME = 0
CRYSTAL_NAME_ERROR = 'Invalid Crystal name "%s" in cell Crystals!$' + COLUMN_MAP[CRYSTAL_NAME] + '$%d.'
CRYSTAL_NAME_CHAR_ERROR = 'Strange character found in Crystal name in cell Crystals!$' + COLUMN_MAP[CRYSTAL_NAME] + '$%d.'
CRYSTAL_BARCODE = 1
CRYSTAL_BARCODE_ERROR = 'Invalid Crystal barcode "%s" in cell Crystals!$' + COLUMN_MAP[CRYSTAL_BARCODE] + '$%d.'
CRYSTAL_EXPERIMENT = 2
CRYSTAL_EXPERIMENT_ERROR = 'Invalid Crystal group "%s" in cell Crystals!$' + COLUMN_MAP[CRYSTAL_EXPERIMENT] + '$%d.'
CRYSTAL_CONTAINER = 3
CRYSTAL_CONTAINER_ERROR = 'Invalid Container name "%s" in cell Crystals!$' + COLUMN_MAP[CRYSTAL_CONTAINER] + '$%d.'
CRYSTAL_CONTAINER_KIND = 4
CRYSTAL_CONTAINER_KIND_ERROR = 'Invalid Container kind "%s" in cell Crystals!$' + COLUMN_MAP[CRYSTAL_CONTAINER_KIND] + '$%d.'
CRYSTAL_CONTAINER_LOCATION = 5
CRYSTAL_CONTAINER_LOCATION_ERROR = 'Invalid Container location "%s" in cell Crystals!$' + COLUMN_MAP[CRYSTAL_CONTAINER_LOCATION] + '$%d.'
CRYSTAL_DUPLICATE_ERROR = 'Multiple crystals named "%s"'
CRYSTAL_PRIORITY = 6
CRYSTAL_PRIORITY_ERROR = 'Invalid Priority "%s" in cell Crystals!$' + COLUMN_MAP[CRYSTAL_PRIORITY] + '$%d.'
CRYSTAL_COCKTAIL = 7
CRYSTAL_COCKTAIL_ERROR = 'Strange character found in cocktail at cell Crystals!$' + COLUMN_MAP[CRYSTAL_COCKTAIL] + '$%d.'
CRYSTAL_COMMENTS = 8
CRYSTAL_COMMENTS_ERROR = 'Strange character found in cell Crystals!$' + COLUMN_MAP[CRYSTAL_COMMENTS] + '$%d.'

CONTAINER_TYPES = {
        'Cassette': 0,
        'Uni-Puck': 1,
        'Cane': 2,
        'Basket': 3,
        'UniPuck': 1
}
PLAN_SHEET_NUM = 2
PLAN_SHEET_NAME = 'Plans'

class LimsWorkbook(object):
    """ A wrapper for an Excel shipment/experiment spreadsheet """

    def __init__(self, xls, project, dewar_name, shipment_name, archive=False):
        """ Reads the xls file into a xlrd.Book wrapper 
        
        @param xls: the filename of an Excel file
        @param project: a Project instance  
        """
        self.xls = xls
        self.project = project
        self.dewar_name = dewar_name
        self.shipment_name = shipment_name
        self.errors = []
        self.archive = archive

        
    def _read_xls(self):
        """ Reads the data from the xlrd.Book wrapper """
        if hasattr(self, 'book'):
            return
        
        try:
            self.book = xlrd.open_workbook(self.xls)
        except xlrd.XLRDError:
            self.errors.append('Invalid Excel spreadsheet. Review documentation "Specifying Sample Information".')
            raise xlrd.XLRDError
        
        self.experiments_sheet = self.book.sheet_by_name(EXPERIMENT_SHEET_NAME)
        self.crystals_sheet = self.book.sheet_by_name(CRYSTAL_SHEET_NAME)
        
        self.shipment = self._get_shipment()
        self.dewar = self._get_dewar()
        self.experiments = self._get_experiments()
        self.containers = self._get_containers()
        self.space_groups = self._get_space_groups()
        self.cocktails = self._get_cocktails()
        self.crystal_forms = self._get_crystal_forms()
        self.crystals = self._get_crystals()
        
    def _get_shipment(self):
        """ Returns a Shipment
        
        @return: a Shipment instance
        """
        name = self.shipment_name
        staff_comments = "Uploaded on %s." % (dateformat.format(timezone.now(), 'M, jS P'))
        return Shipment(project=self.project, name=name, staff_comments=staff_comments)
    
    def _get_dewar(self):
        """ Returns a Dewar
        
        @return: a Dewar instance
        """
        name = self.dewar_name
        return Dewar(project=self.project, name=name)
    
    def _get_containers(self):
        """ Returns a dict of {'name' : Container} from the Excel file 
        
        @return: dict of {'name' : Container}
        """
        containers = {}
        for row_num in range(1, self.crystals_sheet.nrows):
            row_values = self.crystals_sheet.row_values(row_num)
            if row_values[CRYSTAL_CONTAINER]:
                if row_values[CRYSTAL_CONTAINER] not in containers:
                    container = Container()
                    container.project = self.project
                    
                    if row_values[CRYSTAL_CONTAINER]:
                        container.name = str(row_values[CRYSTAL_CONTAINER])
                    else:
                        self.errors.append(CRYSTAL_CONTAINER_ERROR % (row_values[CRYSTAL_CONTAINER], row_num+1))
                    
                    if row_values[CRYSTAL_CONTAINER_KIND]:
                        #container.kind = Container.TYPE.get_value_by_name(str(row_values[CRYSTAL_CONTAINER_KIND]).title()) # validated by Excel
                        container.kind = CONTAINER_TYPES.get(str(row_values[CRYSTAL_CONTAINER_KIND]), 2) # default to cane
                    else:
                        self.errors.append(CRYSTAL_CONTAINER_KIND_ERROR % (row_values[CRYSTAL_CONTAINER_KIND], row_num+1))

                        
                    containers[container.name] = container
                    
                # a bit more validation to ensure that the Container 'kind' does not change
                else:
                    container = containers[row_values[CRYSTAL_CONTAINER]]
                    
                    if row_values[CRYSTAL_CONTAINER_KIND]:
                        #kind = Container.TYPE.get_value_by_name(str(row_values[CRYSTAL_CONTAINER_KIND]).title()) # validated by Excel
                        kind = CONTAINER_TYPES.get(str(row_values[CRYSTAL_CONTAINER_KIND]), 2)
                        if kind != container.kind:
                            self.errors.append(CRYSTAL_CONTAINER_KIND_ERROR % (row_values[CRYSTAL_CONTAINER_KIND], row_num+1))
                    else:
                        self.errors.append(CRYSTAL_CONTAINER_KIND_ERROR % (row_values[CRYSTAL_CONTAINER_KIND], row_num+1))
        return containers
    
    def _get_cocktails(self):
        """ Returns a dict of {'name' : Cocktail} from the Excel file 
        
        @return: dict of {'name' : Cocktail}
        """
        cocktails = {}
        for row_num in range(1, self.crystals_sheet.nrows):
            row_values = self.crystals_sheet.row_values(row_num)
            if row_values[CRYSTAL_COCKTAIL]:
                if row_values[CRYSTAL_COCKTAIL] not in cocktails:
                    if self.project.cocktail_set.filter(name__exact=row_values[CRYSTAL_COCKTAIL]).exists():
                        cocktail = self.project.cocktail_set.filter(name__exact=row_values[CRYSTAL_COCKTAIL])[0] 
                    else:
                        cocktail = Cocktail()
                        cocktail.project = self.project
                        if row_values[CRYSTAL_COCKTAIL]:
                            cocktail.name = str(row_values[CRYSTAL_COCKTAIL])
                    cocktails[cocktail.name] = cocktail

        return cocktails
    
    def _get_space_groups(self):
        """ Returns a dict of {'experiment_name' : SpaceGroup} from the Excel file 
        
        @return: dict of {'experiment_name' : SpaceGroup}
        """
        space_groups = {}
        for row_num in range(1, self.experiments_sheet.nrows):
            row_values = self.experiments_sheet.row_values(row_num)
            if row_values[EXPERIMENT_SPACE_GROUP]:
                try:
                    space_group = SpaceGroup.objects.get(name=row_values[EXPERIMENT_SPACE_GROUP])
                    space_groups[row_values[EXPERIMENT_NAME]] = space_group
                except SpaceGroup.DoesNotExist:
                    self.errors.append(EXPERIMENT_SPACE_GROUP_ERROR % (row_values[EXPERIMENT_SPACE_GROUP], row_num+1))
        return space_groups
    
    def _get_crystal_forms(self):
        """ Returns a dict of {'name' : CrystalForm} from the Excel file 
        
        @return: dict of {'name' : CrystalForm}
        """
        crystal_forms = {}
        for row_num in range(1, self.experiments_sheet.nrows):
            row_values = self.experiments_sheet.row_values(row_num)
            if row_values[EXPERIMENT_CELL_A] or \
               row_values[EXPERIMENT_CELL_B] or \
               row_values[EXPERIMENT_CELL_C] or \
               row_values[EXPERIMENT_CELL_ALPHA] or \
               row_values[EXPERIMENT_CELL_BETA] or \
               row_values[EXPERIMENT_CELL_GAMMA] or \
               row_values[EXPERIMENT_SPACE_GROUP]:

                old_cf = self.project.crystalform_set.all()
                if row_values[EXPERIMENT_CELL_A]: old_cf = old_cf.filter(cell_a__exact=row_values[EXPERIMENT_CELL_A])
                if row_values[EXPERIMENT_CELL_B]: old_cf = old_cf.filter(cell_b=float(row_values[EXPERIMENT_CELL_B]))
                if row_values[EXPERIMENT_CELL_C]: old_cf = old_cf.filter(cell_c=float(row_values[EXPERIMENT_CELL_C]))
                if row_values[EXPERIMENT_CELL_ALPHA]: old_cf = old_cf.filter(cell_alpha=float(row_values[EXPERIMENT_CELL_ALPHA]))
                if row_values[EXPERIMENT_CELL_BETA]: old_cf = old_cf.filter(cell_beta=float(row_values[EXPERIMENT_CELL_BETA]))
                if row_values[EXPERIMENT_CELL_GAMMA]: old_cf = old_cf.filter(cell_gamma=float(row_values[EXPERIMENT_CELL_GAMMA]))
                if row_values[EXPERIMENT_SPACE_GROUP]: old_cf = old_cf.filter(space_group__in=SpaceGroup.objects.filter(name=row_values[EXPERIMENT_SPACE_GROUP]))
                if old_cf.exists():
                    crystal_form = old_cf[0]
                else:
                    crystal_form = CrystalForm(project=self.project)
                    
                    try:
                        crystal_form.cell_a = float(row_values[EXPERIMENT_CELL_A])
                    except ValueError:
                        pass
                        
                    try:
                        crystal_form.cell_b = float(row_values[EXPERIMENT_CELL_B])
                    except ValueError:
                        pass
                        
                    try:
                        crystal_form.cell_c = float(row_values[EXPERIMENT_CELL_C])
                    except ValueError:
                        pass
                        
                    try:
                        crystal_form.cell_alpha = float(row_values[EXPERIMENT_CELL_ALPHA])
                    except ValueError:
                        pass
                        
                    try:
                        crystal_form.cell_beta = float(row_values[EXPERIMENT_CELL_BETA])
                    except ValueError:
                        pass
                        
                    try:
                        crystal_form.cell_gamma = float(row_values[EXPERIMENT_CELL_GAMMA])
                    except ValueError:
                        pass

                    if self.space_groups.has_key(row_values[EXPERIMENT_NAME]):
                        space_group = self.space_groups[row_values[EXPERIMENT_NAME]]
                        crystal_form.space_group = space_group
                        crystal_form.save()                    

                crystal_forms[row_values[EXPERIMENT_NAME]] = crystal_form
        return crystal_forms
    
    def _get_experiments(self):
        """ Returns a dict of {'name' : Experiment} from the Excel file 
        
        @return: dict of {'name' : Experiment}
        """
        experiments = {}
        for row_num in range(1, self.experiments_sheet.nrows):
            row_values = self.experiments_sheet.row_values(row_num)
            experiment = Group()
            experiment.project = self.project
            if row_values[EXPERIMENT_NAME]:
                experiment.name = str(row_values[EXPERIMENT_NAME])
            else:
                self.errors.append(EXPERIMENT_NAME_ERROR % (row_values[EXPERIMENT_NAME], row_num+1))
                
            if row_values[EXPERIMENT_KIND]:
                try:
                    experiment.kind = Group.EXP_TYPES.get_value_by_name(len(row_values[EXPERIMENT_KIND]) > 3 and row_values[EXPERIMENT_KIND].capitalize() or row_values[EXPERIMENT_KIND]) # validated by Excel
                except:
                    self.errors.append(EXPERIMENT_KIND_ERROR % (row_values[EXPERIMENT_KIND], row_num+1))
            else:
                # default to Native
                experiment.kind = Group.EXP_TYPES.NATIVE
             
            if row_values[EXPERIMENT_PLAN]:
                try:
                    experiment.plan = Group.EXP_PLANS.get_value_by_name(row_values[EXPERIMENT_PLAN].capitalize()) # validated by Excel
                except:
                    self.errors.append(EXPERIMENT_PLAN_ERROR % (row_values[EXPERIMENT_PLAN], row_num+1))
            else:
                # no experiment plan provided default to just collect
                experiment.plan = Group.EXP_PLANS.SCREEN_AND_COLLECT
                
            if row_values[EXPERIMENT_ABSORPTION_EDGE]:
                experiment.absorption_edge = row_values[EXPERIMENT_ABSORPTION_EDGE]
                
            if row_values[EXPERIMENT_ENERGY]:
                # cast to str which will eventually get cast to decimal.Decimal
                experiment.energy = str(row_values[EXPERIMENT_ENERGY])
                
            if row_values[EXPERIMENT_TOTAL_ANGLE]:
                experiment.total_angle = row_values[EXPERIMENT_TOTAL_ANGLE]
                
            if row_values[EXPERIMENT_DELTA_ANGLE]:
                experiment.delta_angle = row_values[EXPERIMENT_DELTA_ANGLE]
                
            if row_values[EXPERIMENT_R_MEAS]:
                experiment.r_meas = row_values[EXPERIMENT_R_MEAS]
                            
            if row_values[EXPERIMENT_I_SIGMA]:
                experiment.i_sigma = row_values[EXPERIMENT_I_SIGMA]
                
            if row_values[EXPERIMENT_PRIORITY]:
                try:
                    experiment.priority = int(row_values[EXPERIMENT_PRIORITY])
                except:
                    self.errors.append(EXPERIMENT_PRIORITY_ERROR % (row_values[EXPERIMENT_PLAN], row_num+1))
            
            if row_values[EXPERIMENT_RESOLUTION]:
                experiment.resolution = row_values[EXPERIMENT_RESOLUTION]
                
            if experiments.has_key(experiment.name):
                self.errors.append(EXPERIMENT_DUPLICATE_ERROR % (experiment.name))
            else:
                experiments[experiment.name] = experiment

            if len(row_values) > EXPERIMENT_COMMENTS and row_values[EXPERIMENT_COMMENTS]:
                try:
                    experiment.comments = str(row_values[EXPERIMENT_COMMENTS])
                except:
                    self.errors.append(EXPERIMENT_COMMENTS_ERROR % (row_num+1))

        for key, experiment in experiments.items():
            appended = False
            for suffix in range(1,100):
                if not experiment.project.experiment_set.filter(name__exact=experiment.name).exclude(status__exact=Group.STATES.ARCHIVED).exists():
                    pass
                else:
                    if appended:
                        experiment.name = experiment.name[:-1] + str(suffix)
                    else:
                        appended = True
                        experiment.name += '_%s' % str(suffix)
        return experiments
    
    def _get_crystals(self):
        """ Returns a dict of {'name' : Crystal} from the Excel file 
        
        @return: dict of {'name' : Crystal}
        """
        crystals = {}
        for row_num in range(1, self.crystals_sheet.nrows):
            row_values = self.crystals_sheet.row_values(row_num)

            if not row_values[CRYSTAL_NAME].strip(): continue
            if not re.match(r'^[a-zA-Z0-9_-]+$', row_values[CRYSTAL_NAME]):
                self.errors.append(CRYSTAL_NAME_ERROR % (row_values[CRYSTAL_NAME], row_num+1))
                continue

            crystal = Sample()
            crystal.project = self.project
            crystal.name = row_values[CRYSTAL_NAME].strip()

            if row_values[CRYSTAL_BARCODE]:
                crystal.barcode = row_values[CRYSTAL_BARCODE]
                
            # changed, as experiment is actually a crystal property now.
            crystal.experiment = None
            if row_values[CRYSTAL_EXPERIMENT] and row_values[CRYSTAL_EXPERIMENT] in self.experiments:
                # patch the reference - it will be put in the Experiment in .save()
                crystal.experiment = self.experiments[row_values[CRYSTAL_EXPERIMENT]]
            else:
                self.errors.append(CRYSTAL_EXPERIMENT_ERROR % (row_values[CRYSTAL_EXPERIMENT], row_num+1))
                
            if row_values[CRYSTAL_CONTAINER] and str(row_values[CRYSTAL_CONTAINER]) in self.containers:
                crystal.container = self.containers[str(row_values[CRYSTAL_CONTAINER])]
            else:
                self.errors.append(CRYSTAL_CONTAINER_ERROR % (str(row_values[CRYSTAL_CONTAINER]), row_num+1))
                
            if row_values[CRYSTAL_CONTAINER_LOCATION]:
                # xlrd is doing some auto-conversion to floats regardless of the Excel field type
                try:
                    crystal.container_location = type(row_values[CRYSTAL_CONTAINER_LOCATION]) is unicode and str(row_values[CRYSTAL_CONTAINER_LOCATION]).upper() or str(int(row_values[CRYSTAL_CONTAINER_LOCATION]))
                except ValueError:
                    crystal.container_location = row_values[CRYSTAL_CONTAINER_LOCATION]
            else:
                self.errors.append(CRYSTAL_CONTAINER_LOCATION_ERROR % (row_values[CRYSTAL_CONTAINER_LOCATION], row_num+1))
                
            # sanity check on container_location
            if crystal.container:
                if not crystal.container.location_is_valid(crystal.container_location):
                    self.errors.append(CRYSTAL_CONTAINER_LOCATION_ERROR % (row_values[CRYSTAL_CONTAINER_LOCATION], row_num+1))
                
            if row_values[CRYSTAL_COCKTAIL] and row_values[CRYSTAL_COCKTAIL] in self.cocktails:
                crystal.cocktail = self.cocktails[row_values[CRYSTAL_COCKTAIL]]

            if row_values[CRYSTAL_COMMENTS]:
                try:
                    crystal.comments = str(row_values[CRYSTAL_COMMENTS])
                except:
                    self.errors.append(CRYSTAL_COMMENTS_ERROR % (row_num+1))                
                
            if row_values[CRYSTAL_PRIORITY]:
                try:
                    crystal.priority = int(row_values[CRYSTAL_PRIORITY])
                except:
                    self.errors.append(CRYSTAL_PRIORITY_ERROR % (row_values[CRYSTAL_PRIORITY], row_num+1))
                
            if crystals.has_key(crystal.name):
                self.errors.append(CRYSTAL_DUPLICATE_ERROR % (crystal.name))
            else:
                crystals[crystal.name] = crystal
        return crystals
    
    def is_valid(self):
        """ Returns True if the spreadsheet has no validation errors, and False otherwise 
        
        @return: True if the spreadsheet has no validation errors, and False otherwise
        """
        try:
            self._read_xls()
        except:
            return False
        
        try:
            xtal_names = []
            cont_locs = {}
            temp_errors = list()
            crystal_doubles = str()
            xtal_doubles_xls = str()
            loc_doubles_xls = str()

            for crystal in self.crystals.values():
                if crystal.name in xtal_names:
                    xtal_doubles_xls += str(crystal.name) + ','
                xtal_names.append(crystal.name)
                if cont_locs.has_key(crystal.container.name):
                    if crystal.container_location in cont_locs[crystal.container.name]:
                        loc_doubles_xls += '%s (%s),' % (str(crystal.container.name), str(crystal.container_location)) 
                    cont_locs[crystal.container.name].append(crystal.container_location)
                else: 
                    cont_locs[crystal.container.name] = [crystal.container_location]
                if self.project.sample_set.exclude(status__exact=Sample.STATES.ARCHIVED).filter(name=crystal).exists():
                    if self.archive:
                        for xtal in self.project.sample_set.filter(status__exact=Sample.STATES.RETURNED).filter(name=crystal):
                            xtal.container.dewar.shipment.archive()
                    if self.project.sample_set.exclude(status__exact=Sample.STATES.ARCHIVED).filter(name=crystal).exists():
                        crystal_doubles += str(crystal) + ', '
                        msg = 'Un-archived c'
                        
                
            if crystal_doubles:
                if len(crystal_doubles.split(',')) > 5:
                    crystal_doubles = ','.join(crystal_doubles.split(',')[:5]) + '...'
                msg = self.archive and 'C' or 'Un-archived c'
                temp_errors.append('%srystals already exist with names: %s.' % (msg,crystal_doubles))

            if xtal_doubles_xls:
                idx = min(5, len(xtal_doubles_xls.split(','))-1)
                xtal_doubles_xls = ','.join(xtal_doubles_xls.split(',')[:idx]) + (len(xtal_doubles_xls.split(',')) > 5 and '...' or '')
                temp_errors.append('Multiple crystals in spreadsheet called %s.' % xtal_doubles_xls)
                
            if loc_doubles_xls:
                idx = min(5, len(loc_doubles_xls.split(','))-1)
                loc_doubles_xls = ','.join(loc_doubles_xls.split(',')[:idx]) + (len(loc_doubles_xls.split(',')) > 5 and '...' or '')
                temp_errors.append('Multiples crystals specified for container positions %s.' % loc_doubles_xls)

            container_doubles = str()
            for container in self.containers.values():
                if self.project.container_set.exclude(status__exact=Container.STATES.ARCHIVED).filter(name__exact=container).exists():
                    if self.archive:
                        for cont in self.project.container_set.filter(status__exact=Container.STATES.RETURNED).filter(name=container):
                            cont.dewar.shipment.archive()
                    if self.project.container_set.exclude(status__exact=Container.STATES.ARCHIVED).filter(name__exact=container).exists():
                        container_doubles += str(container) + ', '
            
            if container_doubles:
                if len(container_doubles.split(',')) > 5:
                    container_doubles = ','.join(container_doubles.split(',')[:5]) + '...'
                msg = self.archive and 'C' or 'Un-archived c'
                temp_errors.append('%sontainers already exist with names: %s.' % (msg, container_doubles))

            for err in temp_errors:
                if err not in self.errors: self.errors.append(err)
        except:
           self.errors.append("Invalid Excel Spreadsheet.  Review documentation about specifying sample information at http://cmcf.lightsource.ca/user-guide/")

        return not bool(self.errors)
    
    def log_activity(self, obj, request):
        """ Creates an ActivityLog entry 
        
        @param obj: the created django.Model instance to log about
        @param request: a django.http.HttpRequest object used for logging ActivityLog entities during upload
        """
        if obj and request:
            ActivityLog.objects.log_activity(
                        request,
                        obj, 
                        ActivityLog.TYPE.CREATE,
                        'uploaded from spreadsheet'
                        )
    
    def save(self, request=None):
        """ Saves all the data to the database 
        
        @param request: a django.http.HttpRequest object used for logging ActivityLog entities during upload
        @return: a (possibly empty) list of strings errors that occured while reading the Excel file
        """
        
        self.shipment.save()
        self.log_activity(self.shipment, request)
        self.dewar.shipment = self.shipment
        self.dewar.save()
        self.log_activity(self.dewar, request)
        for experiment in self.experiments.values():
            experiment.priority = experiment.priority
            experiment.save()
            # manage the CrystalForm/SpaceGroup relationship
            if self.crystal_forms.has_key(experiment.name):
                crystal_form = self.crystal_forms[experiment.name]
                crystal_form.save()
            self.log_activity(experiment, request)
        for container in self.containers.values():
            container.dewar = self.dewar
            container.save()
            self.log_activity(container, request)
        for cocktail in self.cocktails.values():
            cocktail.save()
            self.log_activity(cocktail, request)
        for crystal_form in self.crystal_forms.values():
            crystal_form.save()
            self.log_activity(crystal_form, request)
        for crystal in self.crystals.values():
            crystal.container = crystal.container # force the fk reln
            crystal.cocktail = crystal.cocktail # force the fk reln
            crystal.crystal_form = crystal.crystal_form
            crystal.experiment = crystal.experiment
            crystal.priority = crystal.priority
            crystal.save()
            self.log_activity(crystal, request)
            
            # unneeded. Crystal read just puts it in to experiment now. 
            # needed for order of operations?
                
            # buffer was needed to add crystal to experiment.
            if crystal.experiment:
                for key in self.experiments:
                    if self.experiments[key].name == crystal.experiment.name:
                        experiment_key = key
                # manage the Crystal/CrystalForm relationship
                if self.crystal_forms.has_key(experiment_key):
                    crystal_form = self.crystal_forms[experiment_key]
                    crystal.crystal_form = crystal_form
                    crystal.crystal_form.name = crystal.crystal_form.identity()
                    crystal.crystal_form.save()
                    crystal.save()
        return self.errors
        
class LimsWorkbookExport(object):
    """ A class for generating an Excel workbook from database data """
    
    def __init__(self, experiments, crystals):
        """ Constructor 
        
        @param experiments: a list of Experiment models
        @param crystals: a list of Crystal models  
        """
        self.experiments = experiments
        self.crystals = crystals
        self.errors = []
        
    def _create_xls(self):
        """ Generates a xlwt.Workbook object from the supplied database models """
        if hasattr(self, 'book_rd'):
            return
        
        self.book_rd = xlrd.open_workbook(os.path.join(os.path.dirname(__file__), 'base.xls'))
        self.book_wt = xlutils.copy.copy(self.book_rd)
        
        # re-hide the Plans worksheet
        self.plans_sheet = self.book_wt.get_sheet(PLAN_SHEET_NUM)
        self.plans_sheet.visibility = 1
        self.plans_sheet.protect = 1
        
        test_style = xlwt.easyxf()
        
        # add the experiments
        self.experiments_sheet = self.book_wt.get_sheet(EXPERIMENT_SHEET_NUM)
        row_num = 1
        for experiment in self.experiments:
            row = self.experiments_sheet.row(row_num)
            
            if experiment.name:
                row.write(EXPERIMENT_NAME, experiment.name)
            else:
                self.error
                
            if experiment.kind != None:
                row.write(EXPERIMENT_KIND, Group.EXP_TYPES[experiment.kind])
                
            if experiment.plan != None:
                row.write(EXPERIMENT_PLAN, Group.EXP_PLANS[experiment.plan])
                
            if experiment.priority:
                row.write(EXPERIMENT_PRIORITY, experiment.priority)

            if experiment.absorption_edge:
                row.write(EXPERIMENT_ABSORPTION_EDGE, experiment.absorption_edge)
                
            if experiment.energy:
                row.write(EXPERIMENT_ENERGY, experiment.energy)
                
            if experiment.total_angle:
                row.write(EXPERIMENT_TOTAL_ANGLE, experiment.total_angle)
                
            if experiment.delta_angle:
                row.write(EXPERIMENT_DELTA_ANGLE, experiment.delta_angle)
                
            if experiment.r_meas:
                row.write(EXPERIMENT_R_MEAS, experiment.r_meas)
                
            if experiment.i_sigma:
                row.write(EXPERIMENT_I_SIGMA, experiment.i_sigma)
                
            if experiment.resolution:
                row.write(EXPERIMENT_RESOLUTION, experiment.resolution)
                
            crystal_forms = [crystal.crystal_form for crystal in experiment.sample_set.all()]
            if len(set(crystal_forms)) == 1 and None not in crystal_forms:
                crystal_form = crystal_forms[0]
                
                if crystal_form.cell_a is not None:
                    row.write(EXPERIMENT_CELL_A, crystal_form.cell_a)
                    
                if crystal_form.cell_b is not None:
                    row.write(EXPERIMENT_CELL_B, crystal_form.cell_b)
                    
                if crystal_form.cell_c is not None :
                    row.write(EXPERIMENT_CELL_C, crystal_form.cell_c)
                    
                if crystal_form.cell_alpha is not None:
                    row.write(EXPERIMENT_CELL_ALPHA, crystal_form.cell_alpha)
                    
                if crystal_form.cell_beta is not None:
                    row.write(EXPERIMENT_CELL_BETA, crystal_form.cell_beta)
                    
                if crystal_form.cell_gamma is not None:
                    row.write(EXPERIMENT_CELL_GAMMA, crystal_form.cell_gamma)
                    
                if crystal_form.space_group:
                    row.write(EXPERIMENT_SPACE_GROUP, crystal_form.space_group.name)
                
            row_num += 1
            
        # add the crystals
        self.crystals_sheet = self.book_wt.get_sheet(CRYSTAL_SHEET_NUM)
        row_num = 1
        for crystal in self.crystals:
            row = self.crystals_sheet.row(row_num)
            
            if crystal.name:
                row.write(CRYSTAL_NAME, crystal.name)
                
            if crystal.barcode:
                row.write(CRYSTAL_BARCODE, crystal.barcode)
                
            if crystal.experiment:
                experiment = crystal.experiment
                if experiment.name:
                    row.write(CRYSTAL_EXPERIMENT, experiment.name)
                    
            if crystal.container and crystal.container.name:
                row.write(CRYSTAL_CONTAINER, crystal.container.name)
                
            if crystal.container and crystal.container.kind != None:
                row.write(CRYSTAL_CONTAINER_KIND, Container.TYPE[crystal.container.kind])
                
            if crystal.container_location:
                row.write(CRYSTAL_CONTAINER_LOCATION, crystal.container_location)
                
            if crystal.priority:
                row.write(CRYSTAL_PRIORITY, crystal.priority)

            if crystal.cocktail and crystal.cocktail.name:
                row.write(CRYSTAL_COCKTAIL, crystal.cocktail.name)
                
            if crystal.comments:
                row.write(CRYSTAL_COMMENTS, crystal.comments)
                
            row_num += 1
            
    def is_valid(self):
        """ Returns True if the spreadsheet has no validation errors, and False otherwise 
        
        @return: True if the data has no validation errors, and False otherwise
        """
        self._create_xls()
        return not bool(self.errors)
    
    def save(self, filename):
        """ Saves all the data to the spreadsheet 
        
        @param filename: the filename to save to 
        @return: a (possibly empty) list of strings errors that occured while writing the Excel file
        """
        if self.is_valid():
            self.book_wt.save(filename)
        return self.errors
        
