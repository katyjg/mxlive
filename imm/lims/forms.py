import tempfile
import logging
import re
from django.utils import dateformat
from datetime import datetime

from django import forms
from imm.lims.models import *
import imm.objforms.widgets
import imm.objforms.forms
from imm import objforms
from django.forms.util import ErrorList
from imm.lims.excel import LimsWorkbook, LimsWorkbookExport
            
class ProjectForm(objforms.forms.OrderedForm):
    contact_person = objforms.widgets.LargeCharField(required=True)
    contact_email = forms.EmailField(widget=objforms.widgets.LargeInput, max_length=100, required=True)
    carrier = forms.ModelChoiceField(
        widget=objforms.widgets.LeftHalfSelect,
        queryset=Carrier.objects.all(), 
        required=False)
    account_number = objforms.widgets.RightHalfCharField(required=False)
    organisation = objforms.widgets.LargeCharField(required=True)
    department = objforms.widgets.LargeCharField(required=False)
    address = objforms.widgets.LargeCharField(required=True)
    city = forms.CharField(widget=objforms.widgets.LeftHalfInput, required=True)
    province = forms.CharField(widget=objforms.widgets.RightHalfInput, required=True)
    postal_code = forms.CharField(widget=objforms.widgets.LeftHalfInput, required=True)
    country = forms.CharField(widget=objforms.widgets.RightHalfInput, required=True)
    contact_phone = forms.CharField(widget=objforms.widgets.LeftHalfInput, required=True)
    contact_fax =forms.CharField(widget=objforms.widgets.RightHalfInput, required=False)
    show_archives = objforms.widgets.LeftCheckBoxField(required=False)
    updated = forms.CharField(widget=forms.HiddenInput())

    class Meta:
        model = Project
        fields = ('contact_person','contact_email',
                  'carrier','account_number', 'organisation', 'department','address',
                  'city', 'province','postal_code','country','contact_phone','contact_fax','show_archives','updated')
                  
    def clean_updated(self):
        """
        Toggle updated value to True when the profile is saved for the first time.
        """
        return True

    def restrict_by(self, field_name, id): 
        pass
       
class ShipmentForm(objforms.forms.OrderedForm):
    project = forms.ModelChoiceField(queryset=Project.objects.all(), widget=forms.HiddenInput)
    name = forms.CharField(
        widget=objforms.widgets.LargeInput
        )
    comments = objforms.widgets.CommentField(required=False,
           help_text=Crystal.HELP['comments'])

    class Meta:
        model = Shipment
        fields = ('project','name','comments',)
        
class ConfirmDeleteForm(objforms.forms.OrderedForm):
    project = forms.ModelChoiceField(queryset=Project.objects.all(), widget=forms.HiddenInput)
    cascade = objforms.widgets.LargeCheckBoxField(required=False, label='Keep all child objects associated with this object.')
    class Meta:
        fields = ('project','cascade')

class LimsBasicForm(objforms.forms.OrderedForm):
    project = forms.ModelChoiceField(queryset=Project.objects.all(), widget=forms.HiddenInput)
    class Meta:
        fields = ('project',)
        
