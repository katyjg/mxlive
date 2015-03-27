from django import template

register = template.Library()  
  
@register.filter("get_min")
def get_min(data, pad):
    return min(data)-(max(data)-min(data))/pad

@register.filter("get_max")
def get_max(data, pad):
    return max(data)+(max(data)-min(data))/pad

@register.filter("get_xanes_min")
def get_xanes_min(data, pad):
    return min(data['fp']) - (max(data['fpp'])-min(data['fp']))/pad

@register.filter("get_xanes_max")
def get_xanes_max(data, pad):
    return max(data['fpp']) + (max(data['fpp'])-min(data['fp']))/pad

@register.filter("sort_items")
def sort_items(data):
    data.sort()
    return data

@register.filter("get_data")
def get_data(data, xdata=None):
    if xdata:
        try:
            return [[xdata[i], dat] for i, dat in enumerate(data)]
        except: 
            return []
    else:
        return [[i, dat] for i, dat in enumerate(data)]
    
@register.filter("sq_root")
def sq_root(x):
    return (x > 0.0 and (x**-0.5)) or ''

@register.filter("get_from_key")
def get_from_key(data, key):
    ALT_KEYS = {'frame_no': 'frame',
               }
    try:
        return data[key]
    except: 
        return data[ALT_KEYS[key]]
    finally:
        return []
