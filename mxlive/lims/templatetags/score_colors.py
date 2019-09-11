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


@register.filter("score_color")
def score_color(value):
    rgba = colors.colormap(value)
    return 'rgba({}, {}, {}, {:0.2f})'.format(*rgba)
