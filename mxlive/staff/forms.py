from models import UserList, Announcement
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


class AnnouncementForm(forms.ModelForm):

    class Meta:
        model = Announcement
        fields = ['title', 'description', 'attachment', 'url', 'priority']

    def __init__(self, *args, **kwargs):
        super(AnnouncementForm, self).__init__(*args, **kwargs)

        self.helper = FormHelper()
        self.helper.title = u"Edit Announcement"
        self.helper.form_action = reverse_lazy('announcement-edit', kwargs={'pk': self.instance.pk})
        self.helper.layout = Layout(
            Div(
                Div('priority', css_class="col-xs-2"),
                Div('title', css_class="col-xs-10"),
                Div('description', css_class="col-xs-12"),
                Div('url', css_class="col-xs-12"),
                Div('attachment', css_class="col-xs-12"),

            ),
            FormActions(
                Div(
                    Div(
                        StrictButton('Revert', type='reset', value='Reset', css_class="btn btn-default"),
                        StrictButton('Save', type='submit', name="submit", value='save',
                                     css_class='btn btn-primary'),
                        css_class='pull-right'
                    ),
                    css_class="col-xs-12"
                ),
                css_class="row"
            )
        )


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
                        help_text="Comments entered here will be visible on the user's MxLIVE account.")

    class Meta:
        model = Project
        fields = ('staff_comments', )


