from django import forms
from django.forms.utils import ErrorList
from django.forms import inlineformset_factory
from django.forms import BaseFormSet
from django.core.urlresolvers import reverse_lazy
from django.http import QueryDict
from django.utils import dateformat, timezone
import objforms.widgets
import uuid
from excel import LimsWorkbook
from models import *
from objforms.forms import OrderedForm
import re
import tempfile

from crispy_forms.helper import FormHelper
from crispy_forms.layout import Layout, HTML, Div, Field, Button
from crispy_forms.bootstrap import Accordion, AccordionGroup, Tab, TabHolder, PrependedText, InlineField
from crispy_forms.bootstrap import StrictButton, FormActions


disabled_widget = forms.HiddenInput(attrs={'readonly': True})

class BaseForm(forms.Form):
    def restrict_by(self, field_name, value):
        """
        Restrict the form such that only items related to the object identified by
        the primary key `value` through a field specified by `field_name`,
        are displayed within select boxes.
    
        Can also be used to restrict querysets based on some other field, where `field_name`
        also refers to the field of the foreign key object, like container__status, for example        
        """
        for name, formfield in self.fields.items():
            if name != field_name and hasattr(formfield, 'queryset'):
                queryset = formfield.queryset
                if field_name in queryset.model._meta.get_all_field_names():  # some models will not have the field
                    formfield.queryset = queryset.filter(**{'%s__exact' % (field_name): value})


class ProjectForm(forms.ModelForm):

    class Meta:
        model = Project
        fields = ('contact_person', 'contact_email', 'carrier', 'account_number', 'organisation', 'department', 'address',
                  'city', 'province', 'postal_code', 'country', 'contact_phone')

    def __init__(self, *args, **kwargs):
        super(ProjectForm, self).__init__(*args, **kwargs)
        pk = self.instance.pk

        self.helper = FormHelper()
        if pk:
            self.helper.title = u"Edit Profile"
            self.helper.form_action = reverse_lazy('edit-profile', kwargs={'username': self.instance.username})
        else:
            self.helper.title = u"Create New Sample"
            self.helper.form_action = reverse_lazy('sample-new')
        self.helper.layout = Layout(
            Div('contact_person', css_class='col-xs-12'),
            Div('contact_email', css_class='col-xs-6'),
            Div('contact_phone', css_class='col-xs-6'),
            Div(Field('carrier', css_class="chosen"), css_class='col-xs-6'),
            Div('account_number', css_class='col-xs-6'),
            Div('organisation', css_class='col-xs-12'),
            Div('department', css_class='col-xs-12'),
            Div('address', css_class='col-xs-12'),
            Div('city', css_class='col-xs-6'),
            Div('province', css_class='col-xs-6'),
            Div('country', css_class='col-xs-6'),
            Div('postal_code', css_class='col-xs-6'),
            FormActions(
                Div(
                    StrictButton('Revert', type='reset', value='Reset', css_class="btn btn-default"),
                    StrictButton('Save', type='submit', name="submit", value='save', css_class='btn btn-primary'),
                    css_class='pull-right'
                ),
            )
        )

class NewProjectForm(forms.ModelForm):

    class Meta:
        model = Project
        fields = ('first_name','last_name','contact_person','contact_email','contact_phone','username','password')

    def __init__(self, *args, **kwargs):
        super(NewProjectForm, self).__init__(*args, **kwargs)

        self.fields['password'].help_text = 'A password will be auto-generated for this account'
        if getattr(settings, 'LDAP_SEND_EMAILS', False):
            self.fields['password'].help_text += ' and sent to staff once this form is submitted'

        self.helper = FormHelper()
        self.helper.title = u"Create New User Account"
        self.helper.form_action = reverse_lazy('new-project')
        self.helper.layout = Layout(
            Div('username', css_class='col-xs-6'),
            Div(Field('password', disabled=True), css_class="col-xs-6"),
            Div('first_name', css_class='col-xs-6'),
            Div('last_name', css_class='col-xs-6'),
            Div('contact_person', css_class='col-xs-12'),
            Div('contact_email', css_class='col-xs-6'),
            Div('contact_phone', css_class='col-xs-6'),
            FormActions(
                Div(
                    StrictButton('Save', type='submit', name="submit", value='save', css_class='btn btn-primary'),
                    css_class='pull-right'
                ),
            )
        )



