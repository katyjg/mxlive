from django import template
from django.utils.safestring import mark_safe
from lims.models import Sample, Container, ContainerType
import numpy
import json

register = template.Library()

@register.filter
def as_json(data):
    return mark_safe(json.dumps(data))


@register.filter
def color_json(data, pk):
    try:
        pk = int(pk)
        container = Container.objects.get(pk=pk)
        for sample in container.sample_set.all():
            data['locations'][sample.container_location].append(sample.name)
    except:
        pass
    return mark_safe(json.dumps(data))


@register.filter
def get_kind(pk):
    return ContainerType.objects.get(pk=int(pk))

@register.filter
def get_containers_from_choices(data):
    # Expecting a list of strings formatted like {containertype__pk}:{name}:{containerlocation__name}
    # Returns a list of tuples like (name, containertype)
    containers = set([';'.join(opt[0].split(';')[0:-1]) for opt in data])
    return [(c.split(';')[1], ContainerType.objects.get(pk=int(c.split(';')[0]))) for c in containers]