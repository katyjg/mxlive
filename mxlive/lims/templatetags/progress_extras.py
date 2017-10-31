from django.template import Library
from django.db.models import Q
register = Library()


@register.filter
def num_session_samples(group, session):
    return group.sample_set.filter(pk__in=session.data_set.values_list('sample__pk')).count()


@register.simple_tag
def group_samples(group, session=None):
    if session:
        return group.sample_set.filter(pk__in=session.data_set.values_list('sample__pk'))
    return group.sample_set.all()


@register.simple_tag
def sample_data(sample, session=None):
    if session:
        return {
            'data': sample.data_set.filter(session=session),
            'reports': sample.reports().filter(Q(data__in=sample.data_set.filter(session=session)) | Q(data__isnull=True))
        }
    return {
        'data': sample.data_set.all(),
        'reports': sample.reports().all()
    }

