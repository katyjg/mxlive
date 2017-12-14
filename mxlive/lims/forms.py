from django import forms
from django.core.urlresolvers import reverse_lazy

from models import *
import re

from crispy_forms.helper import FormHelper
from crispy_forms.layout import Layout, HTML, Div, Field, Button
from crispy_forms.bootstrap import Accordion, AccordionGroup, Tab, TabHolder, PrependedText, AppendedText, InlineField
from crispy_forms.bootstrap import StrictButton, FormActions

disabled_widget = forms.HiddenInput(attrs={'readonly': True})


class ProjectForm(forms.ModelForm):

    class Meta:
        model = Project
        fields = ('contact_person', 'contact_email', 'carrier', 'account_number', 'organisation', 'department',
                  'address', 'city', 'province', 'postal_code', 'country', 'contact_phone')

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
            Div(
                Div('contact_person', css_class='col-xs-12'),
                css_class="row"
            ),
            Div(
                Div('contact_email', css_class='col-xs-6'),
                Div('contact_phone', css_class='col-xs-6'),
                css_class="row"
            ),
            Div(
                Div(Field('carrier', css_class="chosen"), css_class='col-xs-6'),
                Div('account_number', css_class='col-xs-6'),
                css_class="row"
            ),
            Div(
                Div('organisation', css_class='col-xs-12'),
                css_class="row"
            ),
            Div(
                Div('department', css_class='col-xs-12'),
                css_class="row"
            ),
            Div(
                Div('address', css_class='col-xs-12'),
                css_class="row"
            ),
            Div(
                Div('city', css_class='col-xs-6'),
                Div('province', css_class='col-xs-6'),
                css_class="row"
            ),
            Div(
                Div('country', css_class='col-xs-6'),
                Div('postal_code', css_class='col-xs-6'),
                css_class="row"
            ),
            FormActions(
                Div(
                    Div(
                        StrictButton('Revert', type='reset', value='Reset', css_class="btn btn-default"),
                        StrictButton('Save', type='submit', name="submit", value='submit', css_class='btn btn-primary'),
                        css_class='pull-right'
                    ),
                    css_class="col-xs-12"
                ),
                css_class="row form-action"
            )
        )


class NewProjectForm(forms.ModelForm):
    password = forms.CharField(required=False, help_text='A password will be auto-generated for this account')

    class Meta:
        model = Project
        fields = ('first_name', 'last_name', 'contact_person', 'contact_email', 'contact_phone', 'username')

    def __init__(self, *args, **kwargs):
        super(NewProjectForm, self).__init__(*args, **kwargs)

        if getattr(settings, 'LDAP_SEND_EMAILS', False):
            self.fields['password'].help_text += ' and sent to staff once this form is submitted'

        self.helper = FormHelper()
        self.helper.title = u"Create New User Account"
        self.helper.form_action = reverse_lazy('new-project')
        self.helper.layout = Layout(
        Div(
            Div('username', css_class='col-xs-6'),
            Div(Field('password', disabled=True), css_class="col-xs-6"),
            css_class="row"
        ),
        Div(
            Div('first_name', css_class='col-xs-6'),
            Div('last_name', css_class='col-xs-6'),
            css_class="row"
        ),
        Div(
            Div('contact_person', css_class='col-xs-12'),
                css_class="row"
            ),
        Div(
            Div('contact_email', css_class='col-xs-6'),
            Div('contact_phone', css_class='col-xs-6'),
            css_class="row"
        ),
            FormActions(
                Div(
                    Div(
                        StrictButton('Save', type='submit', name="submit", value='submit', css_class='btn btn-primary'),
                        css_class='pull-right'
                    ),
                    css_class="col-xs-12"
                ),
                css_class="form-action row"
            )
        )


class ShipmentForm(forms.ModelForm):

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
            'project', 'name', 'comments',
            FormActions(
                Div(
                    Div(
                        StrictButton('Revert', type='reset', value='Reset', css_class="btn btn-default"),
                        StrictButton('Save', type='submit', name="submit", value='save', css_class='btn btn-primary'),
                        css_class='pull-right'
                    ),
                    css_class="col-xs-12"
                ),
                css_class="form-action row"
            )
        )

    def clean(self):
        cleaned_data = super(ShipmentForm, self).clean()
        if cleaned_data['project'].shipment_set.filter(name__iexact=cleaned_data.get('name', ''))\
                .exclude(pk=self.instance.pk).exists():
            self.add_error('name', forms.ValidationError("Shipment with this name already exists"))

    class Meta:
        model = Shipment
        fields = ('project', 'name', 'comments',)
        widgets = {'project': disabled_widget,
                   'comments': forms.Textarea(attrs={'rows': "2"})}