class ShipmentUploadForm(forms.Form):
    project = forms.ModelChoiceField(queryset=Project.objects.all(), widget=forms.HiddenInput)
    excel = forms.FileField(widget=objforms.widgets.LargeFileInput)
    dewar = forms.CharField(widget=objforms.widgets.LargeInput, 
            label='Dewar Name', 
            help_text='A dewar with this name will be created for the contents of the uploaded spreadsheet.', 
            required=True)
    shipment = forms.CharField(widget=objforms.widgets.LargeInput, 
            label='Shipment Name', 
            help_text='Provide a name for this shipment.', 
            required=True)    

    NUM_ERRORS = 3    

    def __init__(self, *args, **kwargs):
        super(ShipmentUploadForm, self).__init__(*args, **kwargs)
        self.fields['dewar'].initial = "Dewar %s" % dateformat.format(datetime.now(), 'ymd His')
        self.fields['shipment'].initial = "Shipment %s" % dateformat.format(datetime.now(), 'ymd His')

    def clean(self):
        """ Cleans the form globally. This simply delegates validation to the LimsWorkbook. """
        cleaned_data = self.cleaned_data
        if cleaned_data.has_key('project') and cleaned_data.has_key('excel'):
            temp = tempfile.NamedTemporaryFile()
            temp.write(self.files['excel'].read())
            temp.flush()
            try:
                self.workbook = LimsWorkbook(temp.name, cleaned_data['project'], dewar_name=cleaned_data['dewar'], shipment_name=cleaned_data['shipment'])
            except KeyError:
                del cleaned_data['excel']
                return cleaned_data
            if not self.workbook.is_valid():
                self._errors['excel'] = self._errors.get('excel', ErrorList())
                errors = 'Please check the format of your spreadsheet and try to upload again.'
                del cleaned_data['excel']
            return cleaned_data
    
    def clean_dewar(self):
        if Dewar.objects.filter(project__exact=self.cleaned_data['project'], name__exact=self.cleaned_data['dewar']).exclude(status__exact=Dewar.STATES.ARCHIVED).exists():
            raise forms.ValidationError('An un-archived dewar already exists with this name')
        return self.cleaned_data['dewar']

    def clean_shipment(self):
        if Shipment.objects.filter(project__exact=self.cleaned_data['project'], name__exact=self.cleaned_data['shipment']).exclude(status__exact=Shipment.STATES.ARCHIVED).exists():
            raise forms.ValidationError('An un-archived shipment already exists with this name')
        return self.cleaned_data['shipment']

    def error_message(self):
        errors = ''
        if not self.workbook.is_valid():
            self._errors['excel'] = self._errors.get('excel', ErrorList())
            errors = self.workbook.errors
            #errors = self.workbook.errors[:self.NUM_ERRORS]
            #if len(self.workbook.errors) > len(errors):
            #    errors.append("and %d more errors..." % (len(self.workbook.errors)-len(errors)))
            self._errors['excel'].extend(errors)          
        error_list = list()
        short_errors = list()
        for error in errors:
            try: 
                error.split(' ')[6].split('!')[1][:-1]
                if ' '.join(error.split(' ')[0:3]) not in short_errors:
                    error_list.append(' '.join(error.split(' ')[0:3]) + ' in cell(s) ')
                    short_errors.append(' '.join(error.split(' ')[0:3]))
                for i in range(len(error_list)):
                    if ' '.join(error.split(' ')[0:3]) == ' '.join(error_list[i].split(' ')[0:3]):
                        if len(error_list[i]) < 90:
                            error_list[i] += error.split(' ')[6].split('!')[1][:-1] + ', '
                        elif error_list[i][-3:] != '...':
                            error_list[i] += 'and others ...'   
            except IndexError:
                error_list.append(error)                     
                        
        error_text = list()
        error_text.append('The following problems with the spreadsheet have been identified:')
        for error in error_list:
            error_text.append('- ' + error)
        if len(error_text) > 1:
            return error_text
        return

    def save(self, request=None):
        """ Saves the form which writes the Shipment spreadsheet data to the database """
        assert self.is_valid()
        self.workbook.save(request=request)
        
    def add_excel_error(self, error):
        """ Adds an error message to the 'excel' field """
        self._errors['excel'] = self._errors.get('excel', ErrorList())
        self._errors['excel'].append(error)

class ShipmentSendForm(objforms.forms.OrderedForm):
    project = forms.ModelChoiceField(queryset=Project.objects.all(), widget=forms.HiddenInput)
    carrier = forms.ModelChoiceField(
        queryset=Carrier.objects.all(),
        widget=objforms.widgets.LargeSelect,
        required=True, initial=''
        )
    tracking_code = objforms.widgets.LargeCharField(required=False)
    comments = objforms.widgets.CommentField(required=False)
    
    class Meta:
        model = Shipment
        fields = ('project','carrier', 'tracking_code','comments')
        
    def __init__(self, *args, **kwargs):
        super(ShipmentSendForm, self).__init__(*args, **kwargs)
        for pro in Project.objects.all():
            car = pro.carrier
        try:
            self.fields['carrier'].queryset = Carrier.objects.filter(pk=car.pk) 
        except:
            self.fields['carrier'].queryset = Carrier.objects.all()

    def warning_message(self):
        shipment = self.instance
        if shipment:
            for crystal in shipment.project.crystal_set.filter(container__dewar__shipment__exact=shipment):
                if not crystal.experiment:
                    return 'Crystal "%s" is not associated with any Experiments. Sending the Shipment will create a ' \
                           'default "Screen and confirm" Experiment and assign all unassociated Crystals. Close this window ' \
                           'to setup the Experiment manually.' % crystal.name
                           
    def clean_tracking_code(self):
        cleaned_data = self.cleaned_data['tracking_code']
        # put this here instead of .clean() because objforms does not display form-wide error messages
        if self.instance.status != Shipment.STATES.DRAFT:
            raise forms.ValidationError('Shipment already sent.')
        return cleaned_data

    def restrict_by(self, field_name, id): 
        pass

