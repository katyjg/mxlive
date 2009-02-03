from django import forms
from widgets import *
from models import *
from datetime import datetime


class OrderedForm(forms.ModelForm):
    def __init__(self, *args, **kwargs):
        super(OrderedForm, self).__init__(*args, **kwargs)
        if self._meta.fields:
            self.fields.keyOrder = self._meta.fields


def restrict_to_project(form, project):
    for fieldname, field in form.fields.items():
        if fieldname != 'project' and hasattr(field, 'queryset'):
            queryset = field.queryset
            if 'project' in queryset.model._meta.get_all_field_names(): # some models will fields will not have a project field
                field.queryset = queryset.filter(project__exact=project.pk)
            
class ShipmentForm(OrderedForm):
    project = forms.ModelChoiceField(queryset=Project.objects.all(), widget=forms.HiddenInput)
    label = forms.CharField(
        widget=LargeInput,
        help_text=Shipment.HELP['label']
        )
    comments = CommentField(required=False)
    class Meta:
        model = Shipment
        fields = ('project','label','comments',)

class ShipmentSendForm(OrderedForm):
    project = forms.ModelChoiceField(queryset=Project.objects.all(), widget=forms.HiddenInput)
    carrier = forms.ModelChoiceField(
        queryset=Carrier.objects.all(),
        widget=LargeSelect,
        help_text='Please select the carrier company.',
        required=True
        )
    tracking_code = LargeCharField(required=True)
    date_shipped = forms.DateTimeField(required=True,
        widget=LargeInput,
        )
    comments = CommentField(required=False)
    status = forms.CharField(widget=forms.HiddenInput, required=True)
    class Meta:
        model = Shipment
        fields = ('project','carrier', 'tracking_code','date_shipped', 'comments', 'status')


class DewarForm(OrderedForm):
    project = forms.ModelChoiceField(queryset=Project.objects.all(), widget=forms.HiddenInput)
    shipment = forms.ModelChoiceField(
        queryset=Shipment.objects.all(), 
        widget=LargeSelect,
        required=False
        )
    label = forms.CharField(
        widget=LargeInput,
        help_text=Dewar.HELP['label']
        )
    code = BarCodeField(required=False, help_text=Dewar.HELP['code'])
    comments = CommentField(required=False)
    class Meta:
        model = Dewar
        fields = ('project','label','code','shipment','comments',)

class ContainerForm(OrderedForm):
    project = forms.ModelChoiceField(queryset=Project.objects.all(), widget=forms.HiddenInput)
    dewar = forms.ModelChoiceField(queryset=Dewar.objects.all(), widget=LargeSelect, required=False)
    label = forms.CharField(
        widget=LargeInput,
        help_text=Container.HELP['label']
        )
    code = MatrixCodeField(required=False, help_text=Container.HELP['code'])
    kind = forms.ChoiceField(choices=Container.TYPE.get_choices(), widget=LargeSelect, initial=Container.TYPE.UNI_PUCK)
    comments = CommentField(required=False)
    
    class Meta:
        model = Container
        fields = ('project','label','code','kind','dewar','comments')