class DewarForm(forms.ModelForm):

    class Meta:
        model = Dewar
        fields = ('staff_comments', )
        widgets = {'staff_comments': forms.Textarea(attrs={'rows': "3"})}

    def __init__(self, *args, **kwargs):
        super(DewarForm, self).__init__(*args, **kwargs)

        self.helper = FormHelper()
        self.helper.form_action = reverse_lazy('dewar-edit', kwargs={'pk': self.instance.pk})
        self.helper.title = u"Staff Comments for {} Automounter".format(self.instance.beamline.acronym)
        self.helper.layout = Layout(
            'staff_comments',
            FormActions(
                Div(
                    Div(
                        StrictButton('Revert', type='reset', value='Reset', css_class="btn btn-default"),
                        StrictButton('Save', type='submit', name="submit", value='save', css_class='btn btn-primary'),
                        css_class='pull-right'
                    ),
                    css_class="col-xs-12"
                ),
                css_class="form-action row"
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
            Div(
                Div('name', css_class='col-xs-6'),
                Div('barcode', css_class='col-xs-6'),
                Div('comments', css_class='col-xs-12'),
                css_class="row"
            ),
            FormActions(
                Div(
                    Div(
                        StrictButton('Revert', type='reset', value='Reset', css_class="btn btn-default"),
                        StrictButton('Save', type='submit', name="submit", value='save', css_class='btn btn-primary'),
                        css_class='pull-right'
                    ),
                    css_class="col-xs-12"
                ),
                css_class="form-action row"
            )
        )

    def clean(self):
        if 'name' in self.cleaned_data:
            if not re.compile('^[a-zA-Z0-9-_]+[\w]+$').match(self.cleaned_data['name']):
                self._errors['name'] = self.error_class(['Name cannot contain any spaces or special characters'])
        return self.cleaned_data

    class Meta:
        model = Sample
        fields = ('name', 'barcode', 'comments')
        widgets = {
            'comments': forms.Textarea(attrs={'rows': "4"}),
        }


class SampleAdminForm(forms.ModelForm):

    def __init__(self, *args, **kwargs):
        super(SampleAdminForm, self).__init__(*args, **kwargs)
        pk = self.instance.pk

        self.helper = FormHelper()
        self.helper.title = u"Add Staff Comments to Sample"
        self.helper.form_action = reverse_lazy('sample-admin-edit', kwargs={'pk': pk})

        self.helper.layout = Layout(
            Div('staff_comments', css_class='col-xs-12'),
            FormActions(
                Div(
                    Div(
                        StrictButton('Revert', type='reset', value='Reset', css_class="btn btn-default"),
                        StrictButton('Save', type='submit', name="submit", value='save', css_class='btn btn-primary'),
                        css_class='pull-right'
                    ),
                    css_class="col-xs-12"
                ),
                css_class="form-action row"
            )
        )

    class Meta:
        model = Sample
        fields = ('staff_comments', )
        widgets = {
            'staff_comments': forms.Textarea(attrs={'rows': "4"}),
        }



class ShipmentSendForm(forms.ModelForm):
    components = forms.ModelMultipleChoiceField(label='Items included in shipment',
                                                queryset=ComponentType.objects.all(),
                                                required=False)

    class Meta:
        model = Shipment
        fields = ('carrier', 'tracking_code', 'comments')
        widgets = {
            'comments': forms.Textarea(attrs={'rows': "4"}),
        }

    def __init__(self, *args, **kwargs):
        super(ShipmentSendForm, self).__init__(*args, **kwargs)
        errors = Div()
        if self.instance.shipping_errors():
            errors = Div(
                Div(
                    HTML('/ '.join(self.instance.shipping_errors())),
                    css_class="panel-heading"
                ),
                css_class="panel panel-warning"
            )
        self.helper = FormHelper()
        self.helper.title = u"Add Shipping Information"
        self.helper.form_action = reverse_lazy('shipment-send', kwargs={'pk': self.instance.pk})
        self.helper.layout = Layout(
            errors,
            Div(
                Div(Field('carrier', css_class="chosen"), css_class="col-xs-6"),
                Div('tracking_code', css_class="col-xs-6"),
                Div(Field('components', css_class="chosen"), css_class="col-xs-12"),
                Div('comments', css_class="col-xs-12"),
                css_class="row"
            ),
            FormActions(
                Div(
                    Div(
                        StrictButton('Save', type='submit', name="submit", value='save', css_class='btn btn-primary'),
                        css_class='pull-right'
                    ),
                    css_class="col-xs-12"
                ),
                css_class="form-action row"
            )
        )


class ShipmentReturnForm(forms.ModelForm):
    loaded = forms.BooleanField(label="I have removed these containers from the automounter(s)")

    class Meta:
        model = Shipment
        fields = ['carrier', 'return_code', 'staff_comments']

    def __init__(self, *args, **kwargs):
        super(ShipmentReturnForm, self).__init__(*args, **kwargs)
        if self.instance.container_set.filter(parent__isnull=False):
            self.fields['loaded'].label += ": {}".format(','.join(self.instance.container_set.filter(parent__isnull=False).values_list('name', flat=True)))
        else:
            self.fields['loaded'].initial = True
            self.fields['loaded'].widget = forms.HiddenInput()
        self.helper = FormHelper()
        self.helper.title = u"Add Shipping Information"
        self.helper.form_action = reverse_lazy('shipment-return', kwargs={'pk': self.instance.pk})
        self.helper.layout = Layout(
            Div(
                Div(Field('loaded'), css_class="col-xs-12"),
                css_class="row"
            ),
            Div(
                Div(Field('carrier', css_class="chosen"), css_class="col-xs-6"),
                Div('return_code', css_class="col-xs-6"),
                Div('staff_comments', css_class="col-xs-12"),
                css_class="row"
            ),
            FormActions(
                Div(
                    Div(
                        StrictButton('Save', type='submit', name="submit", value='save', css_class='btn btn-primary'),
                        css_class='pull-right'
                    ),
                    css_class="col-xs-12"
                ),
                css_class="form-action row"
            )
        )


class ShipmentRecallSendForm(forms.ModelForm):
    components = forms.ModelMultipleChoiceField(label='Items included in shipment',
                                                queryset=ComponentType.objects.all(),
                                                required=False)

    class Meta:
        model = Shipment
        fields = ['carrier', 'tracking_code', 'comments']

    def __init__(self, *args, **kwargs):
        super(ShipmentRecallSendForm, self).__init__(*args, **kwargs)
        self.helper = FormHelper()
        self.helper.title = u"Update Shipping Information"
        self.helper.form_action = reverse_lazy('shipment-update-send', kwargs={'pk': self.instance.pk})
        self.helper.layout = Layout(
            Div(
                Div(Field('carrier', css_class="chosen"), css_class="col-xs-6"),
                Div('tracking_code', css_class="col-xs-6"),
                Div(Field('components', css_class="chosen"), css_class="col-xs-12"),
                Div('comments', css_class="col-xs-12"),
                css_class="row"
            ),
            FormActions(
                Div(
                    Div(
                        StrictButton('Unsend', type='recall', value='Recall', css_class="btn btn-danger"),
                        css_class='pull-left'
                    ),
                    Div(
                        StrictButton('Save', type='submit', name="submit", value='save', css_class='btn btn-primary'),
                        css_class='pull-right'
                    ),
                    css_class="col-xs-12"
                ),
                css_class="form-action row"
            )
        )


class ShipmentRecallReturnForm(forms.ModelForm):
    class Meta:
        model = Shipment
        fields = ['carrier', 'return_code', 'staff_comments']

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
                    Div(
                        StrictButton('Unsend', type='recall', value='Recall', css_class="btn btn-danger"),
                        css_class='pull-left'
                    ),
                    Div(
                        StrictButton('Save', type='submit', name="submit", value='save', css_class='btn btn-primary'),
                        css_class='pull-right'
                    ),
                    css_class="col-xs-12"
                ),
                css_class="form-action row"
            )
        )


