from django import template

register = template.Library()  
  
@register.filter("multiplied_by")  
def multiplied_by(value, rows=0, total=250):  
    '''
    'total' should be the size of the image (in the case of the unipuck image, height and width are the same)
    'rows' is the number of rows located above the element (since each individual element has an image size (50x50), 
    we need to account for the resulting vertical offset, which accumulates with additional elements).
    ''' 
    return value*total-20-rows*40 


@register.filter("dewar_price")
def dewar_price(value, price=200):
    return value*price

@register.filter("sum_index")
def sum_index(list, i):
    total = 0
    for v in list:
        total += v[i]
    return total

@register.filter("sum_dict")
def sum_dict(dict, i):
    total = 0
    for k, v in dict.items():
        total = total + v[i]
    return total

@register.filter("sum_shifts")
def sum_shifts(list):
    num = 0
    for v in list:
        num += v.get_num_shifts()
    return num