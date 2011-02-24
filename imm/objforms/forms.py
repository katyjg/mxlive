from django import forms
from django.db.models import Q

class OrderedForm(forms.ModelForm):
    """
    An OrderedForm class which re-uses the order of fields in the `fields`
    Meta option to determine the order in which to render the form fields.
    """
    
    def __init__(self, *args, **kwargs):
        super(OrderedForm, self).__init__(*args, **kwargs)
        if self._meta.fields:
            self.fields.keyOrder = self._meta.fields

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

    def duplicate_name(self, project, value, field):
        if hasattr(self, 'status'):
            return self._meta.model.objects.filter(project__exact=project).exclude(status__exact=self._meta.model.STATES.ARCHIVED).filter(name__exact=value).exists()
        else:
            return self._meta.model.objects.filter(Q(project__exact=project), Q(name__exact=value)).exists()
