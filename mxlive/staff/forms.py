from .models import UserList, UserCategory, Announcement
from django import forms
from django.urls import reverse_lazy

from crispy_forms.helper import FormHelper
from crispy_forms.layout import Layout, HTML, Div, Field
from crispy_forms.bootstrap import StrictButton, FormActions


class AnnouncementForm(forms.ModelForm):

    class Meta:
        model = Announcement
        fields = ['title', 'description', 'attachment', 'url', 'priority']

    def __init__(self, *args, **kwargs):
        super(AnnouncementForm, self).__init__(*args, **kwargs)

        self.helper = FormHelper()
        if self.instance.pk:
            self.helper.title = u"Edit Announcement"
            self.helper.form_action = reverse_lazy('announcement-edit', kwargs={'pk': self.instance.pk})
        else:
            self.helper.title = u"New Announcement"
            self.helper.form_action = reverse_lazy('new-announcement')
        self.helper.layout = Layout(
            Div(
                Div('priority', css_class="col-xs-2"),
                Div('title', css_class="col-xs-10"),
                css_class="row"
            ),
            Div(
                Div('description', css_class="col-xs-12"),
                css_class="row"
            ),
            Div(
                Div('url', css_class="col-xs-12"),
                css_class="row"
            ),
            Div(
                Div('attachment', css_class="col-xs-12"),
                css_class="row"
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
                css_class="form-action row"
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
                css_class="row"
            ),
            Div(
                Div(
                    HTML("""It may take a few minutes for your changes to be updated on the server.<br/>
                            Changes are pulled every 5 minutes."""),
                    css_class="col-xs-12"
                ),
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

    class Meta:
        model = UserList
        fields = ('users',)


class CategoryForm(forms.ModelForm):

    def __init__(self, *args, **kwargs):
        super(CategoryForm, self).__init__(*args, **kwargs)
        self.fields['projects'].label = "%s Users" % format(self.instance)
        self.fields['projects'].queryset = self.fields['projects'].queryset.order_by('name')

        self.helper = FormHelper()
        self.helper.title = u"Edit User Categories"
        self.helper.form_action = reverse_lazy('category-edit', kwargs={'pk': self.instance.pk})
        self.helper.layout = Layout(
            Div(
                Div(
                    Field('projects', css_class="chosen"),
                    css_class="col-xs-12"
                ),
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

    class Meta:
        model = UserCategory
        fields = ('projects',)