class DewarForm(objforms.forms.OrderedForm):
    project = forms.ModelChoiceField(queryset=Project.objects.all(), widget=forms.HiddenInput)
    shipment = forms.ModelChoiceField(
        queryset=Shipment.objects.all(), 
        widget=objforms.widgets.LargeSelect,
        required=False
        )
    name =  objforms.widgets.BarCodeField()
    comments = objforms.widgets.CommentField(required=False,
           help_text=Crystal.HELP['comments'])

    class Meta:
        model = Dewar
        fields = ('project','name','shipment','comments',)

class ContainerForm(objforms.forms.OrderedForm):
    project = forms.ModelChoiceField(queryset=Project.objects.all(), widget=forms.HiddenInput)
    dewar = forms.ModelChoiceField(queryset=Dewar.objects.all(), widget=objforms.widgets.LargeSelect, required=False)
    name = objforms.widgets.BarCodeField()
    kind = forms.ChoiceField(choices=Container.TYPE.get_choices(), widget=objforms.widgets.LargeSelect, initial=Container.TYPE.UNI_PUCK)
    comments = objforms.widgets.CommentField(required=False,
           help_text=Crystal.HELP['comments'])
    
    def clean_kind(self):
        """ Ensures that the 'kind' of Container cannot be changed when Crystals are associated with it """
        cleaned_data = self.cleaned_data
        if self.instance.pk:
            if unicode(self.instance.kind) != cleaned_data['kind']:
                if self.instance.num_crystals() > 0:
                    raise forms.ValidationError('Cannot change kind of Container when Crystals are associated')
        return cleaned_data['kind']
    
    class Meta:
        model = Container
        fields = ('project','name','kind','dewar','comments')

class SampleForm(objforms.forms.OrderedForm):
    project = forms.ModelChoiceField(queryset=Project.objects.all(), widget=forms.HiddenInput)
    name = forms.CharField(
        widget=objforms.widgets.LargeInput, help_text=None
        )
    barcode = objforms.widgets.MatrixCodeField(required=False, label='Code')
    cocktail = forms.ModelChoiceField(
        queryset=Cocktail.objects.all(), 
        widget=objforms.widgets.LargeSelect(attrs={'class': 'field select leftHalf'}),
        required=False
        )
    pin_length = forms.IntegerField(widget=objforms.widgets.RightHalfInput, initial=18, label='Pin Length (mm)' )
    crystal_form = forms.ModelChoiceField(
        queryset=CrystalForm.objects.all(), 
        widget=objforms.widgets.LargeSelect(attrs={'class': 'field select leftHalf'}),
        required=False
        )
    loop_size = forms.FloatField( widget=objforms.widgets.RightHalfInput, required=False )
    container = forms.ModelChoiceField(
        queryset=Container.objects.all(), 
        widget=objforms.widgets.LargeSelect(attrs={'class': 'field select leftHalf'}),
        required=False,
        )
    experiment = forms.ModelChoiceField(
        queryset=Experiment.objects.all(), 
        widget=objforms.widgets.LargeSelect(attrs={'class': 'field select rightHalf'}),
        required=False,
        )
    container_location = objforms.widgets.LeftHalfCharField(
        required=False,
        )
    comments = forms.CharField(
        widget=objforms.widgets.CommentInput, 
        max_length=200, 
        required=False,
        )
   
    def clean(self):
        if self.cleaned_data.has_key('name'):
            if not re.compile('^[a-zA-Z0-9-_]+[\w]+$').match(self.cleaned_data['name']):
                self._errors['name'] = self.error_class(['Name cannot contain any spaces or special characters'])
        return self.cleaned_data

    def clean_container_location(self):
        if self.cleaned_data['container'] and not self.cleaned_data['container_location']:
            raise forms.ValidationError('This field is required with container selected')
        elif self.cleaned_data['container_location'] and not self.cleaned_data['container']:
            raise forms.ValidationError('This field must be blank with no container selected')
        elif self.cleaned_data['container_location'] and self.cleaned_data['container']:
            if self.instance:
                pk = self.instance.pk
            else:
                pk = None
            if not self.cleaned_data['container'].location_is_valid( self.cleaned_data['container_location'] ):
                raise forms.ValidationError('Not a valid location for this container (%s)' % self.cleaned_data['container'].TYPE[self.cleaned_data['container'].kind])
            if not self.cleaned_data['container'].location_is_available( self.cleaned_data['container_location'], pk ):
                raise forms.ValidationError('Another sample is already in that position.')
        return self.cleaned_data['container_location']
        
    class Meta:
        model = Crystal
        fields = ('project','name','barcode','cocktail', 'pin_length','crystal_form',
                    'loop_size','container','experiment','container_location','comments')

