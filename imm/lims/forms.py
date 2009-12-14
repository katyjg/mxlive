from django import forms
from models import *
from datetime import datetime
import objforms.widgets
import objforms.forms

            
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

class ShipmentSendForm(objforms.forms.OrderedForm):
    project = forms.ModelChoiceField(queryset=Project.objects.all(), widget=forms.HiddenInput)
    carrier = forms.ModelChoiceField(
        queryset=Carrier.objects.all(),
        widget=objforms.widgets.LargeSelect,
        help_text='Please select the carrier company.',
        required=True
        )
    tracking_code = objforms.widgets.LargeCharField(required=True)
    date_shipped = forms.DateTimeField(required=True,
        widget=objforms.widgets.LargeInput,
        )
    comments = objforms.widgets.CommentField(required=False)
    status = forms.CharField(widget=forms.HiddenInput, required=True)
    class Meta:
        model = Shipment
        fields = ('project','carrier', 'tracking_code','date_shipped', 'comments', 'status')


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
        help_text='The mixture of protein, buffer, precipitant or heavy atoms that make up your crystal'
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
                raise forms.ValidationError('Not a valid location for this container')
            if not self.cleaned_data['container'].location_is_available( self.cleaned_data['container_location'], pk ):
                raise forms.ValidationError('Another sample is alreay in that position.')
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
    hi_res = forms.FloatField(label='Desired High Res.', widget=objforms.widgets.LeftHalfInput, required=False )
    lo_res = forms.FloatField(label='Desired Low Res.', widget=objforms.widgets.RightHalfInput, required=False )
    i_sigma = forms.FloatField(label='I/Sigma',widget=objforms.widgets.LeftHalfInput, required=False )
    r_meas = forms.FloatField(widget=objforms.widgets.RightHalfInput, required=False )
    multiplicity = forms.IntegerField(widget=objforms.widgets.LargeInput, required=False)
    energy = forms.FloatField(widget=objforms.widgets.LeftHalfInput, required=False )
    absorption_edge = objforms.widgets.RightHalfCharField(required=False )
    comments = objforms.widgets.CommentField(required=False)
    class Meta:
        model = Experiment
        fields = ('project','name', 'kind', 'plan', 'hi_res',
                  'lo_res','i_sigma', 'r_meas', 'multiplicity',
                  'energy', 'absorption_edge','crystals','comments')

class CocktailForm(objforms.forms.OrderedForm):
    project = forms.ModelChoiceField(queryset=Project.objects.all(), widget=forms.HiddenInput)
    comments = forms.CharField(
        widget=objforms.widgets.CommentInput, 
        max_length=200, 
        required=False,
        help_text= Crystal.HELP['comments'])
    class Meta:
        model = Cocktail
        fields = ('project','constituents','comments')

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
    
class ConstituentForm(objforms.forms.OrderedForm):
    project = forms.ModelChoiceField(queryset=Project.objects.all(), widget=forms.HiddenInput)
    name = objforms.widgets.LargeCharField(required=True)
    acronym = objforms.widgets.LargeCharField(required=True)
    kind = objforms.widgets.RightHalfChoiceField(required=True,choices=Constituent.TYPES.get_choices())
    source = objforms.widgets.LeftHalfChoiceField(required=True, choices=Constituent.SOURCES.get_choices())
    is_radioactive = objforms.widgets.LeftCheckBoxField(required=False)
    is_contaminant = objforms.widgets.RightCheckBoxField(required=False)
    is_toxic = objforms.widgets.LeftCheckBoxField(required=False)
    is_oxidising = objforms.widgets.RightCheckBoxField(required=False)
    is_explosive = objforms.widgets.LeftCheckBoxField(required=False)
    is_corrosive = objforms.widgets.RightCheckBoxField(required=False)
    is_inflamable = objforms.widgets.LeftCheckBoxField(required=False)
    is_biological_hazard = objforms.widgets.RightCheckBoxField(required=False)
    hazard_details = objforms.widgets.CommentField(required=False)
    class Meta:
        model = Constituent
    

    