class ShipmentReceiveForm(forms.ModelForm):

    class Meta:
        model = Shipment
        fields = ['storage_location', 'staff_comments']

    def __init__(self, *args, **kwargs):
        super(ShipmentReceiveForm, self).__init__(*args, **kwargs)
        self.helper = FormHelper()
        self.helper.title = u"Receive Shipment?"
        self.helper.form_action = reverse_lazy('shipment-receive', kwargs={'pk': self.instance.pk})
        self.helper.layout = Layout(
            'storage_location', 'staff_comments',
            FormActions(
                Div(
                    Div(
                        StrictButton('Save', type='submit', name="submit", value='submit', css_class='btn btn-primary'),
                        css_class='pull-right'
                    ),
                    css_class="col-xs-12"
                ),
                css_class="form-action row"
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
                    Div(
                        StrictButton('Save', type='submit', name="submit", value='save', css_class='btn btn-primary'),
                        css_class='pull-right'
                    ),
                    css_class="col-xs-12"
                ),
                css_class="row"
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
            'project', 'name', 'shipment', 'comments',
            FormActions(
                Div(
                    Div(
                        StrictButton('Revert', type='reset', value='Reset', css_class="btn btn-default"),
                        StrictButton('Save', type='submit', name="submit", value='submit', css_class='btn btn-primary'),
                        css_class='pull-right'
                    ),
                    css_class="col-xs-12"
                ),
                css_class=" form-action row"
            )
        )

    def clean_kind(self):
        """ Ensures that the 'kind' of Container cannot be changed when Crystals are associated with it """
        cleaned_data = self.cleaned_data
        if self.instance.pk:
            if self.instance.kind != cleaned_data['kind']:
                if self.instance.num_samples() > 0:
                    raise forms.ValidationError('Cannot change kind of Container when Samples are associated')
        return cleaned_data['kind']

    class Meta:
        model = Container
        fields = ['project', 'name', 'shipment', 'comments']
        widgets = {'project': disabled_widget}


