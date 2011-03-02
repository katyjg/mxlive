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

from imm.lims.models import Result
from imm.lims.models import Crystal, Experiment

register = Library()

@register.inclusion_tag('lims/entries/crystal_table.html', takes_context=True)
def crystal_table(context, crystals, admin, experiment):
    # want crystals to be the whole crystal set.
    # want datasets to be a list of datasets, from all datasets, filtered to just have crystals in crystals
    # want results as a list of results from all results, filtered to just have ones relevant to crystals. 
    
    # after discussion, make it an expandable row, 
    crystal_list = list()
    for crystal in crystals:
        best = crystal.best_screening()
        if best.get('report') is not None:
            crystal_list.append((best['report'].score, crystal))
        else:
            crystal_list.append((-99, crystal))
    crystal_list.sort()
    
    if admin:
        crystals = crystals.filter(status__in=[Crystal.STATES.ON_SITE, Crystal.STATES.LOADED])
    return { 'crystals': [xtl for s,xtl in crystal_list],
            'admin': admin,
            'experiment': experiment
            }

@register.inclusion_tag('lims/entries/crystal_priority_table.html', takes_context=True)
def crystal_priority_table(context, crystals, admin, experiment):
    # want crystals sorted by priority to be the whole crystal set.
    return { 'crystals': crystals.order_by('priority').reverse(),
            'admin': admin,
            'experiment': experiment
            }