class ExperimentForm(objforms.forms.OrderedForm):
    project = forms.ModelChoiceField(queryset=Project.objects.all(), widget=forms.HiddenInput)
    name = objforms.widgets.LargeCharField(required=True)
    kind = objforms.widgets.LeftHalfChoiceField(label='Type', choices=Experiment.EXP_TYPES.get_choices(), required=True)
    plan = objforms.widgets.RightHalfChoiceField(label='Plan', choices=Experiment.EXP_PLANS.get_choices(), required=True)
    resolution = forms.FloatField(label='Desired Resolution', widget=objforms.widgets.LeftHalfInput, required=False )
    delta_angle = forms.FloatField(widget=objforms.widgets.RightHalfInput, required=False)
    multiplicity = forms.FloatField(widget=objforms.widgets.LeftHalfInput, required=False)
    total_angle = forms.FloatField(label='Angle Range', widget=objforms.widgets.RightHalfInput, required=False)    
    i_sigma = forms.FloatField(label='Desired I/Sigma',widget=objforms.widgets.LeftHalfInput, required=False )
    r_meas = forms.FloatField(label='Desired R-factor', widget=objforms.widgets.RightHalfInput, required=False )
    energy = forms.DecimalField( max_digits=10, decimal_places=4, widget=objforms.widgets.LeftHalfInput, required=False )
    absorption_edge = objforms.widgets.RightHalfCharField(required=False )
    comments = objforms.widgets.CommentField(required=False,
           help_text=Crystal.HELP['comments'])

    class Meta:
        model = Experiment
        fields = ('project','name', 'kind', 'plan', 'resolution',
                  'delta_angle','multiplicity', 'total_angle', 'i_sigma','r_meas',
                  'energy', 'absorption_edge','comments')

class ExperimentFromStrategyForm(objforms.forms.OrderedForm):
    project = forms.ModelChoiceField(queryset=Project.objects.all(), widget=forms.HiddenInput)
    strategy = forms.ModelChoiceField(queryset=Strategy.objects.all(), widget=forms.HiddenInput)
    name = objforms.widgets.LargeCharField(required=True)
    kind = objforms.widgets.LeftHalfChoiceField(label='Type', choices=Experiment.EXP_TYPES.get_choices(), required=True)
    plan = objforms.widgets.RightHalfChoiceField(label='Plan', choices=Experiment.EXP_PLANS.get_choices(), required=True)
    resolution = forms.FloatField(label='Desired Resolution', widget=objforms.widgets.LeftHalfInput, required=False )
    delta_angle = forms.FloatField(widget=objforms.widgets.RightHalfInput, required=False,
          help_text='If left blank, an appropriate value will be calculated during screening.')
    multiplicity = forms.FloatField(widget=objforms.widgets.LeftHalfInput, required=False,
          help_text='Values entered here take precedence over the specified "Angle Range".')
    total_angle = forms.FloatField(label='Angle Range', widget=objforms.widgets.RightHalfInput, required=False,
          help_text='The total angle range to collect.')
    i_sigma = forms.FloatField(label='Desired I/Sigma',widget=objforms.widgets.LeftHalfInput, required=False )
    r_meas = forms.FloatField(label='Desired R-factor', widget=objforms.widgets.RightHalfInput, required=False )
    energy = forms.DecimalField(widget=objforms.widgets.LeftHalfInput, required=False )
    absorption_edge = objforms.widgets.RightHalfCharField(required=False )
    crystals = forms.ModelChoiceField(queryset=None, widget=forms.Select)
    comments = objforms.widgets.CommentField(required=False,
           help_text='You can use Restructured Text formatting here.')
    class Meta:
        model = Experiment
        fields = ('project','strategy', 'name', 'kind', 'plan', 'resolution',
                  'delta_angle','multiplicity', 'total_angle', 'i_sigma','r_meas',
                  'energy', 'absorption_edge','crystals','comments')

    def __init__(self, *args, **kwargs):
        super(ExperimentFromStrategyForm, self).__init__(*args, **kwargs)
        self.fields['plan'].choices = [(Experiment.EXP_PLANS.JUST_COLLECT, Experiment.EXP_PLANS[Experiment.EXP_PLANS.JUST_COLLECT]),]
        pkey = self.initial.get('crystals', None) or self.data.get('crystals', None)
        self.fields['crystals'].queryset = Crystal.objects.filter(pk=pkey)
        self.fields['crystals'].choices = list(self.fields['crystals'].choices)[1:]

    def clean_crystals(self):
        if not self.cleaned_data.get('crystals', None):
            raise forms.ValidationError('Crystal did not exist for Strategy that this Experiment was based on.')
        return [self.cleaned_data['crystals']]
            