class GroupForm(forms.ModelForm):

    def __init__(self, *args, **kwargs):
        super(GroupForm, self).__init__(*args, **kwargs)
        pk = self.instance.pk

        self.helper = FormHelper()
        if pk:
            self.helper.title = u"Edit Group"
            self.helper.form_action = reverse_lazy("group-edit", kwargs={'pk': pk})
        else:
            self.helper.title = u"Create New Group"
            self.helper.form_action = reverse_lazy("group-new")
        self.helper.layout = Layout(
            'project',
            Div(
                Div('name', css_class="col-xs-12"),
                css_class="row"
            ),
            Div(
                Div(Field('kind', css_class="tab-chosen chosen-select",
                          css_id="kind"), css_class="col-xs-6"),
                Div(Field('plan', css_class="tab-chosen chosen-select",
                          css_id="plan"), css_class="col-xs-6"),
                css_class="row"
            ),
            Div(
                Div(Field('absorption_edge', css_id="absorption_edge"),
                    css_class="col-xs-6"),
                Div(Field('resolution', css_id="resolution"),
                    css_class="col-xs-6"),
                Div('comments', css_class="col-xs-12"),
                css_class="row"
            ),
            FormActions(
                Div(
                    Div(
                        StrictButton('Save', type='submit', name="submit", value='submit', css_class='btn btn-primary'),
                        css_class='pull-right'
                    ),
                    css_class="col-xs-12"
                ),
                css_class="form-action row"
            )
        )

    def clean_name(self):
        name = self.cleaned_data.get('name')
        if self.instance.shipment.group_set.filter(name=name).exclude(pk=self.instance.pk).exists():
            self.add_error('name', forms.ValidationError("Groups in a shipment must each have a unique name"))
        return name

    class Meta:
        model = Group
        fields = ('project', 'name', 'kind', 'plan', 'resolution', 'absorption_edge', 'comments')
        widgets = {'project': disabled_widget}


class ContainerLoadForm(forms.ModelForm):

    def __init__(self, *args, **kwargs):
        super(ContainerLoadForm, self).__init__(*args, **kwargs)

        self.fields['parent'].queryset = self.fields['parent'].queryset.filter(
            kind__in=self.instance.accepted_by())


        self.helper = FormHelper()
        self.helper.title = u"Move Container {}".format(self.instance)
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
                        StrictButton('Unload', type="submit", name="unload", value='Unload', css_class='pull-left btn btn-danger'),
                        StrictButton('Save', type='submit', name="submit", value='submit', css_class='pull-right btn btn-primary'),
                    css_class="col-xs-12"
                ),
                css_class="row form-action"
            )
        )

    def clean(self):
        if self.data.get('submit') == 'Unload':
            self.cleaned_data.update({'location': None, 'parent': None})
        else:
            if self.cleaned_data['location']:
                if self.cleaned_data['parent'].children.exclude(pk=self.instance.pk).filter(location=self.cleaned_data['location']).exists():
                    self.add_error(None, forms.ValidationError("Container is already loaded in that location"))

        return self.cleaned_data

    class Meta:
        model = Container
        fields = ['parent', 'location']


