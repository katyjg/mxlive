from models import Runlist, UserList, Link
from django import forms
from django.conf import settings
from django.forms import widgets
from django.forms.utils import ErrorList
from django.core.urlresolvers import reverse_lazy
from lims.models import Beamline, Carrier, Container, Group, Shipment, Project
import objforms.forms
import re

from crispy_forms.helper import FormHelper
from crispy_forms.layout import Layout, HTML, Div, Field, Button
from crispy_forms.bootstrap import Accordion, AccordionGroup, Tab, TabHolder, PrependedText, InlineField
from crispy_forms.bootstrap import StrictButton, FormActions

# class DewarForm(objforms.forms.OrderedForm):
#     comments = objforms.widgets.CommentField(required=False)
#     storage_location = objforms.widgets.CommentField(required=False)
#
#     class Meta:
#         model = Dewar
#         fields = ('comments', 'storage_location')
#

# class DewarReceiveForm(objforms.forms.OrderedForm):
#     """ Form used to receive a Dewar, based on the Dewar upc code """
#     barcode = objforms.widgets.BarCodeReturnField(required=True,
#                                                   help_text='Please scan in the dewar barcode or type it in.')
#     storage_location = objforms.widgets.LargeCharField(required=True,
#                                                        help_text='Please briefly describe where the dewar will be stored.')
#     staff_comments = objforms.widgets.CommentField(required=False)
#
#     class Meta:
#         model = Dewar
#         fields = ('barcode', 'storage_location', 'staff_comments')
#
#     def __init__(self, *args, **kwargs):
#         super(DewarReceiveForm, self).__init__(*args, **kwargs)
#
#     def clean(self):
#         cleaned_data = self.cleaned_data
#         barcode = cleaned_data.get("barcode", "")
#         bc_match = re.match("[A-Z]{2,3}(?P<dewar_id>\d{4})-(?P<shipment_id>\d{4})", barcode)
#
#         if bc_match:
#             dewar_id = int(bc_match.group('dewar_id'))
#             shipment_id = int(bc_match.group('shipment_id'))
#             try:
#                 instance = Dewar.objects.filter(shipment__id__exact=shipment_id).get(pk=dewar_id)
#                 if instance.status != Dewar.STATES.SENT:
#                     self._errors['barcode'] = self._errors.get('barcode', ErrorList())
#                     self._errors['barcode'].append('This dewar can not be received.')
#                     raise forms.ValidationError('Dewar already received.')
#                 if instance.barcode() != barcode:
#                     self._errors['barcode'] = self._errors.get('barcode', ErrorList())
#                     self._errors['barcode'].append('Barcode Mismatch.')
#                     raise forms.ValidationError('Incorrect barcode.')
#                 self.instance = instance
#             except Dewar.DoesNotExist:
#                 self._errors['barcode'] = self._errors.get('barcode', ErrorList())
#                 self._errors['barcode'].append('Incorrect barcode.')
#                 raise forms.ValidationError(
#                     'No Dewar found with matching tracking code. Did you scan the correct dewar?')
#         else:
#             if barcode != "":
#                 self._errors['barcode'] = self._errors.get('barcode', ErrorList())
#                 self._errors['barcode'].append('Invalid barcode format.')
#             raise forms.ValidationError('Invalid barcode. Please scan in the correct barcode.')
#         return cleaned_data


