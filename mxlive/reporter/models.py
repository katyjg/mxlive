from django.db import models
from django.db.models import Case, When, Value, CharField


# Create your models here.
class WithChoices(Case):
    """Queries display names for a Django choices field"""
    def __init__(self, model, field_ref, condition=None, then=None, **lookups):
        field_name = field_ref.split('__')[-1]
        choices = dict(model._meta.get_field(field_name).flatchoices)
        whens = [When(**{field_ref: k, 'then': Value(v)}) for k, v in choices.items()]
        super().__init__(*whens, output_field=CharField())
