import tempfile
import logging

from django import forms
from imm.lims.models import *
import imm.objforms.widgets
import imm.objforms.forms
from imm import objforms
from django.forms.util import ErrorList
from imm.lims.excel import LimsWorkbook, LimsWorkbookExport
            
class ShipmentForm(objforms.forms.OrderedForm):
    project = forms.ModelChoiceField(queryset=Project.objects.all(), widget=forms.HiddenInput)
    label = forms.CharField(
        widget=objforms.widgets.LargeInput,
        help_text=Shipment.HELP['label']
        )
    comments = objforms.widgets.CommentField(required=False)
    class Meta:
        model = Shipment
        fields = ('project','label','comments',)
        
class ShipmentDeleteForm(objforms.forms.OrderedForm):
    project = forms.ModelChoiceField(queryset=Project.objects.all(), widget=forms.HiddenInput)
    #label = forms.CharField(widget=objforms.widgets.LargeInput, help_text='Delete'  )
    class Meta:
        model = Shipment
        fields = ('project',)
    
        
class ShipmentUploadForm(forms.Form):
    project = forms.ModelChoiceField(queryset=Project.objects.all(), widget=forms.HiddenInput)
    excel = forms.Field(widget=forms.FileInput)
    
    NUM_ERRORS = 3
    
    def clean(self):
        """ Cleans the form globally. This simply delegates validation to the LimsWorkbook. """
        cleaned_data = self.cleaned_data
        if cleaned_data.has_key('project') and cleaned_data.has_key('excel'):
            temp = tempfile.NamedTemporaryFile()
            temp.write(self.files['excel'].read())
            temp.flush()
            self.workbook = LimsWorkbook(temp.name, cleaned_data['project'])
            if not self.workbook.is_valid():
                self._errors['excel'] = self._errors.get('excel', ErrorList())
                errors = self.workbook.errors[:self.NUM_ERRORS]
                if len(self.workbook.errors) > len(errors):
                    errors.append("and %d more errors..." % (len(self.workbook.errors)-len(errors)))
                self._errors['excel'].extend(errors)
                del cleaned_data['excel']
        return cleaned_data
    
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
        help_text='Please select the carrier company.',
        required=True
        )
    tracking_code = objforms.widgets.LargeCharField(required=True)
    comments = objforms.widgets.CommentField(required=False)
    
    class Meta:
        model = Shipment
        fields = ('project','carrier', 'tracking_code','comments')
        
    def warning_message(self):
        shipment = self.instance
        if shipment:
            for crystal in shipment.project.crystal_set.all():
                if crystal.num_experiments() == 0:
                    return 'Crystal "%s" is not associated with any Experiments. Sending the Shipment will create a ' \
                           'default "Screen and confirm" Experiment and assign all unassociated Crystals. Close this window ' \
                           'to setup the Experiment manually.' % crystal.name
                           
    def clean_tracking_code(self):
        cleaned_data = self.cleaned_data['tracking_code']
        # put this here instead of .clean() because objforms does not display form-wide error messages
        if self.instance.status != Shipment.STATES.DRAFT:
            raise forms.ValidationError('Shipment already sent.')
        return cleaned_data

class DewarForm(objforms.forms.OrderedForm):
    project = forms.ModelChoiceField(queryset=Project.objects.all(), widget=forms.HiddenInput)
    shipment = forms.ModelChoiceField(
        queryset=Shipment.objects.all(), 
        widget=objforms.widgets.LargeSelect,
        required=False
        )
    label = forms.CharField(
        widget=objforms.widgets.LargeInput,
        help_text=Dewar.HELP['label']
        )
    code = objforms.widgets.BarCodeField(required=False, help_text=Dewar.HELP['code'])
    comments = objforms.widgets.CommentField(required=False)
    class Meta:
        model = Dewar
        fields = ('project','label','code','shipment','comments',)