class CocktailForm(objforms.forms.OrderedForm):
    project = forms.ModelChoiceField(queryset=Project.objects.all(), widget=forms.HiddenInput)
    name = objforms.widgets.LargeCharField(required=True, label='Constituents')
    is_radioactive = objforms.widgets.LeftCheckBoxField(required=False)
    contains_heavy_metals = objforms.widgets.RightCheckBoxField(required=False)
    contains_prions = objforms.widgets.LeftCheckBoxField(required=False)
    contains_viruses = objforms.widgets.RightCheckBoxField(required=False)
    description = forms.CharField(
        widget=objforms.widgets.CommentInput,
        max_length=200, 
        required=False,
        help_text= Crystal.HELP['comments'])

    class Meta:
        model = Cocktail
        fields = ('project','name','is_radioactive','contains_heavy_metals','contains_prions','contains_viruses','description')

class CrystalFormForm(objforms.forms.OrderedForm):
    project = forms.ModelChoiceField(queryset=Project.objects.all(), widget=forms.HiddenInput)
    name = objforms.widgets.LargeCharField(required=True)
    space_group = forms.ModelChoiceField(
        widget=objforms.widgets.LargeSelect,
        queryset=SpaceGroup.objects.all(), 
        required=False)
    cell_a = forms.FloatField(label='a', widget=objforms.widgets.LeftThirdInput,required=False)
    cell_b = forms.FloatField(label='b', widget=objforms.widgets.MiddleThirdInput,required=False)
    cell_c = forms.FloatField(label='c', widget=objforms.widgets.RightThirdInput,required=False)
    cell_alpha = forms.FloatField(label='alpha', widget=objforms.widgets.LeftThirdInput,required=False)
    cell_beta = forms.FloatField(label='beta', widget=objforms.widgets.MiddleThirdInput,required=False)
    cell_gamma = forms.FloatField(label='gamma', widget=objforms.widgets.RightThirdInput,required=False)

    class Meta:
        model = CrystalForm 
        fields = ('project','name', 'space_group','cell_a','cell_b','cell_c','cell_alpha','cell_beta','cell_gamma')
    
class DataForm(forms.ModelForm):
    class Meta:
        model = Data
        
class StrategyRejectForm(objforms.forms.OrderedForm):
    name = objforms.widgets.LargeCharField(widget=forms.HiddenInput, required=False)

    class Meta:
        model = Strategy
        fields = ('name',)
        
    def get_message(self):
        return "Are you sure you want to reject this Strategy?"

class FeedbackForm(objforms.forms.OrderedForm):
    project = forms.ModelChoiceField(queryset=Project.objects.all(), widget=forms.HiddenInput)
    contact_name = objforms.widgets.LargeCharField(label='Name (optional)', required=False)
    contact = forms.EmailField(widget=objforms.widgets.LargeInput, label="Email Address (optional)", required=False)
    category = forms.ChoiceField(choices=Feedback.TYPE.get_choices(), widget=objforms.widgets.LargeSelect)
    message = objforms.widgets.LargeTextField(required=True)

    class Meta:
        model = Feedback
        fields = ('project','contact_name','contact','category','message')

class CommentsForm(objforms.forms.OrderedForm):
    comments = objforms.widgets.CommentField(required=False, 
            help_text="Comments entered here will be visible to staff at the CMCF. You can use Restructured Text markup for formatting.")

    class Meta:
        fields = ('comments',)

    def is_valid(self):
        super(CommentsForm, self).is_valid()
        return self.cleaned_data.get('comments', None)

    
