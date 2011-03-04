import logging
import re

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
    barcode = objforms.widgets.BarCodeReturnField(required=True,
        help_text='Please scan in the dewar barcode or type it in. The format is "CLSxxxx-xxxx".')
    storage_location = objforms.widgets.LargeCharField(required=True,
        help_text='Please briefly describe where the dewar will be stored. For example "CMCF-BM 1608-7".')
    staff_comments = objforms.widgets.CommentField(required=False)
    
    class Meta:
        model = Dewar
        fields = ('barcode', 'storage_location', 'staff_comments')
        
    def __init__(self, *args, **kwargs):
        super(DewarReceiveForm, self).__init__(*args, **kwargs)

    def clean(self):
        cleaned_data = self.cleaned_data
        barcode = cleaned_data.get("barcode","")
        bc_match = re.match("CLS(?P<dewar_id>\d{4})-(?P<shipment_id>\d{4})", barcode)
        
        if bc_match:
            dewar_id = int(bc_match.group('dewar_id'))
            shipment_id = int(bc_match.group('shipment_id'))
            try:
                instance = Dewar.objects.filter(shipment__id__exact=shipment_id).get(pk=dewar_id)
                if instance.status != Dewar.STATES.SENT:
                    self._errors['barcode'] = self._errors.get('barcode', ErrorList())
                    self._errors['barcode'].append('This dewar can not be received.')
                    raise forms.ValidationError('Dewar already received.')
                if instance.barcode() != barcode:
                    self._errors['barcode'] = self._errors.get('barcode', ErrorList())
                    self._errors['barcode'].append('Barcode Mismatch.')
                    raise forms.ValidationError('Incorrect barcode.')
                self.instance = instance
            except Dewar.DoesNotExist:
                self._errors['barcode'] = self._errors.get('barcode', ErrorList())
                self._errors['barcode'].append('Incorrect barcode.')
                raise forms.ValidationError('No Dewar found with matching tracking code. Did you scan the correct dewar?')
        else:
            if barcode != "":
                self._errors['barcode'] = self._errors.get('barcode', ErrorList())
                self._errors['barcode'].append('Invalid barcode format.')
            raise forms.ValidationError('Invalid barcode. Please scan in the correct barcode.')
        print cleaned_data, self.is_valid(), self.errors
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
            for experiment in shipment.project.experiment_set.filter(pk__in=shipment.project.crystal_set.filter(container__dewar__shipment__exact=shipment.pk).values('experiment')):
                if experiment.status != Experiment.STATES.REVIEWED:
                    return 'Experiment "%s" has not been reviewed. Click "Cancel" to review Experiments.' % experiment.name

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
    staff_comments = objforms.widgets.CommentField(required=False, 
            help_text="Comments entered here will be visible on the user's LIMS account. You can use Restructured Text markup for formatting.")

    class Meta:
        fields = ('staff_comments',)


