import xlrd
import xlwt
import xlutils.copy
import xlutils.save
import os
import logging

from imm.lims.models import Experiment
from imm.lims.models import Dewar
from imm.lims.models import Crystal
from imm.lims.models import Shipment
from imm.lims.models import Container
from imm.lims.models import Constituent
from imm.lims.models import Cocktail
from imm.lims.models import ActivityLog
from django.contrib.contenttypes.models import ContentType

EXPERIMENT_SHEET_NUM = 1
EXPERIMENT_SHEET_NAME = 'Groups'
EXPERIMENT_NAME = 0
EXPERIMENT_NAME_ERROR = 'Invalid Experiment name "%s" in cell Groups!$A$%d.'
EXPERIMENT_KIND = 1
EXPERIMENT_KIND_ERROR = 'Invalid Experiment type "%s" in cell Groups!$B$%d.'
EXPERIMENT_PLAN = 2
EXPERIMENT_PLAN_ERROR = 'Invalid Experiment plan "%s" in cell Groups!$C$%d.'
EXPERIMENT_PRIORITY = 3
EXPERIMENT_ABSORPTION_EDGE = 4
EXPERIMENT_R_MEAS = 5
EXPERIMENT_R_MEAS_ERROR = 'Invalid Experiment R-factor "%s" in cell Groups!$F$%d.'
EXPERIMENT_I_SIGMA = 6
EXPERIMENT_I_SIGMA_ERROR = 'Invalid Experiment I/Sigma "%s" in cell Groups!$G$%d.'
EXPERIMENT_RESOLUTION = 7
EXPERIMENT_RESOLUTION_ERROR = 'Invalid Experiment resolution "%s" in cell Groups!$H$%d.'

CRYSTAL_SHEET_NUM = 0
CRYSTAL_SHEET_NAME = 'Crystals'
CRYSTAL_NAME = 0
CRYSTAL_NAME_ERROR = 'Invalid Crystal name "%s" in cell Crystals!$A$%d.'
CRYSTAL_EXPERIMENT = 1
CRYSTAL_EXPERIMENT_ERROR = 'Invalid Group/Experiment name "%s" in cell Crystals!$B$%d.'
CRYSTAL_CONTAINER = 2
CRYSTAL_CONTAINER_ERROR = 'Invalid Container name "%s" in cell Crystals!$C$%d.'
CRYSTAL_CONTAINER_KIND = 3
CRYSTAL_CONTAINER_KIND_ERROR = 'Invalid Container kind "%s" in cell Crystals!$D$%d.'
CRYSTAL_CONTAINER_LOCATION = 4
CRYSTAL_CONTAINER_LOCATION_ERROR = 'Invalid Container location "%s" in cell Crystals!$E$%d.'
CRYSTAL_PRIORITY = 5
CRYSTAL_COCKTAIL = 6
CRYSTAL_COMMENTS = 7

PLAN_SHEET_NUM = 2
PLAN_SHEET_NAME = 'Plans'