class EmptyContainers(forms.ModelForm):
    parent = forms.ModelChoiceField(queryset=Container.objects.all(), widget=forms.HiddenInput)

    class Meta:
        model = Project
        fields = []

    def __init__(self, *args, **kwargs):
        super(EmptyContainers, self).__init__(*args, **kwargs)

        self.helper = FormHelper()
        self.helper.title = u"Remove containers".format(self.instance.username.upper())
        self.helper.form_action = reverse_lazy("empty-containers", kwargs={
            'pk': self.initial['parent'].pk,
            'username': self.instance.username})
        self.helper.layout = Layout(
            Div(HTML("""Any containers owned by {} will be removed from the automounter.""".format(self.instance.username))),
            'parent',
            FormActions(
                Div(
                    StrictButton('Save', type='submit', name="submit", value='submit',
                                 css_class='pull-right btn btn-primary'),
                    css_class="col-xs-12"
                ),
                css_class="row form-action"
            )
        )

class LocationLoadForm(forms.ModelForm):
    child = forms.ModelChoiceField(
        label="Container",
        queryset=Container.objects.filter(status=Container.STATES.ON_SITE))
    container_location = forms.ModelChoiceField(queryset=ContainerLocation.objects.all())

    class Meta:
        model = Container
        fields = ['child', 'container_location']

    def __init__(self, *args, **kwargs):
        super(LocationLoadForm, self).__init__(*args, **kwargs)

        self.fields['child'].queryset = self.fields['child'].queryset.filter(parent__isnull=True).filter(
            kind__in=self.initial['container_location'].accepts.all())

        self.helper = FormHelper()
        self.helper.title = u"Load Container in location {}".format(self.initial['container_location'])
        self.helper.form_action = reverse_lazy("location-load", kwargs={
            'pk': self.instance.pk,
            'location': self.initial['container_location'].name})

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
                    Div(
                        StrictButton('Save', type='submit', name="submit", value='submit', css_class='btn btn-primary'),
                        css_class='pull-right'
                    ),
                    css_class="col-xs-12"
                ),
                css_class="row form-action"
            )
        )


class AddShipmentForm(forms.ModelForm):
    class Meta:
        model = Shipment
        fields = ('name', 'comments', 'project')
        widgets = {
            'comments': forms.Textarea(),
        }

    def __init__(self, *args, **kwargs):
        super(AddShipmentForm, self).__init__(*args, **kwargs)

        if self.initial['project'].is_superuser:
            name_row = Div(
                Div(Field('project', css_class="chosen"), css_class="col-xs-4"),
                Div('name', css_class="col-xs-8"),
                css_class="row"
            )
        else:
            self.fields['project'].widget = forms.HiddenInput()
            name_row = Div(
                Field('project', hidden=True),
                Field('name', css_class="col-xs-12")
            )

        self.helper = FormHelper()
        self.helper.layout = Layout(
            Div(
                Div(
                    HTML("""<h4>Give your shipment a name!</h4>"""),
                    HTML("""<small>This name will be visible to you and staff at the beamline.</small>"""),
                    name_row,
                    Field('comments', rows="2", css_class="col-xs-12"),
                    css_class="col-xs-12"
                ),
                css_class="row"
            ),
            FormActions(
                Div(
                    Div(
                        StrictButton("Continue", type="submit", value="Continue", css_class='btn btn-primary'),
                        css_class="pull-right"
                    ),
                    css_class="col-xs-12"
                ),
                css_class="form-action row"
            )
        )

    def clean(self):
        cleaned_data = super(AddShipmentForm, self).clean()
        if cleaned_data['project'].shipment_set.filter(name__iexact=cleaned_data.get('name', '')).exists():
            self.add_error('name', forms.ValidationError("Shipment with this name already exists"))