class ShipmentReturnForm(objforms.forms.OrderedForm):
    """ Form used to return a Shipment """
    carrier = forms.ModelChoiceField(
        queryset=Carrier.objects.all(),
        widget=objforms.widgets.LargeSelect,
        help_text='Please select the carrier company.',
        required=True
    )
    return_code = objforms.widgets.LargeCharField(required=False)

    class Meta:
        model = Shipment
        fields = ('carrier', 'return_code')

    def warning_message(self):
        """ Returns a warning message to display in the form - accessed in objforms/plain.py """
        shipment = self.instance
        if shipment:
            container_list = shipment.project.container_set.filter(dewar__shipment__exact=shipment.pk,
                                                                   status__exact=Container.STATES.LOADED)
            if container_list.count():
                return 'There are containers still loaded in the %s automounter.' % container_list[0].runlist_set.all()[
                    0].beamline
            for experiment in shipment.project.experiment_set.filter(
                    pk__in=shipment.project.sample_set.filter(container__dewar__shipment__exact=shipment.pk).values(
                            'experiment')):
                if experiment.status != Group.STATES.REVIEWED:
                    return 'Experiment "%s" has not been reviewed. Click "Cancel" to review Experiments.' % experiment.name

    def clean_return_code(self):
        cleaned_data = self.cleaned_data['return_code']
        # put this here instead of .clean() because objforms does not display form-wide error messages
        if self.instance.status != Shipment.STATES.ON_SITE:
            raise forms.ValidationError('Shipment already returned.')
        return cleaned_data

    def restrict_by(self, field_name, value):
        pass


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
        fields = ('name', 'beamline', 'comments')  # , 'experiments', 'containers')


class RunlistEmptyForm(objforms.forms.OrderedForm):
    """ Form used to load/complete a Runlist """
    name = forms.CharField(widget=widgets.HiddenInput)

    class Meta:
        model = Runlist
        fields = ('name',)


class LinkForm(objforms.forms.OrderedForm):
    description = objforms.widgets.SmallTextField(required=True)
    category = forms.ChoiceField(choices=Link.CATEGORY, widget=objforms.widgets.LeftHalfSelect,
                                 required=False)
    frame_type = forms.ChoiceField(choices=Link.TYPE, widget=objforms.widgets.RightHalfSelect,
                                   required=False)
    url = forms.CharField(widget=objforms.widgets.LargeInput, label='Absolute or Relative address', required=False)
    document = forms.Field(widget=objforms.widgets.LargeFileInput, required=False)

    class Meta:
        model = Link
        fields = ('description', 'category', 'frame_type', 'url', 'document')

    def _update(self):
        cleaned_data = self.cleaned_data


class AccessForm(forms.ModelForm):

    def __init__(self, *args, **kwargs):
        super(AccessForm, self).__init__(*args, **kwargs)
        self.fields['users'].label = "Users on %s" % format(self.instance)
        self.fields['users'].queryset = self.fields['users'].queryset.order_by('name')

        self.helper = FormHelper()
        self.helper.title = u"Edit Remote Access List"
        self.helper.form_action = reverse_lazy('access-edit', kwargs={'address': self.instance.address})
        self.helper.layout = Layout(
            Div(
                Div(
                    Field('users', css_class="chosen"),
                    css_class="col-xs-12"
                ),
                Div(
                    HTML("""It may take a few minutes for your changes to be updated on the server.<br/>
                            Changes are pulled every 5 minutes.<br/><br/><br/><br/><br/>&nbsp;"""),
                    css_class="col-xs-12"
                ),
                css_class="row"
            ),
            FormActions(
                Div(
                    StrictButton('Save', type='submit', name="submit", value='save', css_class='btn btn-primary'),
                    css_class='pull-right'
                ),
            )
        )

    class Meta:
        model = UserList
        fields = ('users',)


class StaffCommentsForm(objforms.forms.OrderedForm):
    staff_comments = objforms.widgets.CommentField(required=False,
                                                   help_text="Comments entered here will be visible on the user's MxLIVE account. You can use Restructured Text markup for formatting.")

    class Meta:
        model = Project
        fields = ('staff_comments',)




class RunlistCommentsForm(objforms.forms.OrderedForm):
    comments = objforms.widgets.CommentField(required=False,
                                             help_text="Comments entered here will be visible on the user's MxLIVE account. You can use Restructured Text markup for formatting.")

    class Meta:
        model = Project
        fields = ('comments',)