class LimsWorkbook(object):
    """ A wrapper for an Excel shipment/experiment spreadsheet """
    
    def __init__(self, xls, project):
        """ Reads the xls file into a xlrd.Book wrapper 
        
        @param xls: the filename of an Excel file
        @param project: a Project instance  
        """
        self.xls = xls
        self.project = project
        self.errors = []
        
    def _read_xls(self):
        """ Reads the data from the xlrd.Book wrapper """
        if hasattr(self, 'book'):
            return
        
        try:
            self.book = xlrd.open_workbook(self.xls)
        except xlrd.XLRDError:
            self.errors.append('Invalid Excel spreadsheet.')
            return
        
        self.experiments_sheet = self.book.sheet_by_name(EXPERIMENT_SHEET_NAME)
        self.crystals_sheet = self.book.sheet_by_name(CRYSTAL_SHEET_NAME)
        
        self.shipment = self._get_shipment()
        self.dewar = self._get_dewar()
        self.experiments = self._get_experiments()
        self.containers = self._get_containers()
        self.constituents = self._get_constituents()
        self.cocktails = self._get_cocktails()
        self.crystals = self._get_crystals()
        
    def _get_shipment(self):
        """ Returns a Shipment
        
        @return: a Shipment instance
        """
        return Shipment(project=self.project, label='Uploaded Shipment')
    
    def _get_dewar(self):
        """ Returns a Dewar
        
        @return: a Dewar instance
        """
        return Dewar(project=self.project, label="Default Dewar")
    
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
                        container.label = row_values[CRYSTAL_CONTAINER]
                    else:
                        self.errors.append(CRYSTAL_CONTAINER_ERROR % (row_values[CRYSTAL_CONTAINER], row_num))
                    
                    if row_values[CRYSTAL_CONTAINER_KIND]:
                        container.kind = Container.TYPE.get_value_by_name(row_values[CRYSTAL_CONTAINER_KIND]) # validated by Excel
                    else:
                        self.errors.append(CRYSTAL_CONTAINER_KIND_ERROR % (row_values[CRYSTAL_CONTAINER_KIND], row_num))
                        
                    containers[container.label] = container
                    
                # a bit more validation to ensure that the Container 'kind' does not change
                else:
                    container = containers[row_values[CRYSTAL_CONTAINER]]
                    
                    if row_values[CRYSTAL_CONTAINER_KIND]:
                        kind = Container.TYPE.get_value_by_name(row_values[CRYSTAL_CONTAINER_KIND]) # validated by Excel
                        if kind != container.kind:
                            self.errors.append(CRYSTAL_CONTAINER_KIND_ERROR % (row_values[CRYSTAL_CONTAINER_KIND], row_num))
                    else:
                        self.errors.append(CRYSTAL_CONTAINER_KIND_ERROR % (row_values[CRYSTAL_CONTAINER_KIND], row_num))
                    
        return containers
    
    def _get_constituents(self):
        """ Returns a dict of {'name' : Constituent} from the Excel file 
        
        @return: dict of {'name' : Constituent}
        """
        constituents = {}
        for row_num in range(1, self.crystals_sheet.nrows):
            row_values = self.crystals_sheet.row_values(row_num)
            if row_values[CRYSTAL_COCKTAIL]:
                names = row_values[CRYSTAL_COCKTAIL].split(Cocktail.NAME_JOIN_STRING)
                normalized_names = [name.strip() for name in names]
                for name in normalized_names:
                    constituent = Constituent()
                    constituent.project = self.project
                    constituent.name = name
                    constituent.acronym = name
                    constituents[name] = constituent
        return constituents
    
    def _get_cocktails(self):
        """ Returns a dict of {'name' : Cocktail} from the Excel file 
        
        @return: dict of {'name' : Cocktail}
        """
        cocktails = {}
        for row_num in range(1, self.crystals_sheet.nrows):
            row_values = self.crystals_sheet.row_values(row_num)
            if row_values[CRYSTAL_COCKTAIL]:
                cocktail = Cocktail()
                cocktail.project = self.project
                names = row_values[CRYSTAL_COCKTAIL].split(Cocktail.NAME_JOIN_STRING)
                normalized_names = sorted([name.strip() for name in names])
                cocktail.tmp_constituents = []
                for name in normalized_names:
                    constituent = self.constituents[name]
                    cocktail.tmp_constituents.append(constituent)
                cocktails[Cocktail.NAME_JOIN_STRING.join(normalized_names)] = cocktail
        return cocktails
    
    def _get_experiments(self):
        """ Returns a dict of {'name' : Experiment} from the Excel file 
        
        @return: dict of {'name' : Experiment}
        """
        experiments = {}
        for row_num in range(1, self.experiments_sheet.nrows):
            row_values = self.experiments_sheet.row_values(row_num)
            experiment = Experiment()
            experiment.project = self.project
            
            if row_values[EXPERIMENT_NAME]:
                experiment.name = row_values[EXPERIMENT_NAME]
            else:
                self.errors.append(EXPERIMENT_NAME_ERROR % (row_values[EXPERIMENT_NAME], row_num))
                
            if row_values[EXPERIMENT_KIND]:
                experiment.kind = Experiment.EXP_TYPES.get_value_by_name(row_values[EXPERIMENT_KIND]) # validated by Excel
            else:
                self.errors.append(EXPERIMENT_KIND_ERROR % (row_values[EXPERIMENT_KIND], row_num))
                
            if row_values[EXPERIMENT_PLAN]:
                experiment.plan = Experiment.EXP_PLANS.get_value_by_name(row_values[EXPERIMENT_PLAN]) # validated by Excel
            else:
                self.errors.append(EXPERIMENT_PLAN_ERROR % (row_values[EXPERIMENT_PLAN], row_num))
                
            if row_values[EXPERIMENT_ABSORPTION_EDGE]:
                experiment.absorption_edge = row_values[EXPERIMENT_ABSORPTION_EDGE]
                
            if row_values[EXPERIMENT_R_MEAS]:
                experiment.r_meas = row_values[EXPERIMENT_R_MEAS]
            else:
                self.errors.append(EXPERIMENT_R_MEAS_ERROR % (row_values[EXPERIMENT_R_MEAS], row_num))
                
            if row_values[EXPERIMENT_I_SIGMA]:
                experiment.i_sigma = row_values[EXPERIMENT_I_SIGMA]
            else:
                self.errors.append(EXPERIMENT_I_SIGMA_ERROR % (row_values[EXPERIMENT_I_SIGMA], row_num))
                
            if row_values[EXPERIMENT_RESOLUTION]:
                experiment.resolution = row_values[EXPERIMENT_RESOLUTION]
            else:
                self.errors.append(EXPERIMENT_RESOLUTION_ERROR % (row_values[EXPERIMENT_RESOLUTION], row_num))
                
            experiments[experiment.name] = experiment
        return experiments
    
    def _get_crystals(self):
        """ Returns a dict of {'name' : Crystal} from the Excel file 
        
        @return: dict of {'name' : Crystal}
        """
        crystals = {}
        for row_num in range(1, self.crystals_sheet.nrows):
            row_values = self.crystals_sheet.row_values(row_num)
            crystal = Crystal()
            crystal.project = self.project
            
            if row_values[CRYSTAL_NAME]:
                crystal.name = row_values[CRYSTAL_NAME]
            else:
                self.errors.append(CRYSTAL_NAME_ERROR % (row_values[CRYSTAL_NAME], row_num))
                
            crystal.tmp_experiment = None
            if row_values[CRYSTAL_EXPERIMENT] and row_values[CRYSTAL_EXPERIMENT] in self.experiments:
                # patch the reference - it will be put in the Experiment in .save()
                crystal.tmp_experiment = self.experiments[row_values[CRYSTAL_EXPERIMENT]]
            else:
                self.errors.append(CRYSTAL_EXPERIMENT_ERROR % (row_values[CRYSTAL_EXPERIMENT], row_num))
                
            if row_values[CRYSTAL_CONTAINER] and row_values[CRYSTAL_CONTAINER] in self.containers:
                crystal.container = self.containers[row_values[CRYSTAL_CONTAINER]]
            else:
                self.errors.append(CRYSTAL_CONTAINER_ERROR % (row_values[CRYSTAL_CONTAINER], row_num))
                
            if row_values[CRYSTAL_CONTAINER_LOCATION]:
                # xlrd is doing some auto-conversion to floats regardless of the Excel field type
                try:
                    crystal.container_location = str(int(row_values[CRYSTAL_CONTAINER_LOCATION]))
                except ValueError:
                    crystal.container_location = row_values[CRYSTAL_CONTAINER_LOCATION]
            else:
                self.errors.append(CRYSTAL_CONTAINER_LOCATION_ERROR % (row_values[CRYSTAL_CONTAINER_LOCATION], row_num))
                
            # sanity check on container_location
            if crystal.container:
                if not crystal.container.location_is_valid(crystal.container_location):
                    self.errors.append(CRYSTAL_CONTAINER_LOCATION_ERROR % (row_values[CRYSTAL_CONTAINER_LOCATION], row_num))
                
            if row_values[CRYSTAL_COCKTAIL]:
                names = row_values[CRYSTAL_COCKTAIL].split(Cocktail.NAME_JOIN_STRING)
                normalized_names = sorted([name.strip() for name in names])
                cocktail = self.cocktails[Cocktail.NAME_JOIN_STRING.join(normalized_names)]
                crystal.cocktail = cocktail
                
            if row_values[CRYSTAL_COMMENTS]:
                crystal.comments = row_values[CRYSTAL_COMMENTS]
                
            crystals[crystal.name] = crystal
        return crystals
    
    def is_valid(self):
        """ Returns True if the spreadsheet has no validation errors, and False otherwise 
        
        @return: True if the spreadsheet has no validation errors, and False otherwise
        """
        self._read_xls()
        return not bool(self.errors)
    
    def log_activity(self, obj, request):
        """ Creates an ActivityLog entry 
        
        @param obj: the created django.Model instance to log about
        @param request: a django.http.HttpRequest object used for logging ActivityLog entities during upload
        """
        if obj and request:
            ActivityLog.objects.log_activity(
                        self.project.pk,
                        request.user.pk, 
                        request.META['REMOTE_ADDR'],
                        ContentType.objects.get_for_model(obj.__class__).id,
                        obj.pk, 
                        str(obj), 
                        ActivityLog.TYPE.CREATE,
                        'The %(name)s "%(obj)s" was uploaded successfully.' % {'name': str(obj.__class__._meta.verbose_name), 'obj': str(obj)}
                        )
    
    def save(self, request=None):
        """ Saves all the data to the database 
        
        @param request: a django.http.HttpRequest object used for logging ActivityLog entities during upload
        @return: a (possibly empty) list of strings errors that occured while reading the Excel file
        """
        if self.is_valid():
            self.shipment.save()
            self.log_activity(self.shipment, request)
            self.dewar.shipment = self.shipment
            self.dewar.save()
            self.dewar.code = '%s-%s-%s' % (self.project.user.username, self.shipment.pk, self.dewar.pk)
            self.dewar.save()
            self.log_activity(self.dewar, request)
            for experiment in self.experiments.values():
                experiment.save()
                self.log_activity(experiment, request)
            for container in self.containers.values():
                container.dewar = self.dewar
                container.save()
                self.log_activity(container, request)
            for constituent in self.constituents.values():
                constituent.save()
                self.log_activity(constituent, request)
            for cocktail in self.cocktails.values():
                cocktail.save()
                self.log_activity(cocktail, request)
                for constituent in cocktail.tmp_constituents:
                    cocktail.constituents.add(constituent)
                    cocktail.save()
            for crystal in self.crystals.values():
                crystal.container = crystal.container # force the fk reln
                crystal.cocktail = crystal.cocktail # force the fk reln
                crystal.save()
                self.log_activity(crystal, request)
                if crystal.tmp_experiment:
                    # update the Experiment<->Crystal mapping
                    crystal.tmp_experiment.crystals.add(crystal)
                    crystal.tmp_experiment.save()
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
                row.write(EXPERIMENT_KIND, Experiment.EXP_TYPES[experiment.kind])
                
            if experiment.plan != None:
                row.write(EXPERIMENT_PLAN, Experiment.EXP_PLANS[experiment.plan])
                
