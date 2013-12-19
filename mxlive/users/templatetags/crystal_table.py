from django.template import Library
from mxlive.users.models import Crystal

register = Library()

@register.inclusion_tag('users/entries/crystal_table.html', takes_context=True)
def crystal_table(context, crystals, admin, experiment):
    # want crystals to be the whole crystal set.
    # want datasets to be a list of datasets, from all datasets, filtered to just have crystals in crystals
    # want results as a list of results from all results, filtered to just have ones relevant to crystals. 
    
    # after discussion, make it an expandable row, 
    if admin:
        crystals = crystals.filter(status__in=[Crystal.STATES.ON_SITE, Crystal.STATES.LOADED])

    crystal_list = list()
    unprocessed = list()
    for crystal in crystals:
        best_s = crystal.best_screening()
        best_c = crystal.best_collection()
        if best_s.get('report') is not None:
            best = best_s
        else:
            best = best_c
        if best.get('report') is not None:
            crystal_list.append((best['report'].score, crystal))
        else:
            unprocessed.append(crystal)
    crystal_list.sort()
    crystal_list.reverse()
    for crystal in unprocessed:
        crystal_list.append((-99, crystal))
    
    return { 'crystals': [xtl for s,xtl in crystal_list],
            'admin': admin,
            'experiment': experiment
            }

@register.inclusion_tag('users/entries/crystal_priority_table.html', takes_context=True)
def crystal_priority_table(context, crystals, admin, experiment):
    # want crystals sorted by priority to be the whole crystal set.
    crystal_list = list(crystals.exclude(priority__isnull=True).exclude(priority__exact=0).order_by('priority')) + list(crystals.exclude(priority__gte=1))
    return {'crystals': crystal_list, #prioritize_and_sort(crystals), #'crystals': crystals.order_by('priority','container','container_location'),
            'admin': admin,
            'experiment': experiment
            }
