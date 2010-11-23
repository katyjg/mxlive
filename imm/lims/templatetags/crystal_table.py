from django import template
from django.template import Library
from django.db import models
from django.core.exceptions import ObjectDoesNotExist
from django.utils import dateformat
from django.utils.html import escape
from django.utils.text import capfirst
from django.utils.translation import get_date_formats
from django.contrib import admin
from django.conf import settings 
from django.utils.safestring import mark_safe
from django.utils.datastructures import MultiValueDict

register = Library()

@register.inclusion_tag('lims/entries/crystal_table.html', takes_context=True)
def crystal_table(context, crystals):
    # want crystals to be the whole crystal set.
    # want datasets to be a list of datasets, from all datasets, filtered to just have crystals in crystals
    # want results as a list of results from all results, filtered to just have ones relevant to crystals. 
    
    # after discussion, make it an expandable row, 
    datasets = None
    results = None
    return { 'crystals': crystals,
            'datasets': datasets,
            'results': results
            }
