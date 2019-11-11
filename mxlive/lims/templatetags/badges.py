from django import template
from django.utils.safestring import mark_safe
from mxlive.utils import colors

register = template.Library()  
SCORE_CLASSES = [(0.8, 1, 'excellent-score'),
                 (0.7, 0.8, 'good-score'),
                 (0.6, 0.7, 'fair-score'),
                 (0.5, 0.6, 'usable-score'),
                 (0.0, 0.5, 'unusable-score')]

@register.filter("color_score")  
def color_score(value, decimal_places):
    ffmt = '%%0.%df' % decimal_places
    for lo, hi, c in SCORE_CLASSES:
        if lo < value <= hi:
            return mark_safe('<span class="%s">%s</span>' % (c, ffmt % value))
    else:
        return mark_safe('<span class="unusable-score">%s</span>' % (c, ffmt % value))

@register.filter("label_score")
def label_score(value):
    for lo, hi, c in SCORE_CLASSES:
        if lo < value <= hi:
            return c
    return "unusable-score"


@register.filter("dataset")
def dataset(dataset):
    if 'MX' in dataset.kind or dataset.kind == 'RASTER':
        return "{} frames".format(len(dataset.frames))
    elif 'SCAN' in dataset.kind:
        return "{} keV".format(dataset.energy)


@register.inclusion_tag('users/components/badge-score.html')
def score_badge(score):
    rgba = colors.colormap(score)
    return {
        'score': round(score, 2),
        'styles': (
            "text-shadow: 0 0 2px rgba(0, 0, 0, 0.9); "
            "color: #fff; "
            "background-color: rgba({}, {}, {}, {:0.2f});"
        ).format(*rgba)
    }


@register.inclusion_tag('users/components/badge-label.html')
def label_badge(header="", classes="", value=0, score=False):
    if score:
        rgba = colors.colormap(value)
        value = round(value, 2)
        styles = (
            "text-shadow: 0 0 2px rgba(0, 0, 0, 0.9); "
            "color: #fff; "
            "background-color: rgba({}, {}, {}, {:0.2f});"
        ).format(*rgba)
    else:
        styles = ""
    return {
        'header': header,
        'classes': classes,
        'styles': styles,
        'value': value
    }

@register.filter("score_color")
def score_color(value):
    rgba = colors.colormap(value)
    return 'rgba({}, {}, {}, {:0.2f})'.format(*rgba)