class ShipmentContainerForm(forms.ModelForm):
    id = forms.CharField(required=False, widget=forms.HiddenInput)

    class Meta:
        model = Container
        fields = ('shipment', 'id', 'name', 'kind')
        widgets = {'shipment': forms.HiddenInput()}

    def __init__(self, *args, **kwargs):
        super(ShipmentContainerForm, self).__init__(*args, **kwargs)
        self.fields['kind'].initial = ContainerType.objects.get(pk=1)

        self.fields['kind'].queryset = self.fields['kind'].queryset.filter(
            container_locations__in=ContainerLocation.objects.filter(accepts__isnull=True)).distinct()

        self.repeated_fields = ['name', 'kind', 'id']
        self.repeated_data = {}
        for f in self.repeated_fields:
            self.fields['{}_set'.format(f)] = forms.CharField(required=False)

        self.helper = FormHelper()
        action_row = Div(
            Div(
                Div(
                    Button('Add', type='add', value='Add Another', css_class="btn btn-success add"),
                    css_class="pull-left"
                ),
                css_class="col-xs-6"
            ),
            css_class="form-action row"
        )

        if self.initial.get('shipment'):
            self.repeated_data['name_set'] = [str(c.name) for c in self.initial['shipment'].container_set.all()]
            self.repeated_data['id_set'] = [c.pk for c in self.initial['shipment'].container_set.all()]
            self.repeated_data['kind_set'] = [c.kind.pk for c in self.initial['shipment'].container_set.all()]
            self.helper.form_action = reverse_lazy('shipment-add-containers', kwargs={'pk': self.initial['shipment'].pk})
            self.helper.title = 'Add Containers to Shipment'
            action_row.append(Div(
                Div(
                    StrictButton('Save', type='submit', name="submit", value='submit', css_class='btn btn-primary'),
                    css_class="pull-right"
                ),
                css_class="col-xs-6"
            ))
        else:
            action_row.append(Div(
                Div(
                    StrictButton("Continue", type="submit", value="Continue", css_class='btn btn-primary'),
                    css_class="pull-right"
                ),
                css_class="col-xs-6"
            ))

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
                            Div(Field('name', css_id="name"), css_class="col-xs-6 no-left-padding"),
                            Div(Field('kind', css_class="tab-chosen chosen-single", css_id="kind"), css_class="col-xs-5"),
                            Div(
                                HTML("""<a title="Remove Container" class="inline-btn safe-remove btn btn-default">
                                            <i class="fa fa-fw fa-minus"></i></a>"""),
                                HTML("""<a title="Remove Container" class="inline-btn remove btn btn-danger" style="display: none;">
                                            <i class="fa fa-fw fa-remove"></i></a>"""),
                                css_class="col-xs-1 pull-right"),
                            css_class="col-xs-12 template repeat-row list-group-item"
                        ),
                        css_class="row repeat-group repeat-container list-group list-group-hover",
                    ),
                    action_row,
                    css_class="repeat-wrapper"
                ),
                css_class='repeat'
            )
        )

    def help_text(self):
        if self.initial.get('shipment'):
            return Div(HTML("""Use labels that are visible on your containers.<br/>
                               <strong>Be careful! Removing a container will also remove the samples inside</strong><br/>&nbsp;""")
                       )
        else:
            return Div(HTML("""<h4>Add the containers you are bringing!</h4>"""),
                       HTML("""<small>Use labels that are visible on your containers.
                               Don't worry, you can always add more containers later.</small>"""))

    def clean(self):
        self.repeated_data = {}
        cleaned_data = super(ShipmentContainerForm, self).clean()
        for field in self.repeated_fields:
            if 'containers-{}'.format(field) in self.data:
                cleaned_data['{}_set'.format(field)] = self.data.getlist('containers-{}'.format(field))
            else:
                cleaned_data['{}_set'.format(field)] = self.data.getlist(field)
            self.fields[field].initial = cleaned_data['{}_set'.format(field)]
        if not self.is_valid():
            for k, v in cleaned_data.items():
                if isinstance(v, list):
                    self.repeated_data[k] = [str(e) for e in v]
        return cleaned_data