class ShipmentForm(forms.ModelForm):
    project = forms.ModelChoiceField(queryset=Project.objects.all(), widget=disabled_widget)
    name = forms.CharField(
        widget=objforms.widgets.LargeInput
    )
    comments = objforms.widgets.CommentField(required=False,
                                             help_text=Sample.HELP['comments'])

    def __init__(self, *args, **kwargs):
        super(ShipmentForm, self).__init__(*args, **kwargs)
        pk = self.instance.pk

        self.helper = FormHelper()
        if pk:
            self.helper.title = u"Edit Shipment"
            self.helper.form_action = reverse_lazy('shipment-edit', kwargs={'pk': pk})
        else:
            self.helper.title = u"Create New Shipment"
            self.helper.form_action = reverse_lazy('shipment-new')
        self.helper.layout = Layout(
            'project','name','comments',
            FormActions(
                Div(
                    StrictButton('Revert', type='reset', value='Reset', css_class="btn btn-default"),
                    StrictButton('Save', type='submit', name="submit", value='save', css_class='btn btn-primary'),
                    css_class='pull-right'
                ),
            )
        )

    class Meta:
        model = Shipment
        fields = ('project', 'name', 'comments',)


class DataForm(forms.ModelForm):

    class Meta:
        model = Data
        fields = ('staff_comments','resolution','start_angle','delta_angle','first_frame','frame_sets','exposure_time',
                  'two_theta','wavelength','detector','beamline')
        widgets = {
            'staff_comments': forms.Textarea(attrs={'rows': "4"}),
        }

    def __init__(self, *args, **kwargs):
        super(DataForm, self).__init__(*args, **kwargs)

        self.helper = FormHelper()
        self.helper.form_action = reverse_lazy('data-edit', kwargs={'pk': self.instance.pk})
        self.helper.title = "Add notes about this dataset"
        self.helper.layout = Layout(
            Div(
                Div('staff_comments', css_class="col-xs-12"),
                Div(Field('resolution', disabled=True), css_class="col-xs-3"),
                Div(Field('wavelength', disabled=True), css_class="col-xs-3"),
                Div(Field('delta_angle', disabled=True), css_class="col-xs-3"),
                Div(Field('exposure_time', disabled=True), css_class="col-xs-3"),
                Div(Field('start_angle', disabled=True), css_class="col-xs-3"),
                Div(Field('first_frame', disabled=True), css_class="col-xs-3"),
                Div(Field('frame_sets', disabled=True), css_class="col-xs-6"),
                Div(Field('beamline', disabled=True), css_class="col-xs-4"),
                Div(Field('detector', disabled=True), css_class="col-xs-4"),
                Div(Field('two_theta', disabled=True), css_class="col-xs-4"),
                css_class="row"
            ),
            FormActions(
                Div(
                    StrictButton('Revert', type='reset', value='Reset', css_class="btn btn-default"),
                    StrictButton('Save', type='submit', name="submit", value='save', css_class='btn btn-primary'),
                    css_class='pull-right'
                ),
            )
        )

class SampleDoneForm(forms.ModelForm):

    class Meta:
        model = Sample
        fields = ('collect_status',)

    def __init__(self, *args, **kwargs):
        super(SampleDoneForm, self).__init__(*args, **kwargs)

        self.helper = FormHelper()
        self.helper.layout = Layout('collect_status')

