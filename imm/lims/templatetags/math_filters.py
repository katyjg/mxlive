from django import template

register = template.Library()  
  
@register.filter("multiplied_by")  
def multiplied_by(value, rows=0, total=300):  
    '''
    total should be the size of the image (in the case of the unipuck image, height and width are the same)
    rows is the number of rows located above the element (since each individual element has an image size (50x50), 
    we need to account for the resulting vertical offset, which accumulates with additional elements).
    ''' 
    return value*total-25-rows*50 


@register.filter("dewar_price")
def dewar_price(value, price=200):
    return value*price
