from django import forms
from django.forms.utils import ErrorList
from django.forms import inlineformset_factory
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
from crispy_forms.bootstrap import Accordion, AccordionGroup, Tab, TabHolder, PrependedText
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


class ProjectForm(OrderedForm):
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
    contact_fax = forms.CharField(widget=objforms.widgets.RightHalfInput, required=False)
    show_archives = objforms.widgets.LeftCheckBoxField(required=False)
    updated = forms.CharField(widget=forms.HiddenInput())

    class Meta:
        model = Project
        fields = ('contact_person', 'contact_email',
                  'carrier', 'account_number', 'organisation', 'department', 'address',
                  'city', 'province', 'postal_code', 'country', 'contact_phone', 'contact_fax', 'show_archives',
                  'updated')

    def clean_updated(self):
        """
        Toggle updated value to True when the profile is saved for the first time.
        """
        return True

    def restrict_by(self, field_name, id):
        pass


class NewUserForm(OrderedForm):
    username = forms.CharField(required=False, widget=objforms.widgets.LeftHalfInput, help_text="The username is optional, it will be generated automatically if not provided")
    password = forms.CharField(required=False, widget=objforms.widgets.RightHalfInput, help_text="The password is optional, a random password will be generated automatically if not provided")

    first_name = forms.CharField(widget=objforms.widgets.LeftHalfInput, required=True)
    last_name = forms.CharField(widget=objforms.widgets.RightHalfInput, required=True)
    contact_email = forms.EmailField(widget=objforms.widgets.LargeInput, max_length=100, required=True)

    organisation = objforms.widgets.LargeCharField(required=True)
    department = objforms.widgets.LargeCharField(required=False)
    address = objforms.widgets.LargeCharField(required=True)
    city = forms.CharField(widget=objforms.widgets.LeftHalfInput, required=True)
    province = forms.CharField(widget=objforms.widgets.RightHalfInput, required=True)
    postal_code = forms.CharField(widget=objforms.widgets.LeftHalfInput, required=False)
    country = forms.CharField(widget=objforms.widgets.RightHalfInput, required=True)

    class Meta:
        model = Project
        fields = ('first_name', 'last_name', 'username', 'password',  'contact_email',
                  'organisation', 'department', 'address',
                  'city', 'province', 'postal_code', 'country')

    def clean(self):
        data = self.cleaned_data
        data['contact_person'] = u'{} {}'.format(data['first_name'], data['last_name'])
        return data


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

    def __init__(self, *args, **kwargs):
        super(ShipmentSendForm, self).__init__(*args, **kwargs)
        self.helper = FormHelper()
        self.helper.title = u"Add Shipping Information"
        self.helper.form_action = reverse_lazy('shipment-send', kwargs={'pk': self.instance.pk})
        self.helper.layout = Layout(
            'carrier','tracking_code','comments',
            FormActions(
                Div(
                    StrictButton('Revert', type='reset', value='Reset', css_class="btn btn-default"),
                    StrictButton('Save', type='submit', name="submit", value='save', css_class='btn btn-primary'),
                    css_class='pull-right'
                ),
            )
        )

