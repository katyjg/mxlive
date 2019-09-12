from django import template
from django.utils.safestring import mark_safe
from mxlive.lims.models import Container, ContainerType, ContainerLocation
import json
from django.db.models import F, Func

register = template.Library()


@register.filter
def as_json(data):
    return mark_safe(json.dumps(data))


@register.simple_tag
def get_kind_json(data, container, create=False):
    if not create:
        try:
            for loc in data['locations'].keys():
                sample = container.samples.filter(location=loc).first()
                location = container.kind.locations.get(name=loc)
                child = container.children.filter(location=location).first()
                loc_info = {
                    'sample': sample and sample.name or child and child.name or '',
                    'group': sample and sample.group.name or '',
                    'started': sample and sample.datasets.count() or 0,
                    'accepts': location and ';'.join(location.accepts.values_list('name', flat=True)) or False
                }
                data['locations'][loc].append(loc_info)
        except:
            pass

    return mark_safe(json.dumps(data, indent=4))

@register.simple_tag
def get_layout_json(container, create=False):

    locations = ContainerLocation.objects.filter(containers=container.kind).annotate(
        owner=F('contents__project__name'), title=F('contents__name'),
    )
    layout = container.kind.layout
    data = {
        'radius': layout['radius'],
        'locations': {
            loc.name: layout['locations'].get(loc.name, [0.0, 0.0]) + [
                {
                    'sample': '',
                    'group': '',
                    'started': 0,
                    'accepts': ';'.join(loc.accepts.all().values_list('name', flat=True))
                }
            ]
            for loc in locations
        }
    }
    if 'height' in layout:
        data['height'] = layout['height']
    return mark_safe(json.dumps(data, indent=4))


@register.filter
def kind_json(data, pk):
    try:
        container = Container.objects.get(pk=int(pk))
        for loc in data['locations'].keys():
            sample = container.samples.filter(location=loc).first()
            location = container.kind.locations.get(name=loc)
            child = container.children.filter(location=location).first()
            loc_info = {
                'sample': sample and sample.name or child and child.name or '',
                'group': sample and sample.group.name or '',
                'started': sample and sample.datasets.count() or 0,
                'accepts': location and ';'.join(location.accepts.values_list('name', flat=True)) or False
            }
            data['locations'][loc].append(loc_info)
    except:
        pass

    return mark_safe(json.dumps(data, indent=4))


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
        types = ContainerType.objects.filter(pk__in=c.kind.locations.values_list('accepts', flat=True).distinct())\
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


@register.simple_tag
def containers_from_choices(data):
    containers = set([';'.join(opt[0].split(';')[0:-1]) for opt in data])
    return [(c.split(';')[1], c.split(';')[1], ContainerType.objects.get(pk=int(c.split(';')[0]))) for c in containers]


@register.simple_tag
def containers_from_queryset(data):
    return [(c.pk, c.name, c.kind) for c in data]

@register.simple_tag
def stop_propagation(b):
    return b