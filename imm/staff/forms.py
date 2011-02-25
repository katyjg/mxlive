import logging

from imm import objforms
from imm.lims.models import Shipment
from imm.lims.models import Carrier
from imm.lims.models import Container
from imm.lims.models import Experiment
from imm.lims.models import Dewar
from imm.lims.models import Beamline
from imm.lims.models import Project
from imm.staff.models import Link

from imm.staff.models import Runlist

from django.forms.util import ErrorList

from django import forms
from django.forms import widgets

class DewarForm(objforms.forms.OrderedForm):
    comments = objforms.widgets.CommentField(required=False)
    storage_location = objforms.widgets.CommentField(required=False)
    class Meta:
        model = Dewar
        fields = ('comments', 'storage_location')
    
class DewarReceiveForm(objforms.forms.OrderedForm):
    """ Form used to receive a Dewar, based on the Dewar upc code """
    name = forms.ModelChoiceField(
        queryset=Dewar.objects.filter(status=Dewar.STATES.SENT),
        widget=objforms.widgets.LargeSelect,
        help_text='Please select the Dewar to receive.',
        required=True, initial=''
        )
    barcode = objforms.widgets.BarCodeField(required=True)
    staff_comments = objforms.widgets.CommentField(required=False)
    storage_location = objforms.widgets.CommentField(required=False)
    
    class Meta:
        model = Dewar
        fields = ('name', 'barcode', 'staff_comments', 'storage_location')
        
    def __init__(self, *args, **kwargs):
        super(DewarReceiveForm, self).__init__(*args, **kwargs)
        self.fields['name'].queryset = Dewar.objects.filter(name=self.initial.get('name', None)) or Dewar.objects.filter(status=Dewar.STATES.SENT)

    def clean(self):
        cleaned_data = self.cleaned_data
        barcode = cleaned_data.get("barcode")
        name = cleaned_data.get("name")
        if name:
            try:
                instance = self.Meta.model.objects.get(name__exact=name)
                if instance.status != Dewar.STATES.SENT:
                    raise forms.ValidationError('Dewar already received.')
                if instance.barcode() != barcode:
                    self._errors['barcode'] = self._errors.get('barcode', ErrorList())
                    self._errors['barcode'].append('Incorrect barcode.')
                    raise forms.ValidationError('Incorrect barcode.')
                self.instance = instance
            except Dewar.DoesNotExist:
                raise forms.ValidationError('No Dewar found with matching tracking code. Did you scan the correct Shipment?')
        return cleaned_data
   
class ShipmentReturnForm(objforms.forms.OrderedForm):
    """ Form used to return a Shipment """
    carrier = forms.ModelChoiceField(
        queryset=Carrier.objects.all(),
        widget=objforms.widgets.LargeSelect,
        help_text='Please select the carrier company.',
        required=True
        )
    return_code = objforms.widgets.LargeCharField(required=True)

    class Meta:
        model = Shipment
        fields = ('carrier', 'return_code')
        
    def warning_message(self):
        """ Returns a warning message to display in the form - accessed in objforms/plain.py """
        shipment = self.instance
        if shipment:
            for experiment in shipment.project.experiment_set.all():
                if experiment.status != Experiment.STATES.REVIEWED:
                    return 'Experiment "%s" has not been reviewed. Click "Cancel" to complete Experiments.' % experiment.name

    def clean_return_code(self):
        cleaned_data = self.cleaned_data['return_code']
        # put this here instead of .clean() because objforms does not display form-wide error messages
        if self.instance.status != Shipment.STATES.ON_SITE:
            raise forms.ValidationError('Shipment already returned.')
        return cleaned_data
    
class RunlistForm(objforms.forms.OrderedForm):
    """ Form used to create a Runlist """
    name = objforms.widgets.LargeCharField(required=True)
    beamline = forms.ModelChoiceField(
        queryset=Beamline.objects.all(),
        widget=objforms.widgets.LargeSelect,
        required=True
        )
    comments = objforms.widgets.CommentField(required=False)

    class Meta:
        model = Runlist
        fields = ('name', 'beamline', 'comments') #, 'experiments', 'containers')
        
    def _update(self):
        cleaned_data = self.cleaned_data
       # experiments = cleaned_data.get('experiments', [])
        
        # containers don't have experiments. Need to go to crystals in container, iterate them, 
            # and add container once one crystal is in the experiment...
        #choices = Container.objects.all().filter(crystal.experiment=experiments)
        
        #self.fields['containers'].queryset = choices
        
        
class RunlistEmptyForm(objforms.forms.OrderedForm):
    """ Form used to load/complete a Runlist """
    name = forms.CharField(widget=widgets.HiddenInput)
    
    class Meta:
        model = Runlist
        fields = ('name',)
        
class LinkForm(objforms.forms.OrderedForm):
    description = objforms.widgets.SmallTextField(required=True)
    category = forms.ChoiceField(choices=Link.CATEGORY.get_choices(), widget=objforms.widgets.LeftHalfSelect, required=False)
    frame_type = forms.ChoiceField(choices=Link.TYPE.get_choices(), widget=objforms.widgets.RightHalfSelect, required=False)
    url = forms.URLField(widget=objforms.widgets.LargeInput, label='External Web site', required=False)
    document = forms.Field(widget=objforms.widgets.LargeFileInput, required=False)

    class Meta:
        model = Link
        fields = ('description','category','frame_type','url','document')

    def _update(self):
        cleaned_data = self.cleaned_data

class StaffCommentsForm(objforms.forms.OrderedForm):
    staff_comments = objforms.widgets.CommentField(required=False, help_text="Comments entered here will be visible on the user's LIMS account.")

    class Meta:
        fields = ('staff_comments',)