class SampleForm(forms.ModelForm):

    def __init__(self, *args, **kwargs):
        super(SampleForm, self).__init__(*args, **kwargs)
        pk = self.instance.pk

        self.helper = FormHelper()
        if pk:
            self.helper.title = u"Edit Sample"
            self.helper.form_action = reverse_lazy('sample-edit', kwargs={'pk': pk})
        else:
            self.helper.title = u"Create New Sample"
            self.helper.form_action = reverse_lazy('sample-new')
        self.helper.layout = Layout(
            'project','name','comments',
            'barcode','pin_length','loop_size','container','group','container_location',
            FormActions(
                Div(
                    StrictButton('Revert', type='reset', value='Reset', css_class="btn btn-default"),
                    StrictButton('Save', type='submit', name="submit", value='save', css_class='btn btn-primary'),
                    css_class='pull-right'
                ),
            )
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
            if not self.cleaned_data['container'].location_is_valid(self.cleaned_data['container_location']):
                raise forms.ValidationError(
                    'Not a valid location for this container (%s)' % self.cleaned_data['container'].TYPE[
                        self.cleaned_data['container'].kind])
            if not self.cleaned_data['container'].location_is_available(self.cleaned_data['container_location'], pk):
                raise forms.ValidationError('Another sample is already in that position.')
        return self.cleaned_data['container_location']

    class Meta:
        model = Sample
        fields = ('project', 'name', 'barcode', 'pin_length',
                  'loop_size', 'container', 'group', 'container_location', 'comments')




class ShipmentSendForm(forms.ModelForm):
    class Meta:
        model = Shipment
        fields = ('carrier','tracking_code','comments')
        widgets = {
            'comments': forms.Textarea(attrs={'rows': "4"}),
        }

    def __init__(self, *args, **kwargs):
        super(ShipmentSendForm, self).__init__(*args, **kwargs)
        self.helper = FormHelper()
        self.helper.title = u"Add Shipping Information"
        self.helper.form_action = reverse_lazy('shipment-send', kwargs={'pk': self.instance.pk})
        self.helper.layout = Layout(
            Div(
                Div(Field('carrier', css_class="chosen"), css_class="col-xs-6"),
                Div('tracking_code', css_class="col-xs-6"),
                Div('comments', css_class="col-xs-12"),
                css_class="row"
            ),
            FormActions(
                Div(
                    StrictButton('Save', type='submit', name="submit", value='save', css_class='btn btn-primary'),
                    css_class='pull-right'
                ),
            )
        )


class ShipmentReturnForm(forms.ModelForm):
    class Meta:
        model = Shipment
        fields = ['carrier','return_code','staff_comments']

    def __init__(self, *args, **kwargs):
        super(ShipmentReturnForm, self).__init__(*args, **kwargs)
        self.helper = FormHelper()
        self.helper.title = u"Add Shipping Information"
        self.helper.form_action = reverse_lazy('shipment-return', kwargs={'pk': self.instance.pk})
        self.helper.layout = Layout(
            Div(
                Div(Field('carrier', css_class="chosen"), css_class="col-xs-6"),
                Div('return_code', css_class="col-xs-6"),
                Div('staff_comments', css_class="col-xs-12"),
                css_class="row"
            ),
            FormActions(
                Div(
                    StrictButton('Revert', type='reset', value='Reset', css_class="btn btn-default"),
                    StrictButton('Save', type='submit', name="submit", value='save', css_class='btn btn-primary'),
                    css_class='pull-right'
                ),
            )
        )


class ShipmentRecallSendForm(forms.ModelForm):
    class Meta:
        model = Shipment
        fields = ['carrier','tracking_code','comments']

    def __init__(self, *args, **kwargs):
        super(ShipmentRecallSendForm, self).__init__(*args, **kwargs)
        self.helper = FormHelper()
        self.helper.title = u"Update Shipping Information"
        self.helper.form_action = reverse_lazy('shipment-update-send', kwargs={'pk': self.instance.pk})
        self.helper.layout = Layout(
            Div(
                Div(Field('carrier', css_class="chosen"), css_class="col-xs-6"),
                Div('tracking_code', css_class="col-xs-6"),
                Div('comments', css_class="col-xs-12"),
                css_class="row"
            ),
            FormActions(
                Div(
                    StrictButton('Unsend', type='recall', value='Recall', css_class="btn btn-danger"),
                    StrictButton('Save', type='submit', name="submit", value='save', css_class='btn btn-primary'),
                    css_class='pull-right'
                ),
            )
        )

class ShipmentRecallReturnForm(forms.ModelForm):
    class Meta:
        model = Shipment
        fields = ['carrier','return_code','staff_comments']

    def __init__(self, *args, **kwargs):
        super(ShipmentRecallReturnForm, self).__init__(*args, **kwargs)
        self.helper = FormHelper()
        self.helper.title = u"Update Shipping Information"
        self.helper.form_action = reverse_lazy('shipment-update-return', kwargs={'pk': self.instance.pk})
        self.helper.layout = Layout(
            Div(
                Div(Field('carrier', css_class="chosen"), css_class="col-xs-6"),
                Div('return_code', css_class="col-xs-6"),
                Div('staff_comments', css_class="col-xs-12"),
                css_class="row"
            ),
            FormActions(
                Div(
                    StrictButton('Unsend', type='recall', value='Recall', css_class="btn btn-danger"),
                    StrictButton('Save', type='submit', name="submit", value='save', css_class='btn btn-primary'),
                    css_class='pull-right'
                ),
            )
        )

class ShipmentReceiveForm(forms.ModelForm):

    class Meta:
        model = Shipment
        fields = ['storage_location','staff_comments']

    def __init__(self, *args, **kwargs):
        super(ShipmentReceiveForm, self).__init__(*args, **kwargs)
        self.helper = FormHelper()
        self.helper.title = u"Receive Shipment?"
        self.helper.form_action = reverse_lazy('shipment-receive', kwargs={'pk': self.instance.pk})
        self.helper.layout = Layout(
            'storage_location','staff_comments',
            FormActions(
                Div(
                    StrictButton('Revert', type='reset', value='Reset', css_class="btn btn-default"),
                    StrictButton('Save', type='submit', value='save', css_class='btn btn-primary'),
                    css_class='pull-right'
                ),
            )
        )

class ShipmentArchiveForm(forms.ModelForm):
    class Meta:
        model = Shipment
        fields = []

    def __init__(self, *args, **kwargs):
        super(ShipmentArchiveForm, self).__init__(*args, **kwargs)
        self.helper = FormHelper()
        self.helper.title = u"Archive Shipment?"
        self.helper.form_action = reverse_lazy('shipment-archive', kwargs={'pk': self.instance.pk})
        self.helper.layout = Layout(
            HTML("""{{ object }}"""),
            FormActions(
                Div(
                    StrictButton('Save', type='submit', name="submit", value='save', css_class='btn btn-primary'),
                    css_class='pull-right'
                ),
            )
        )

class ContainerForm(forms.ModelForm):

    def __init__(self, *args, **kwargs):
        super(ContainerForm, self).__init__(*args, **kwargs)
        pk = self.instance.pk

        self.helper = FormHelper()
        if pk:
            self.helper.title = u"Edit Container"
            self.helper.form_action = reverse_lazy("container-edit", kwargs={'pk': pk})
        else:
            self.helper.title = u"Create New Container"
            self.helper.form_action = reverse_lazy("container-new")
        self.helper.layout = Layout(
            'project','name','shipment','comments',
            FormActions(
                Div(
                    StrictButton('Save', type='submit', name="submit", value='submit', css_class='btn btn-primary'),
                    css_class='pull-right'
                ),
            )
        )

    def clean_kind(self):
        """ Ensures that the 'kind' of Container cannot be changed when Crystals are associated with it """
        cleaned_data = self.cleaned_data
        if self.instance.pk:
            if self.instance.kind != cleaned_data['kind']:
                if self.instance.num_samples() > 0:
                    raise forms.ValidationError('Cannot change kind of Container when Crystals are associated')
        return cleaned_data['kind']

    class Meta:
        model = Container
        fields = ['project', 'name', 'shipment', 'comments']
        widgets = {'project': disabled_widget}

class ContainerLoadForm(forms.ModelForm):

    def __init__(self, *args, **kwargs):
        super(ContainerLoadForm, self).__init__(*args, **kwargs)

        self.fields['parent'].queryset = self.fields['parent'].queryset.filter(kind__container_locations=self.instance.kind.locations.all())

        self.helper = FormHelper()
        self.helper.title = u"Move Container"
        self.helper.form_action = reverse_lazy("container-load", kwargs={'pk': self.instance.pk})

        self.helper.layout = Layout(
            Div(
                Div(
                    Field('parent', css_class="chosen"),
                    css_class="col-xs-6"
                ),
                Div(
                    Field('location', css_class="chosen"),
                    css_class="col-xs-6"
                ),
                css_class="row"
            ),
            FormActions(
                Div(
                    StrictButton('Save', type='submit', name="submit", value='submit', css_class='btn btn-primary'),
                    css_class='pull-right'
                ),
            )
        )

    class Meta:
        model = Container
        fields = ['parent','location']


class LocationLoadForm(forms.ModelForm):
    child = forms.ModelMultipleChoiceField(label="Container", queryset=Container.objects.filter(status=Container.STATES.ON_SITE))
    container_location = forms.ModelChoiceField(queryset=ContainerLocation.objects.all())

    class Meta:
        model = Container
        fields = ['child','container_location']

    def __init__(self, *args, **kwargs):
        super(LocationLoadForm, self).__init__(*args, **kwargs)

        self.fields['child'].queryset = self.fields['child'].queryset.filter(parent__isnull=True).filter(kind__in=self.initial['container_location'].accepts.all())

        self.helper = FormHelper()
        self.helper.title = u"Load Container in location {}".format(self.initial['container_location'])
        self.helper.form_action = reverse_lazy("location-load", kwargs={'pk': self.instance.pk, 'location': self.initial['container_location'].name})

        self.helper.layout = Layout(
            Div(
                Field('container_location', type="hidden"),
                Div(
                    Field('child', css_class="chosen"),
                    css_class="col-xs-12"
                ),
                css_class="row"
            ),
            FormActions(
                Div(
                    StrictButton('Save', type='submit', name="submit", value='submit', css_class='btn btn-primary'),
                    css_class='pull-right'
                ),
            )
        )

class AddShipmentForm(forms.ModelForm):
    class Meta:
        model = Shipment
        fields = ('name','comments','project')
        widgets = {
            'comments': forms.Textarea(),
            'project': forms.HiddenInput(),
        }

    def __init__(self, *args, **kwargs):
        super(AddShipmentForm, self).__init__(*args, **kwargs)

        self.helper = FormHelper()
        self.helper.layout = Layout(
            Div(
                Div(
                    HTML("""<h4>Step 1: Give your shipment a name!</h4>"""),
                    HTML("""<small>This name will be visible to you and staff at the beamline.</small>"""),
                    Field('name', css_class="col-xs-12"),
                    Field('comments', rows="2", css_class="col-xs-12"),
                    'project',
                    css_class="col-xs-12"
                ),
                css_class="row"
            )
        )

    def clean(self):
        cleaned_data = super(AddShipmentForm, self).clean()
        if cleaned_data['project'].shipment_set.filter(name__iexact=cleaned_data['name']).exists():
            self.add_error('name', forms.ValidationError("Shipment with this name already exists"))


class ShipmentContainerForm(forms.ModelForm):
    id = forms.CharField(required=False, widget=forms.HiddenInput)

    class Meta:
        model = Container
        fields = ('shipment', 'id', 'name', 'kind')
        widgets = {'shipment': forms.HiddenInput()}

    def __init__(self, *args, **kwargs):
        super(ShipmentContainerForm, self).__init__(*args, **kwargs)

        self.fields['kind'].queryset = self.fields['kind'].queryset.filter(container_locations__in=ContainerLocation.objects.filter(accepts__isnull=True)).distinct()

        self.repeated_fields = ['name','kind','id']
        self.repeated_data = {}
        for f in self.repeated_fields:
            self.fields['{}_set'.format(f)] = forms.CharField(required=False)

        self.helper = FormHelper()
        self.helper.layout = Layout(
            Div(
                Div(
                    self.help_text(),
                    css_class="col-xs-12"
                ),
                css_class="row"
            ),
            Div(
                Div(
                    Div(
                        Div(
                            Div(Field('shipment')),
                            Div(Field('id', css_id="id")),
                            Div(Field('name', css_id="name"), css_class="col-xs-5"),
                            Div(Field('kind', css_class="tab-chosen chosen-single chosen-select", css_id="kind"), css_class="col-xs-5"),
                            Div(HTML("""<a title="Remove Group" class="inline-btn remove btn btn-danger"><i class="fa fa-fw fa-remove"></i></a>"""),
                                css_class="col-xs-2"),
                            css_class="col-xs-12 template repeat-row list-group-item"
                        ),
                        css_class="row repeat-group repeat-container list-group list-group-hover",
                    ),
                    Div(
                        HTML("""<br/>"""),
                        Button('Add', type='add', value='Add Another', css_class="btn btn-success add"),
                        css_class="col-xs-12"
                    ),
                    css_class="repeat-wrapper"
                ),
                css_class='repeat'
            )
        )

        if self.initial.get('shipment'):
            self.repeated_data['name_set'] = [str(container.name) for container in self.initial['shipment'].container_set.all()]
            self.repeated_data['id_set'] = [container.pk for container in self.initial['shipment'].container_set.all()]
            self.repeated_data['kind_set'] = [container.kind.pk for container in self.initial['shipment'].container_set.all()]
            self.helper.form_action = reverse_lazy('shipment-add-containers', kwargs={'pk': self.initial['shipment'].pk})
            self.helper.title = 'Add Containers to Shipment'
            self.helper.layout.append(
                FormActions(
                    Div(
                        StrictButton('Save and Continue', type='submit', name="submit", value='submit', css_class='btn btn-primary'),
                        css_class='pull-right'
                    ),
                ))

    def help_text(self):
        if self.initial.get('shipment'):
            return Div(HTML("""Use labels that are visible on your containers.<br/>
                               <strong>Be careful! Removing a container will also remove the samples inside</strong><br/>&nbsp;""")
                       )
        else:
            return Div(HTML("""<h4>Step 2: Add the containers you are bringing!</h4>"""),
                       HTML("""<small>Use labels that are visible on your containers.
                               Don't worry, you can always add more containers later.</small>"""))

    def clean(self):
        self.repeated_data = {}
        self.cleaned_data = super(ShipmentContainerForm, self).clean()
        for field in self.repeated_fields:
            if 'containers-{}'.format(field) in self.data:
                self.cleaned_data['{}_set'.format(field)] = self.data.getlist('containers-{}'.format(field))
            else:
                self.cleaned_data['{}_set'.format(field)] = self.data.getlist(field)
            self.fields[field].initial = self.cleaned_data['{}_set'.format(field)]
        if not self.is_valid():
            for k, v in self.cleaned_data.items():
                if type(v) == type([]):
                    self.repeated_data[k] = [str(e) for e in v]
        return self.cleaned_data


class ShipmentGroupForm(forms.ModelForm):
    id = forms.CharField(required=False, widget=forms.HiddenInput)
    sample_locations = forms.CharField(initial='{}')
    locations = forms.TypedMultipleChoiceField(
        choices=[], coerce=str,
        label='Container Locations', required=False
    )

    class Meta:
        model = Group
        fields = ['shipment','id','name','sample_count','priority','kind','energy','absorption_edge','plan','comments','locations']
        widgets = {
            'comments': forms.Textarea(attrs={'rows': "4"}),
            'priority': forms.TextInput(attrs={'readonly': True}),
            'shipment': forms.HiddenInput()
        }

    def __init__(self, *args, **kwargs):
        super(ShipmentGroupForm, self).__init__(*args, **kwargs)

        locations = []
        containers = self.initial.pop('containers')
        for c in containers:
            kind = ContainerType.objects.get(pk=int(c[1]))
            locations.extend([('{2};{0};{1}'.format(c[0], l, c[1]),'{2};{0};{1}'.format(c[0], l, c[1])) for l in kind.container_locations.values_list('name',flat=True)])

        self.fields['locations'].choices = locations

        self.helper = FormHelper()
        self.helper.layout = Layout(
            Div(Field('shipment')),
            Div(
                Div(
                    self.help_text(),
                    css_class="col-xs-12"
                ),
                css_class="row"
            ),
            Div(
                Div(
                    Div(
                        Div(
                            Div(
                                Div(
                                    Div(
                                        Div(
                                            Div(
                                                HTML("""<a title="Edit more group details" href="#group-details-{rowcount}" data-toggle="collapse" class="inline-btn btn btn-info btn-collapse"><i class="fa fa-fw fa-angle-double-right"></i></a>"""),
                                                css_class="col-xs-1"
                                            ),
                                            Div(
                                                PrependedText('priority', '<a title="Drag to change group priority" class="disabled btn btn-info btn-addon move"><i class="fa fa-fw ti ti-split-v"></i></a>', css_id="priority"),
                                                css_class="col-xs-2",
                                            ),
                                            Div(Field('id', css_id="id")),
                                            Div(Field('name', css_id="name"), css_class="col-xs-4"),
                                            Div(
                                                PrependedText('sample_count', '<a title="Sample Seat Selection" onclick="toggleFlip(this, true);" class="disabled btn btn-info btn-addon"><i class="fa fa-fw fa-braille"></i></a>', css_class="addon-btn-holder", css_id="sample_count"),
                                                css_class="col-xs-4"
                                            ),
                                            Div(

                                                HTML("""<a title="Remove Group" class="pull-right inline-btn remove btn btn-danger"><i class="fa fa-fw fa-remove"></i></a>"""),
                                                css_class="col-xs-1"
                                            ),
                                            css_class="row"
                                        ),
                                        Div(
                                            Div(
                                                TabHolder(
                                                    Tab('Experiment Parameters',
                                                        Div(
                                                            Div(
                                                                Div(Field('kind', css_class="tab-chosen chosen-select", css_id="kind"), css_class="col-xs-6"),
                                                                Div(Field('plan', css_class="tab-chosen chosen-select", css_id="plan"), css_class="col-xs-6"),
                                                                Div(Field('energy', css_id="energy"), css_class="col-xs-6"),
                                                                Div(Field('absorption_edge', css_id="absorption_edge"), css_class="col-xs-6"),
                                                                css_class="col-xs-12"
                                                            ),
                                                            css_class="row"
                                                        )
                                                    ),
                                                    Tab('Comments',
                                                        Div(
                                                            Div(
                                                                Field('comments', css_id="comments"),
                                                                css_class="col-xs-12"
                                                            ),
                                                            css_class="row"
                                                        )
                                                    )
                                                )
                                            ),
                                            css_class="col-xs-12 collapse",
                                            css_id="group-details-{rowcount}"
                                        ),
                                    ),
                                    css_class="col-xs-12 template repeat-row list-group-item"
                                ),
                                css_class="repeat-group repeat-container list-group list-group-hover",
                            ),
                            Div(
                                HTML("""<br/>"""),
                                Button('Add', type='add', value='Add Another', css_class="btn btn-success add"),
                                css_class="col-xs-12"
                            ),
                            css_class="repeat-wrapper"
                        ),
                        css_class='repeat front'
                    ),
                    Div(
                        Div(
                            Div(
                                HTML("""<h4><strong>Group "<span class="group-name"></span>"</strong> | Select sample locations in your containers</h4>"""),
                                css_class="col-xs-12"
                            ),
                            Field('sample_locations', type="hidden"),
                            Field('locations', template="users/forms/layout-container.html"),
                            css_class="col-xs-12"
                        ),
                        Div(
                            Div(
                                Button('Back', value="Back", type="back", onclick="toggleFlip(false);", css_class="btn btn-info"),
                                css_class="pull-right"
                            ),
                            css_class="back-actions col-xs-12"
                        ),
                        css_class="back"
                    ),
                    css_class="flipper row"
                ),
                css_class="flip-container"
            )
        )

        if self.initial.get('shipment'):
            groups = self.initial['shipment'].group_set.order_by('priority')
            self.repeated_data = {}
            self.repeated_data['name_set'] = [str(group.name) for group in groups]
            self.repeated_data['priority_set'] = [group.priority for group in groups]
            self.repeated_data['id_set'] = [group.pk for group in groups]
            self.repeated_data['sample_count_set'] = [group.sample_count for group in groups]
            self.helper.layout.append(
                FormActions(
                    Div(
                        StrictButton('Save', type='submit', name="submit", value='submit', css_class='btn btn-primary'),
                        css_class='pull-right'
                    ),
                    css_class="form-actions"
                ))

            self.helper.title = "Add Groups to Shipment"
            self.helper.form_action = reverse_lazy('shipment-add-groups', kwargs={'pk': self.initial['shipment'].pk})


    def help_text(self):
        if self.initial.get('shipment'):
            return Div(HTML("""How do you want to group your samples?<br/>
                               <strong>Be careful! Removing a group will also remove any samples in the group</strong>""")
                       )
        else:
            return Div(HTML("""<h4>Step 3: Add the groups of samples you will be working on!</h4>"""),
                       HTML("""<small>How do you want to group your samples?
                               Don't worry, you can always add more groups later.</small>"""),)


    def clean(self):
        self.repeated_data = {}
        self.cleaned_data = super(ShipmentGroupForm, self).clean()
        for field in self.Meta.fields:
            if 'groups-{}'.format(field) in self.data:
                self.cleaned_data['{}_set'.format(field)] = self.data.getlist('groups-{}'.format(field))
            else:
                self.cleaned_data['{}_set'.format(field)] = self.data.getlist(field)
        if not self.is_valid():
            for k, v in self.cleaned_data.items():
                if type(v) == type([]):
                    self.repeated_data[k] = [str(e) for e in v]
        return self.cleaned_data


class ConfirmDeleteForm(BaseForm):
    project = forms.ModelChoiceField(queryset=Project.objects.all(), widget=forms.HiddenInput)
    cascade = objforms.widgets.LargeCheckBoxField(required=False,
                                                  label='Keep all child objects associated with this object.')

    class Meta:
        fields = ('project', 'cascade')


class LimsBasicForm(OrderedForm):
    project = forms.ModelChoiceField(queryset=Project.objects.all(), widget=forms.HiddenInput)

    class Meta:
        model = Project
        fields = ('project',)


class ComponentForm(OrderedForm):
    project = forms.ModelChoiceField(queryset=Project.objects.all(), widget=forms.HiddenInput)
    shipment = forms.ModelChoiceField(queryset=Shipment.objects.all(), widget=forms.HiddenInput)
    name = objforms.widgets.LargeCharField(required=True)
    description = objforms.widgets.LargeTextField(required=False)
    label = objforms.widgets.LargeCheckBoxField(required=False, label="Print Label")

    class Meta:
        model = Component
        fields = ('project', 'shipment', 'name', 'label', 'description',)

    def clean_name(self):
        return self.cleaned_data['name']


class GroupForm(OrderedForm):
    project = forms.ModelChoiceField(queryset=Project.objects.all(), widget=forms.HiddenInput)
    name = objforms.widgets.LargeCharField(required=True)
    kind = objforms.widgets.LeftHalfChoiceField(label='Type', choices=Group.EXP_TYPES, required=True)
    plan = objforms.widgets.RightHalfChoiceField(label='Plan', choices=Group.EXP_PLANS,
                                                 required=True, initial=Group.EXP_PLANS.COLLECT_FIRST_GOOD)
    resolution = forms.FloatField(label='Desired Resolution', widget=objforms.widgets.LeftHalfInput, required=False)
    delta_angle = forms.FloatField(widget=objforms.widgets.RightHalfInput, required=False)
    multiplicity = forms.FloatField(widget=objforms.widgets.LeftHalfInput, required=False)
    total_angle = forms.FloatField(label='Angle Range', widget=objforms.widgets.RightHalfInput, required=False)
    i_sigma = forms.FloatField(label='Desired I/Sigma', widget=objforms.widgets.LeftHalfInput, required=False)
    r_meas = forms.FloatField(label='Desired R-factor', widget=objforms.widgets.RightHalfInput, required=False)
    energy = forms.DecimalField(max_digits=10, decimal_places=4, widget=objforms.widgets.LeftHalfInput, required=False)
    absorption_edge = objforms.widgets.RightHalfCharField(required=False)
    comments = objforms.widgets.CommentField(required=False,
                                             help_text=Sample.HELP['comments'])

    class Meta:
        model = Group
        fields = ('project', 'name', 'kind', 'plan', 'resolution',
                  'delta_angle', 'multiplicity', 'total_angle', 'i_sigma', 'r_meas',
                  'energy', 'absorption_edge', 'comments')


class CommentsForm(forms.Form):
    comments = objforms.widgets.CommentField(required=False,
                                             help_text="Comments entered here will be visible to staff at the CMCF. You can use Restructured Text markup for formatting.")

    class Meta:
        fields = ('comments',)

    def is_valid(self):
        super(CommentsForm, self).is_valid()
        return self.cleaned_data.get('comments', None)
