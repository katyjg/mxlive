from django.template import Library
from lims.models import Sample

register = Library()

@register.inclusion_tag('users/entries/experiment_table.html', takes_context=True)
def experiment_table(context, obj, admin):
    containers = obj.project.container_set.filter(shipment=obj)
    experiments = obj.project.experiment_set.filter(pk__in=obj.project.sample_set.filter(container__shipment__exact=obj.pk).values('experiment'))
    list_exps = list(experiments.exclude(priority__isnull=True).exclude(priority__exact=0).order_by('priority')) + list(experiments.exclude(priority__gte=1))

    return { 'experiments': list_exps,
              'containers': containers,
              'admin': admin,
              'object': obj
            }

@register.filter("in_shipment")  
def in_shipment(crystals, containers):
    return crystals.filter(container__in=containers).count()

@register.filter("arrived_onsite")
def arrived_onsite(crystals, containers):
    return crystals.filter(container__in=containers).filter(status__in=[Sample.STATES.ON_SITE, Sample.STATES.LOADED]).count()