class ContainerForm(objforms.forms.OrderedForm):
    project = forms.ModelChoiceField(queryset=Project.objects.all(), widget=forms.HiddenInput)
    dewar = forms.ModelChoiceField(queryset=Dewar.objects.all(), widget=objforms.widgets.LargeSelect, required=False)
    label = forms.CharField(
        widget=objforms.widgets.LargeInput,
        help_text=Container.HELP['label']
        )
    code = objforms.widgets.MatrixCodeField(required=False, help_text=Container.HELP['code'])
    kind = forms.ChoiceField(choices=Container.TYPE.get_choices(), widget=objforms.widgets.LargeSelect, initial=Container.TYPE.UNI_PUCK)
    comments = objforms.widgets.CommentField(required=False)
    
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
        fields = ('project','label','code','kind','dewar','comments')

class SampleForm(objforms.forms.OrderedForm):
    project = forms.ModelChoiceField(queryset=Project.objects.all(), widget=forms.HiddenInput)
    name = forms.CharField(
        widget=objforms.widgets.LargeInput,
        help_text=Crystal.HELP['name']
        )
    code = objforms.widgets.MatrixCodeField(required=False, help_text=Crystal.HELP['code'])
    cocktail = forms.ModelChoiceField(
        queryset=Cocktail.objects.all(), 
        widget=objforms.widgets.LargeSelect(attrs={'class': 'field select leftHalf'}),
        help_text='The mixture of protein, buffer, precipitant or heavy atoms that make up your crystal',
        required=False
        )
    crystal_form = forms.ModelChoiceField(
        queryset=CrystalForm.objects.all(), 
        widget=objforms.widgets.LargeSelect(attrs={'class': 'field select rightHalf'}),
        required=False
        )
    pin_length = forms.IntegerField(widget=objforms.widgets.LeftHalfInput, help_text=Crystal.HELP['pin_length'], initial=18 )
    loop_size = forms.FloatField( widget=objforms.widgets.RightHalfInput, required=False )
    container = forms.ModelChoiceField(
        queryset=Container.objects.all(), 
        widget=objforms.widgets.LargeSelect(attrs={'class': 'field select leftHalf'}),
        required=False,
        )
    container_location = objforms.widgets.RightHalfCharField(
        required=False,
        help_text='This field is required only if a container has been selected'
        )
    comments = forms.CharField(
        widget=objforms.widgets.CommentInput, 
        max_length=200, 
        required=False,
        help_text= Crystal.HELP['comments'])
    
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
        fields = ('project','name','code','cocktail','crystal_form', 'pin_length',
                    'loop_size','container','container_location','comments')


class ObjectSelectForm(forms.Form):
    items = forms.ModelMultipleChoiceField(
        widget=forms.SelectMultiple(attrs={'class': 'field select large'}),
        queryset=None, 
        required=False,
        help_text='Select multiple items and then click submit to add them. Items already assigned will be reassigned.'
        )

        
class SampleSelectForm(forms.Form):
    """ A form that obeys the same 'items' interface as ObjectSelectForm, but also
        has the 'parent' model associated with the form.
    """
    parent = forms.ModelChoiceField(queryset=None, widget=forms.HiddenInput)
    items = forms.ModelChoiceField(queryset=None, label='Crystal sample')
    container_location = forms.ChoiceField(label='Container location')
    
    def __init__(self, *args, **kwargs):
        # construct the form
        super(SampleSelectForm, self).__init__(*args, **kwargs)
        
        # pop the parent model out because it is not valid to pass into superclass
        pk = self.initial.get('parent', None) or self.data.get('parent', None)
        container = Container.objects.get(pk=pk)
        self.fields['parent'].queryset = Container.objects.all()
        
        # find the crystals assign to the container, and remove the port choices
        # that are already assigned
        choices = list(container.get_location_choices()) # all ports
        for crystal in container.crystal_set.all():
            choice = (crystal.container_location, crystal.container_location)
            if choice in choices:
                choices.pop(choices.index(choice)) # remove assigned port
        self.fields['container_location'].choices = tuple(choices)
        

