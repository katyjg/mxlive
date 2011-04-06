from django import forms
from django.db.models import Q
from django.core.exceptions import FieldError
from lims.models import *

class OrderedForm(forms.ModelForm):
    """
    An OrderedForm class which re-uses the order of fields in the `fields`
    Meta option to determine the order in which to render the form fields.
    """
    
    def __init__(self, *args, **kwargs):
        super(OrderedForm, self).__init__(*args, **kwargs)
        if self._meta.fields:
            self.fields.keyOrder = self._meta.fields
            if self._meta.model and hasattr(self._meta.model, 'HELP'):
                for field in self._meta.fields:
                    if not self.fields[field].help_text:
                        try:
                            self.fields[field].help_text = self._meta.model.HELP[field]
                        except KeyError:
                            pass

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
                if field_name in queryset.model._meta.get_all_field_names(): # some models will not have the field
                    formfield.queryset = queryset.filter(**{'%s__exact' % (field_name): value})

    def clean_name(self):
        try: 
            if self.initial['name'] == self.cleaned_data['name']:
                return self.cleaned_data['name']
        except KeyError:
            pass

        try:        
            if self.Meta.model.objects.filter(project__exact=self.cleaned_data['project'], name__exact=self.cleaned_data['name']).exclude(status__exact=self.Meta.model.STATES.ARCHIVED).exists():
                raise forms.ValidationError('An un-archived %s already exists with this name' % self.Meta.model.__name__)
        except (KeyError, FieldError):
            pass
        return self.cleaned_data['name']
          

