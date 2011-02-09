from django import forms

class OrderedForm(forms.ModelForm):
    """
    An OrderedForm class which re-uses the order of fields in the `fields`
    Meta option to determine the order in which to render the form fields.
    """
    
    def __init__(self, *args, **kwargs):
        super(OrderedForm, self).__init__(*args, **kwargs)
        if self._meta.fields:
            self.fields.keyOrder = self._meta.fields

    def restrict_by(self, field_name, obj):
        """
        Restrict the form such that only items related to the object identified by
        the primary key `id` through a field specified by `field_name`,
        are displayed within select boxes.
        
        """
        if obj is not None:
            id = obj.pk
        else:
            return
        for name, formfield in self.fields.items():
            if name != field_name and hasattr(formfield, 'queryset'):
                queryset = formfield.queryset
                if field_name in queryset.model._meta.get_all_field_names(): # some models will not have the field
                    formfield.queryset = queryset.filter(**{'%s__exact' % (field_name): id})

