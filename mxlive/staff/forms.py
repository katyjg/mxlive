from models import UserList, Link
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
