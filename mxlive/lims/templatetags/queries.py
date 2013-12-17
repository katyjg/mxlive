from django.template import Library

register = Library()

from mxlive.lims.models import Data
from mxlive.lims.models import Result

@register.inclusion_tag('staff/entries/crystal_detail.html')
def crystal_detail(experiment, crystal):
    return {'datasets' : Data.objects.filter(experiment=experiment).filter(crystal=crystal),
            'experiment': experiment,
            'crystal': crystal}

@register.inclusion_tag('staff/entries/data_detail.html')
def data_detail(experiment, crystal, dataset):
    import logging
    logging.info('%s, %s, %s' % (experiment.pk, crystal.pk, dataset.pk))
    return {'results' : Result.objects.filter(experiment=experiment).filter(crystal=crystal).filter(data=dataset),
            'experiment': experiment,
            'crystal': crystal,
            'dataset': dataset}
