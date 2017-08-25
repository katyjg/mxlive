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
def kind_json(data, pk):
    try:
        container = Container.objects.get(pk=int(pk))
        for sample in container.sample_set.all():
            data['locations'][sample.container_location].extend([sample.name, sample.group.name])
        for location in container.kind.container_locations.filter(accepts__isnull=False):
            data['locations'][location.name].extend([container.children.filter(location=location).exists(), '',
                                                     ';'.join(location.accepts.values_list('name', flat=True))])
    except:
        pass
    return mark_safe(json.dumps(data))


@register.filter
def get_children(pk):
    try:
        return Container.objects.get(pk=pk).children.all()
    except:
        return []


@register.filter
def get_accepts(pk):
    try:
        return Container.objects.get(pk=pk).kind.accepts
    except:
        return ""


@register.filter
def accepts_envelope(pk):
    try:
        c = Container.objects.get(pk=int(pk))
        types = ContainerType.objects.filter(pk__in=c.kind.container_locations.values_list('accepts', flat=True).distinct())\
                            .values_list('envelope',flat=True)
        return types and types.first() or 'circle'
    except:
        return 'circle'


@register.filter
def get_coords(kind, location):
    return kind.layout['locations'].get('{}'.format(location))


@register.filter
def get_kind(pk):
    return ContainerType.objects.get(pk=int(pk))


@register.filter
def get_containers_from_choices(data):
    # Expecting a list of strings formatted like {containertype__pk}:{name}:{containerlocation__name}
    # Returns a list of tuples like (name, containertype)
    containers = set([';'.join(opt[0].split(';')[0:-1]) for opt in data])
    return [(c.split(';')[1], ContainerType.objects.get(pk=int(c.split(';')[0]))) for c in containers]