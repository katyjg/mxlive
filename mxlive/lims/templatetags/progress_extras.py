from django.template import Library
from django.db.models import Q
register = Library()


@register.filter
def num_session_samples(group, session):
    return group.samples.filter(pk__in=session.datasets.values_list('sample__pk')).count()


@register.simple_tag
def group_samples(group, session=None):
    if session:
        return group.samples.filter(datasets__session=session.pk)
    return group.samples.all()


@register.simple_tag
def sample_data(sample, session=None):
    if session:
        return {
            'data': sample.datasets.filter(session=session),
            'reports': sample.reports().filter(Q(data__in=sample.datasets.filter(session=session)) | Q(data__isnull=True))
        }
    return {
        'data': sample.datasets.all(),
        'reports': sample.reports().all()
    }