# class ShipmentAddContainerForm(forms.ModelForm):
#     target = forms.ModelChoiceField(queryset=Container.objects.all())
#
#     class Meta:
#         model = Shipment
#         fields = ['target',]

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
            'carrier','return_code','staff_comments',
            FormActions(
                Div(
                    StrictButton('Revert', type='reset', value='Reset', css_class="btn btn-default"),
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
                    StrictButton('Save', type='submit', name="submit", value='save', css_class='btn btn-primary'),
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
                HTML("<hr/>"),
                Div(
                    StrictButton('Revert', type='reset', value='Reset', css_class="btn btn-default"),
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
    class Meta:
        model = Container
        fields = ('name', 'kind')

    def __init__(self, *args, **kwargs):
        super(ShipmentContainerForm, self).__init__(*args, **kwargs)

        repeated_fields = ['name','kind']
        for f in repeated_fields:
            self.fields['{}_set'.format(f)] = forms.CharField(required=False)

        self.helper = FormHelper()
        self.helper.layout = Layout(
            Div(
                Div(
                    HTML("""<h4>Step 2: Add the containers you are bringing!</h4>"""),
                    HTML("""<small>Use labels that are visible on your containers.
                            Don't worry, you can always add more containers later.</small>"""),
                    css_class="col-xs-12"
                ),
                css_class="row"
            ),
            Div(
                Div(
                    Div(
                        Div(
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

    def clean(self):
        self.repeated_data = {}
        self.cleaned_data = super(ShipmentContainerForm, self).clean()
        for field in self.Meta.fields:
            self.cleaned_data['{}_set'.format(field)] = self.data.getlist('containers-0-{}'.format(field))
            self.fields[field].initial = self.cleaned_data['{}_set'.format(field)][0]
        if not self.is_valid():
            for k, v in self.cleaned_data.items():
                if type(v) == type([]):
                    self.repeated_data[k] = [str(e) for e in v]
        return self.cleaned_data

ContainerFormSet = inlineformset_factory(Shipment, Container, form=ShipmentContainerForm, extra=1)

class AddContainerForm(ShipmentContainerForm):
    def __init__(self, *args, **kwargs):
        super(AddContainerForm, self).__init__(*args, **kwargs)
        self.helper.layout.append(
            FormActions(
                Div(
                    StrictButton('Revert', type='reset', value='Reset', css_class="btn btn-default"),
                    StrictButton('Save', type='submit', name="submit", value='save', css_class='btn btn-primary'),
                    css_class='pull-right'
                ),
            )
        )
        self.helper.title = "Add Containers to Shipment"

        self.repeated_data = {}
        # self.cleaned_data = super(ShipmentContainerForm, self).clean()
        # for field in self.Meta.fields:
        #     self.cleaned_data['{}_set'.format(field)] = self.data.getlist('containers-0-{}'.format(field))
        #     self.fields[field].initial = self.cleaned_data['{}_set'.format(field)][0]
        # if not self.is_valid():
        #     for k, v in self.cleaned_data.items():
        #         if type(v) == type([]):
        #             self.repeated_data[k] = [str(e) for e in v]
        # return self.cleaned_data


class ShipmentGroupForm(forms.ModelForm):
    sample_locations = forms.CharField(initial='{}')
    locations = forms.TypedMultipleChoiceField(
        choices=[], coerce=str,
        label='Container Locations', required=False
    )

    class Meta:
        model = Group
        fields = ['name','sample_count','priority','kind','energy','absorption_edge','plan','comments','locations']
        widgets = {
            'comments': forms.Textarea(attrs={'rows': "4"}),
            'priority': forms.TextInput(attrs={'readonly': True})
        }

    def __init__(self, *args, **kwargs):
        super(ShipmentGroupForm, self).__init__(*args, **kwargs)

        containers = self.initial.get('containers', [])
        locations = []
        for c in containers:
            kind = ContainerType.objects.get(pk=int(c[1]))
            locations.extend([('{2};{0};{1}'.format(c[0], l, c[1]),'{2};{0};{1}'.format(c[0], l, c[1])) for l in kind.container_locations.values_list('name',flat=True)])

        self.fields['locations'].choices = locations

        self.helper = FormHelper()
        self.helper.layout = Layout(
            Div(
                Div(
                    HTML("""<h4>Step 3: Add the groups of samples you will be working on!</h4>"""),
                    HTML("""<small>How do you want to keep track of your different projects?
                        Don't worry, you can always add more groups later.</small>"""),
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
                                                PrependedText('priority', '<a title="Drag to change group priority" class="disabled btn btn-info btn-addon move"><i class="fa fa-fw ti ti-split-v"></i></a>'),
                                                css_class="col-xs-2"
                                            ),
                                            Div(Field('name'), css_class="col-xs-4"),
                                            Div(
                                                PrependedText('sample_count', '<a title="Sample Seat Selection" onclick="toggleFlip(this, true);" class="disabled btn btn-info btn-addon"><i class="fa fa-fw fa-braille"></i></a>', css_class="addon-btn-holder"),
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
                                                                Div(Field('kind', css_class="tab-chosen chosen-select"), css_class="col-xs-6"),
                                                                Div(Field('plan', css_class="tab-chosen chosen-select"), css_class="col-xs-6"),
                                                                Div(Field('energy'), css_class="col-xs-6"),
                                                                Div(Field('absorption_edge'), css_class="col-xs-6"),
                                                                css_class="col-xs-12"
                                                            ),
                                                            css_class="row"
                                                        )
                                                    ),
                                                    Tab('Comments',
                                                        Div(
                                                            Div(
                                                                Div(Field('comments'), css_class="col-xs-12"),
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


    def clean(self):
        self.cleaned_data = super(ShipmentGroupForm, self).clean()
        for field in self.Meta.fields:
            self.cleaned_data['{}_set'.format(field)] = self.data.getlist('groups-0-{}'.format(field))
        return self.cleaned_data


GroupFormSet = inlineformset_factory(Shipment, Group, form=ShipmentGroupForm, extra=1)

class AddGroupForm(ShipmentGroupForm):
    def __init__(self, *args, **kwargs):
        super(AddGroupForm, self).__init__(*args, **kwargs)
        self.helper.layout.append(
            FormActions(
                Div(
                    StrictButton('Revert', type='reset', value='Reset', css_class="btn btn-default"),
                    StrictButton('Save', type='submit', name="submit", value='save', css_class='btn btn-primary'),
                    css_class='pull-right'
                ),
            )
        )
        self.helper.title = "Add Groups to Shipment"


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


#
# class ShipmentSendForm(OrderedForm):
#     project = forms.ModelChoiceField(queryset=Project.objects.all(), widget=forms.HiddenInput)
#     carrier = forms.ModelChoiceField(
#         queryset=Carrier.objects.all(),
#         widget=objforms.widgets.LargeSelect,
#         required=True, initial=''
#     )
#     tracking_code = objforms.widgets.LargeCharField(required=False)
#     comments = objforms.widgets.CommentField(required=False)
#
#     class Meta:
#         model = Shipment
#         fields = ('project', 'carrier', 'tracking_code', 'comments')
#
#     def warning_message(self):
#         shipment = self.instance
#         if shipment:
#             for crystal in shipment.project.sample_set.filter(container__dewar__shipment__exact=shipment):
#                 if not crystal.experiment:
#                     return 'Crystal "%s" is not associated with any Experiments. Sending the Shipment will create a ' \
#                            'default "Screen and confirm" Experiment and assign all unassociated Crystals. Close this window ' \
#                            'to setup the Experiment manually.' % crystal.name
#
#     def clean_tracking_code(self):
#         cleaned_data = self.cleaned_data['tracking_code']
#         # put this here instead of .clean() because objforms does not display form-wide error messages
#         if self.instance.status != Shipment.STATES.DRAFT:
#             raise forms.ValidationError('Shipment already sent.')
#         return cleaned_data
#
#     def restrict_by(self, field_name, id):
#         pass


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


class FeedbackForm(OrderedForm):
    project = forms.ModelChoiceField(queryset=Project.objects.all(), widget=forms.HiddenInput)
    contact_name = objforms.widgets.LargeCharField(label='Name (optional)', required=False)
    contact = forms.EmailField(widget=objforms.widgets.LargeInput, label="Email Address (optional)", required=False)
    category = forms.ChoiceField(choices=Feedback.TYPE, widget=objforms.widgets.LargeSelect)
    message = objforms.widgets.LargeTextField(required=True)

    class Meta:
        model = Feedback
        fields = ('project', 'contact_name', 'contact', 'category', 'message')


class CommentsForm(forms.Form):
    comments = objforms.widgets.CommentField(required=False,
                                             help_text="Comments entered here will be visible to staff at the CMCF. You can use Restructured Text markup for formatting.")

    class Meta:
        fields = ('comments',)

    def is_valid(self):
        super(CommentsForm, self).is_valid()
        return self.cleaned_data.get('comments', None)