class ShipmentGroupForm(forms.ModelForm):
    id = forms.CharField(required=False, widget=forms.HiddenInput)
    sample_locations = forms.CharField(initial='{}')
    locations = forms.TypedMultipleChoiceField(
        choices=[], coerce=str,
        label='Container Locations', required=False
    )
    containers = forms.ModelMultipleChoiceField(
        queryset=Container.objects.all(),
        required=False
    )
    name = forms.CharField(max_length=50, required=False)
    sample_count = forms.IntegerField(min_value=1, required=False, initial=1)

    class Meta:
        model = Group
        fields = ['shipment', 'id', 'priority', 'kind', 'resolution', 'absorption_edge', 'name', 'sample_count', 'plan', 'comments', 'locations']
        widgets = {
            'comments': forms.Textarea(attrs={'rows': "4"}),
            'priority': forms.TextInput(attrs={'readonly': True}),
            'shipment': forms.HiddenInput()
        }

    def __init__(self, *args, **kwargs):
        super(ShipmentGroupForm, self).__init__(*args, **kwargs)
        user = self.initial.get('user')

        locations = []
        containers = self.initial.get('containers')
        if self.initial.get('shipment'):
            self.fields['containers'].queryset = containers
        else:
            for c in containers:
                kind = ContainerType.objects.get(pk=int(c[1]))
                locations.extend([('{2};{0};{1}'.format(c[0], l, c[1]), '{2};{0};{1}'.format(c[0], l, c[1]))
                                  for l in kind.container_locations.values_list('name', flat=True)])
            self.fields['locations'].choices = locations

        self.helper = FormHelper()

        action_row = Div(
            Div(
                Div(
                    Button('Add', type='add', value='Add Another', css_class="btn btn-success add pull-left"),
                    not self.initial.get('shipment') and HTML(
                        """<span title="Create one group for each container" class="btn btn-warning btn-margin" onclick="fillContainers();">Fill Containers</span>"""),
                    css_class="pull-left"
                ),
                css_class="col-xs-6"
            ),
            css_class="form-action row"
        )

        if self.initial.get('shipment'):
            groups = self.initial['shipment'].group_set.order_by('priority')
            self.repeated_data = {
                'name_set': [str(group.name) for group in groups],
                'priority_set': [group.priority or 0 for group in groups],
                'id_set': [group.pk for group in groups],
                'sample_count_set': [group.sample_count for group in groups],
                'plan_set': [str(group.plan) for group in groups],
                'kind_set': [str(group.kind) for group in groups],
                'absorption_edge_set': [str(group.absorption_edge) for group in groups],
                'resolution_set': [group.resolution or '' for group in groups],
            }
            action_row.append(Div(
                Div(
                    StrictButton('Save', type='submit', name="submit", value='submit', css_class='btn btn-primary'),
                    css_class="pull-right"
                ),
                css_class="col-xs-6"
            ))

            self.helper.title = "Add Groups to Shipment"
            self.helper.form_action = reverse_lazy('shipment-add-groups', kwargs={'pk': self.initial['shipment'].pk})

        else:
            action_row.append(Div(
                Div(
                    StrictButton('Finish', type='submit', name="submit", value='Finish', css_class='btn btn-primary'),
                    css_class="pull-right"
                ),
                css_class="col-xs-6"
            ))

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
                            Div(Field('priority', type="hidden", css_id="priority")),
                            Div(HTML("""<a title="Drag to change group priority" class="disabled move">
                                            <i class="fa fa-3x fa-grip"></i></a>"""), css_class="col-xs-1 form-offset"),
                            Div(Field('name', css_id="name"), css_class="col-xs-5"),
                            Div(Field('sample_count', css_id="sample_count"), css_class="col-xs-3"),
                            Div(HTML("""<a title="Sample Seat Selection" class="disabled btn btn-info inline-btn" onclick="showModal($(this));" href="#group-select"><i class="fa fa-fw fa-braille"></i></a>"""),
                                HTML("""<a title="Click to Delete Group" class="pull-right inline-btn remove btn btn-danger" style="display: none;"><i class="fa fa-fw fa-remove"></i></a>"""),
                                HTML("""<a title="Remove Group" class="pull-right inline-btn safe-remove btn btn-default"><i class="fa fa-fw fa-minus"></i></a>"""),
                                HTML("""<a title="Edit more group details" href="#group-details-{rowcount}" data-toggle="collapse" class="pull-right inline-btn btn btn-info btn-collapse"><i class="fa fa-fw fa-angle-double-right"></i></a>"""),
                                css_class="col-xs-3 text-right"),
                            Div(
                                Div(
                                    TabHolder(
                                        Tab('Experiment Parameters',
                                            Div(
                                                Div(
                                                    Div(Field('kind', css_class="tab-chosen chosen-select",
                                                              css_id="kind"), css_class="col-xs-6"),
                                                    Div(Field('plan', css_class="tab-chosen chosen-select",
                                                              css_id="plan"), css_class="col-xs-6"),
                                                    css_class="row"
                                                ),
                                                Div(
                                                    Div(Field('absorption_edge', css_id="absorption_edge"),
                                                        css_class="col-xs-6"),
                                                    Div(Field('resolution', css_id="resolution"), css_class="col-xs-6"),
                                                    css_class="row"
                                                ),
                                                css_class="row-fluid"
                                            )
                                        ),
                                        Tab('Comments',
                                            Div(
                                                Div(Field('comments', css_id="comments"), css_class="col-xs-12"),
                                                css_class="row"
                                            )
                                        )
                                    )
                                ),
                                css_class="col-xs-12 collapse",
                                css_id="group-details-{rowcount}"
                            ),
                            css_class="row template repeat-row list-group-item"
                        ),
                        css_class="repeat-group repeat-container list-group list-group-hover",
                    ),
                    action_row,
                    css_class="repeat-wrapper"
                ),
                css_class='repeat'
            ),
            Field('sample_locations', type="hidden"),
            Div(
                Div(
                    Div(
                        Div(
                            HTML("""<h3 class="modal-title">Select Seats for Samples in Group <span class="group-name"></span></h3>"""),
                            css_class="modal-header"
                        ),
                        Div(
                            Field('locations', template="users/forms/layout-container.html"),
                            Div(
                                Div(
                                    Div(
                                        StrictButton('Done', type='button', name="done",
                                                     onclick="hideModal($(this));",
                                                     css_class='btn btn-primary'),
                                        css_class="pull-right"
                                    ),
                                    css_class="col-xs-12"
                                ),
                                css_class="row form-action"
                            ),
                            css_class="modal-body",
                            css_id="form-content",
                        ),
                        css_class="modal-content",
                    ),
                    css_class="modal-dialog modal-md",
                ),
                css_class="modal fade extra-modal",
                css_id="group-select",
                css_role="dialog",
            )
        )

    def help_text(self):
        if self.initial.get('shipment'):
            return Div(HTML("""How do you want to group your samples?<br/>
                               <strong>Be careful! Removing a group will also remove any samples in the group</strong>""")
                       )
        else:
            return Div(HTML("""<h4>Add the groups of samples you will be working on!</h4>"""),
                       HTML("""<small>How do you want to group your samples?
                               Don't worry, you can always add more groups later.</small>"""),)

    def clean(self):
        self.repeated_data = {}
        cleaned_data = super(ShipmentGroupForm, self).clean()
        for field in self.Meta.fields:
            if 'groups-{}'.format(field) in self.data:
                cleaned_data['{}_set'.format(field)] = self.data.getlist('groups-{}'.format(field))
            else:
                cleaned_data['{}_set'.format(field)] = self.data.getlist(field)
        cleaned_data['sample_count_set'] = [count or 0 for count in cleaned_data.get('sample_count_set')]
        if len(set(cleaned_data['name_set'])) != len(cleaned_data['name_set']):
            self.add_error(None, forms.ValidationError("Groups in a shipment must each have a unique name"))
        if not self.is_valid():
            for k, v in cleaned_data.items():
                if isinstance(v, list):
                    self.repeated_data[k] = [str(e) for e in v]

        return cleaned_data


