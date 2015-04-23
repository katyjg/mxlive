from django import template

register = template.Library()  

@register.filter("sorted_list")  
def sorted_list(d, pos): 
    """Convert dictionary or list to a sorted list."""
    try:
        l = d.items()
    except:
        l = d
    l.sort(key=lambda x: x[pos])
    return l