class DewarSelectForm(forms.Form):
    dewars = forms.ModelMultipleChoiceField(
        widget=forms.SelectMultiple(attrs={'class': 'field select large'}),
        queryset=Dewar.objects.all(), 
        required=False,
        help_text='Select multiple dewars and then click submit to add them to the shipment. Dewars already assigned to other shipments will be transfered to the current shipment'
        )
    
class ContainerSelectForm(forms.Form):
    containers = forms.ModelMultipleChoiceField(
        widget=forms.SelectMultiple(attrs={'class': 'field select large'}),
        queryset=Container.objects.all(), 
        required=False,
        help_text='Select multiple containers and then click submit to add them to the dewar. Containers already assigned to other dewars will be transfered to the current dewar'
        )
    
class ExperimentForm(objforms.forms.OrderedForm):
    project = forms.ModelChoiceField(queryset=Project.objects.all(), widget=forms.HiddenInput)
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
    energy = forms.DecimalField( max_digits=10, decimal_places=4, widget=objforms.widgets.LeftHalfInput, required=False )
    absorption_edge = objforms.widgets.RightHalfCharField(required=False )
    comments = objforms.widgets.CommentField(required=False)
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
    comments = objforms.widgets.CommentField(required=False)
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
    #constituents = forms.ModelMultipleChoiceField(
    #    widget=forms.SelectMultiple(attrs={'class': 'field select large'}),
    #    queryset=Constituent.objects.all(),
    #    required=False,
    #    help_text='Select multiple items and then click submit to add them.') 
    name = objforms.widgets.LargeCharField(required=True, help_text=Cocktail.HELP['name'])
    acronym = objforms.widgets.LargeCharField(required=True)
    kind = objforms.widgets.RightHalfChoiceField(required=True,choices=Cocktail.TYPES.get_choices())
    source = objforms.widgets.LeftHalfChoiceField(required=True, choices=Cocktail.SOURCES.get_choices())
    is_radioactive = objforms.widgets.LeftCheckBoxField(required=False)
    is_contaminant = objforms.widgets.RightCheckBoxField(required=False)
    is_toxic = objforms.widgets.LeftCheckBoxField(required=False)
    is_oxidising = objforms.widgets.RightCheckBoxField(required=False)
    is_explosive = objforms.widgets.LeftCheckBoxField(required=False)
    is_corrosive = objforms.widgets.RightCheckBoxField(required=False)
    is_inflamable = objforms.widgets.LeftCheckBoxField(required=False)
    is_biological_hazard = objforms.widgets.RightCheckBoxField(required=False)
    hazard_details = objforms.widgets.CommentField(required=False)
    comments = forms.CharField(
        widget=objforms.widgets.CommentInput,
        max_length=200, 
        required=False,
        help_text= Crystal.HELP['comments'])

    class Meta:
        model = Cocktail

class CrystalFormForm(objforms.forms.OrderedForm):
    project = forms.ModelChoiceField(queryset=Project.objects.all(), widget=forms.HiddenInput)
    name = objforms.widgets.LargeCharField(required=True)
    space_group = forms.ModelChoiceField(
        widget=objforms.widgets.LargeSelect,
        queryset=SpaceGroup.objects.all(), 
        required=False)
    cell_a = forms.FloatField(label='a', widget=objforms.widgets.LeftThirdInput,required=False, help_text='Dimension of the cell A-axis')
    cell_b = forms.FloatField(label='b', widget=objforms.widgets.MiddleThirdInput,required=False, help_text='Dimension of the cell B-axis')
    cell_c = forms.FloatField(label='c', widget=objforms.widgets.RightThirdInput,required=False, help_text='Dimension of the cell C-axis' )
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
    