#            if experiment.priority:
#                row.write(EXPERIMENT_PRIORITY, experiment.priority

            if experiment.absorption_edge:
                row.write(EXPERIMENT_ABSORPTION_EDGE, experiment.absorption_edge)
                
            if experiment.r_meas:
                row.write(EXPERIMENT_R_MEAS, experiment.r_meas)
                
            if experiment.i_sigma:
                row.write(EXPERIMENT_I_SIGMA, experiment.i_sigma)
                
            if experiment.resolution:
                row.write(EXPERIMENT_RESOLUTION, experiment.resolution)
                
            row_num += 1
            
        # add the crystals
        self.crystals_sheet = self.book_wt.get_sheet(CRYSTAL_SHEET_NUM)
        row_num = 1
        for crystal in self.crystals:
            row = self.crystals_sheet.row(row_num)
            
            if crystal.name:
                row.write(CRYSTAL_NAME, crystal.name)
                
            if crystal.num_experiments() > 0:
                experiment = crystal.experiment_set.all()[0]
                if experiment.name:
                    row.write(CRYSTAL_EXPERIMENT, experiment.name)
                    
            if crystal.container and crystal.container.label:
                row.write(CRYSTAL_CONTAINER, crystal.container.label)
                
            if crystal.container and crystal.container.kind != None:
                row.write(CRYSTAL_CONTAINER_KIND, Container.TYPE[crystal.container.kind])
                
            if crystal.container_location:
                row.write(CRYSTAL_CONTAINER_LOCATION, crystal.container_location)
                
#            if crystal.priority:
#                row.write(CRYSTAL_PRIORITY, crystal.priority)

            if crystal.cocktail and crystal.cocktail.name():
                row.write(CRYSTAL_COCKTAIL, crystal.cocktail.name())
                
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
        