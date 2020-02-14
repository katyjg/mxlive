from django import forms
from django.urls import reverse_lazy

from crispy_forms.bootstrap import StrictButton
from crispy_forms.helper import FormHelper
from crispy_forms.layout import Div, Field, Layout

from .models import AccessType, BeamlineProject, Beamtime


class BodyHelper(FormHelper):
    def __init__(self, form):
        super().__init__(form)
        self.form_tag = False
        self.use_custom_control = True
        self.form_show_errors = False


class FooterHelper(FormHelper):
    def __init__(self, form):
        super().__init__(form)
        self.form_tag = False
        self.disable_csrf = True
        self.form_show_errors = False


class BeamlineProjectForm(forms.ModelForm):
    class Meta:
        model = BeamlineProject
        fields = ['project', 'number', 'title', 'expiration', 'email']
        widgets = {
            'title': forms.Textarea(attrs={"cols": 40, "rows": 2}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self.body = BodyHelper(self)
        self.footer = FooterHelper(self)
        if self.instance.pk:
            self.body.title = u"Edit Beamline Project"
            self.body.form_action = reverse_lazy('beamline-project-edit', kwargs={'pk': self.instance.pk})
        else:
            self.body.title = u"New Beamline Project"
            self.body.form_action = reverse_lazy('new-beamline-project')
        self.body.layout = Layout(
            Div(
                Div('project', css_class="col-12"),
                css_class="row"
            ),
            Div(
                Div('number', css_class="col-6"),
                Div('expiration', css_class="col-6"),
                css_class="row"
            ),
            Div(
                Div('email', css_class="col-12"),
                css_class="row"
            ),
            Div(
                Div('title', css_class="col-12"),
                css_class="row"
            ),
        )
        self.footer.layout = Layout(
            StrictButton('Revert', type='reset', value='Reset', css_class="btn btn-secondary"),
            StrictButton('Save', type='submit', name="submit", value='save', css_class='btn btn-primary'),
        )


class BeamtimeForm(forms.ModelForm):
    access = forms.ModelMultipleChoiceField(label='Access Type', queryset=AccessType.objects.all(), required=False)

    class Meta:
        model = Beamtime
        fields = ['project', 'beamline', 'start', 'end', 'comments']
        widgets = {
            'comments': forms.Textarea(attrs={"cols": 40, "rows": 7}),
            'start': forms.HiddenInput(),
            'end': forms.HiddenInput(),
            'beamline': forms.HiddenInput(),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self.body = BodyHelper(self)
        self.footer = FooterHelper(self)
        if self.instance.pk:
            self.body.title = u"Edit Beamtime"
            self.body.form_action = reverse_lazy('beamtime-edit', kwargs={'pk': self.instance.pk})
        else:
            self.body.title = u"New Beamtime"
            self.body.form_action = reverse_lazy('new-beamtime')
        self.body.layout = Layout(
            Div(
                Div('project', css_class="col-12"),
                Div('beamline', css_class="col-12"),
                css_class="row"
            ),

            Div(
                Div(Field('access', css_class="select"), css_class="col-12"),
                css_class="row"
            ),
            Div(
                Div('start', css_class="col-6"),
                Div('end', css_class="col-6"),
                css_class="row"
            ),
            Div(
                Div('comments', css_class="col-12"),
                css_class="row"
            ),
        )
        self.footer.layout = Layout(
            StrictButton('Revert', type='reset', value='Reset', css_class="btn btn-secondary"),
            StrictButton('Save', type='submit', name="submit", value='save', css_class='btn btn-primary'),
        )