class GroupSelectForm(forms.ModelForm):
    id = forms.CharField(required=False, widget=forms.HiddenInput)
    sample_locations = forms.CharField(initial='{}')
    containers = forms.ModelMultipleChoiceField(
        queryset=Container.objects.all()
    )

    class Meta:
        model = Group
        fields = ['shipment', 'id']
        widgets = {
            'comments': forms.Textarea(attrs={'rows': "4"}),
            'priority': forms.TextInput(attrs={'readonly': True}),
            'shipment': forms.HiddenInput()
        }

    def __init__(self, *args, **kwargs):
        super(GroupSelectForm, self).__init__(*args, **kwargs)

        self.fields['containers'].queryset = self.initial.get('containers')

        self.helper = FormHelper()
        self.helper.form_id = "group-select"
        self.helper.layout = Layout(
            Div(Field('shipment')),
            Div(
                Div(
                    Field('sample_locations', type="hidden"),
                    Field('containers', template="users/forms/layout-container.html"),
                    css_class="col-xs-12"
                ),
                css_class="row"
            ),
        )

        if self.initial.get('shipment'):

            self.helper.layout.append(
                FormActions(
                    Div(
                        Div(
                            StrictButton('Save', type='submit', name="submit", value='submit', css_class='btn btn-primary'),
                            css_class='pull-right'
                        ),
                        css_class="col-xs-12"
                    ),
                    css_class="form-action row"
                )
            )
            self.helper.title = 'Select Seats for Samples in Group {}'.format(self.instance.name)
            self.helper.form_action = reverse_lazy('group-select', kwargs={'pk': self.instance.pk})

    def help_text(self):
        if self.initial.get('shipment'):
            return Div(HTML("""How do you want to group your samples?<br/>
                               <strong>Be careful! Removing a group will also remove any samples in the group</strong>""")
                       )
        else:
            return Div(HTML("""<h4>Step 3: Add the groups of samples you will be working on!</h4>"""),
                       HTML("""<small>How do you want to group your samples?
                               Don't worry, you can always add more groups later.</small>"""),)
