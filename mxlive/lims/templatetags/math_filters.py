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

@register.filter("top_offset")
def top_offset(loc, counter):
    top_list = [17, 12, 14, 0, -32, -75, -85, -86, -83, -81, -86, -101, -126, -158, -191, -220]
    return top_list[int(loc)-1] + (int(loc)-int(counter))*15 