class SampleForm(OrderedForm):
    project = forms.ModelChoiceField(queryset=Project.objects.all(), widget=forms.HiddenInput)
    name = forms.CharField(
        widget=LargeInput,
        help_text=Crystal.HELP['name']
        )
    code = MatrixCodeField(required=False, help_text=Crystal.HELP['code'])
    cocktail = forms.ModelChoiceField(
        queryset=Cocktail.objects.all(), 
        widget=LargeSelect(attrs={'class': 'field select leftHalf'}),
        help_text='The mixture of protein, buffer, precipitant or heavy atoms that make up your crystal'
        )
    crystal_form = forms.ModelChoiceField(
        queryset=CrystalForm.objects.all(), 
        widget=LargeSelect(attrs={'class': 'field select rightHalf'}),
        required=False
        )
    pin_length = forms.IntegerField(widget=LeftHalfInput, help_text=Crystal.HELP['pin_length'], initial=18 )
    loop_size = forms.FloatField( widget=RightHalfInput, required=False )
    container = forms.ModelChoiceField(
        queryset=Container.objects.all(), 
        widget=LargeSelect(attrs={'class': 'field select leftHalf'}),
        required=False,
        )
    container_location = RightHalfCharField(
        required=False,
        help_text='This field is required only if a container has been selected'
        )
    comments = forms.CharField(
        widget=CommentInput, 
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
    
class ExperimentForm(OrderedForm):
    project = forms.ModelChoiceField(queryset=Project.objects.all(), widget=forms.HiddenInput)
    name = LargeCharField(required=True)
    kind = LeftHalfChoiceField(label='Type', choices=Experiment.EXP_TYPES.get_choices(), required=True)
    plan = RightHalfChoiceField(label='Plan', choices=Experiment.EXP_PLANS.get_choices(), required=True)
    hi_res = forms.FloatField(label='Desired High Res.', widget=LeftHalfInput, required=False )
    lo_res = forms.FloatField(label='Desired Low Res.', widget=RightHalfInput, required=False )
    i_sigma = forms.FloatField(label='I/Sigma',widget=LeftHalfInput, required=False )
    r_meas = forms.FloatField(widget=RightHalfInput, required=False )
    multiplicity = forms.IntegerField(widget=LargeInput, required=False)
    energy = forms.FloatField(widget=LeftHalfInput, required=False )
    absorption_edge = RightHalfCharField(required=False )
    comments = CommentField(required=False)
    class Meta:
        model = Experiment
        fields = ('project','name', 'kind', 'plan', 'hi_res',
                  'lo_res','i_sigma', 'r_meas', 'multiplicity',
                  'energy', 'absorption_edge','crystals','comments')

class CocktailForm(OrderedForm):
    project = forms.ModelChoiceField(queryset=Project.objects.all(), widget=forms.HiddenInput)
    comments = forms.CharField(
        widget=CommentInput, 
        max_length=200, 
        required=False,
        help_text= Crystal.HELP['comments'])
    class Meta:
        model = Cocktail
        fields = ('project','constituents','comments')

class CrystalFormForm(OrderedForm):
    project = forms.ModelChoiceField(queryset=Project.objects.all(), widget=forms.HiddenInput)
    name = LargeCharField(required=True)
    space_group = forms.ModelChoiceField(
        widget=LargeSelect,
        queryset=SpaceGroup.objects.all(), 
        required=False)
    cell_a = forms.FloatField(label='a', widget=LeftThirdInput,required=False, help_text='Dimension of the cell A-axis')
    cell_b = forms.FloatField(label='b', widget=MiddleThirdInput,required=False, help_text='Dimension of the cell B-axis')
    cell_c = forms.FloatField(label='c', widget=RightThirdInput,required=False, help_text='Dimension of the cell C-axis' )
    cell_alpha = forms.FloatField(label='alpha', widget=LeftThirdInput,required=False)
    cell_beta = forms.FloatField(label='beta', widget=MiddleThirdInput,required=False)
    cell_gamma = forms.FloatField(label='gamma', widget=RightThirdInput,required=False)
    class Meta:
        model = CrystalForm
        fields = ('project','name', 'space_group','cell_a','cell_b','cell_c','cell_alpha','cell_beta','cell_gamma')
    
class ConstituentForm(forms.ModelForm):
    project = forms.ModelChoiceField(queryset=Project.objects.all(), widget=forms.HiddenInput)
    name = LargeCharField(required=True)
    acronym = LargeCharField(required=True)
    kind = RightHalfChoiceField(required=True,choices=Constituent.TYPES.get_choices())
    source = LeftHalfChoiceField(required=True, choices=Constituent.SOURCES.get_choices())
    is_radioactive = LeftCheckBoxField(required=False)
    is_contaminant = RightCheckBoxField(required=False)
    is_toxic = LeftCheckBoxField(required=False)
    is_oxidising = RightCheckBoxField(required=False)
    is_explosive = LeftCheckBoxField(required=False)
    is_corrosive = RightCheckBoxField(required=False)
    is_inflamable = LeftCheckBoxField(required=False)
    is_biological_hazard = RightCheckBoxField(required=False)
    hazard_details = CommentField(required=False)
    class Meta:
        model = Constituent
    

    
