"""
Widgets and Fields with extra html class attributes
"""

from django import forms
from django.contrib.admin import widgets


# Widgets

class CommentInput(forms.Textarea):
    def __init__(self, *args, **kwargs):
        kwargs.setdefault('attrs',{'class': 'field textarea medium'})
        super(CommentInput, self).__init__(*args, **kwargs)

class LargeTextArea(forms.Textarea):
    def __init__(self, *args, **kwargs):
        kwargs.setdefault('attrs',{'class': 'field textarea Large'})
        super(LargeTextArea, self).__init__(*args, **kwargs)

class SmallTextArea(forms.Textarea):
    def __init__(self, *args, **kwargs):
        kwargs.setdefault('attrs',{'class': 'field textarea small'})
        super(SmallTextArea, self).__init__(*args, **kwargs)


class LargeInput(forms.TextInput):
    def __init__(self, *args, **kwargs):
        kwargs.setdefault('attrs',{'class': 'field text large'})
        super(LargeInput, self).__init__(*args, **kwargs)

class LargeFileInput(forms.FileInput):
    def __init__(self, *args, **kwargs):
        kwargs.setdefault('attrs',{'class': 'field file large','id': 'file-uploader'})
        super(LargeFileInput, self).__init__(*args, **kwargs)
    
    class Media:
        css = {
            'all': ('/css/fileuploader.css',)
        }
        js = ('/js/fileuploader.js',)

class LeftHalfInput(forms.TextInput):
    def __init__(self, *args, **kwargs):
        kwargs.setdefault('attrs',{'class': 'field text leftHalf'})
        super(LeftHalfInput, self).__init__(*args, **kwargs)

class RightHalfInput(forms.TextInput):
    def __init__(self, *args, **kwargs):
        kwargs.setdefault('attrs',{'class': 'field text rightHalf'})
        super(RightHalfInput, self).__init__(*args, **kwargs)
        
class LeftHalfDate(widgets.AdminDateWidget):
    def __init__(self, *args, **kwargs):
        kwargs.setdefault('attrs',{'class': 'field text leftHalf'})
        super(widgets.AdminDateWidget, self).__init__(*args, **kwargs)

class RightHalfDate(widgets.AdminDateWidget):
    def __init__(self, *args, **kwargs):
        kwargs.setdefault('attrs',{'class': 'field text rightHalf'})
        super(widgets.AdminDateWidget, self).__init__(*args, **kwargs)

class LeftThirdInput(forms.TextInput):
    def __init__(self, *args, **kwargs):
        kwargs.setdefault('attrs',{'class': 'field text leftThird'})
        super(LeftThirdInput, self).__init__(*args, **kwargs)

class MiddleThirdInput(forms.TextInput):
    def __init__(self, *args, **kwargs):
        kwargs.setdefault('attrs',{'class': 'field text middleThird'})
        super(MiddleThirdInput, self).__init__(*args, **kwargs)

class RightThirdInput(forms.TextInput):
    def __init__(self, *args, **kwargs):
        kwargs.setdefault('attrs',{'class': 'field text rightThird'})
        super(RightThirdInput, self).__init__(*args, **kwargs)

class LargeSelect(forms.Select):
    def __init__(self, *args, **kwargs):
        kwargs.setdefault('attrs',{'class': 'field select large'})
        super(LargeSelect, self).__init__(*args, **kwargs)

class RightHalfSelect(forms.Select):
    def __init__(self, *args, **kwargs):
        kwargs.setdefault('attrs',{'class': 'field select rightHalf'})
        super(RightHalfSelect, self).__init__(*args, **kwargs)

class LeftHalfSelect(forms.Select):
    def __init__(self, *args, **kwargs):
        kwargs.setdefault('attrs',{'class': 'field select leftHalf'})
        super(LeftHalfSelect, self).__init__(*args, **kwargs)

class RightThirdSelect(forms.Select):
    def __init__(self, *args, **kwargs):
        kwargs.setdefault('attrs',{'class': 'field select rightThird'})
        super(RightThirdSelect, self).__init__(*args, **kwargs)

class MiddleThirdSelect(forms.Select):
    def __init__(self, *args, **kwargs):
        kwargs.setdefault('attrs',{'class': 'field select middleThird'})
        super(MiddleThirdSelect, self).__init__(*args, **kwargs)

class LeftThirdSelect(forms.Select):
    def __init__(self, *args, **kwargs):
        kwargs.setdefault('attrs',{'class': 'field select leftThird'})
        super(LeftThirdSelect, self).__init__(*args, **kwargs)

class BarCodeInput(forms.TextInput):
    def __init__(self, *args, **kwargs):
        kwargs.setdefault('attrs',{'class': 'field barcode large'})
        super(BarCodeInput, self).__init__(*args, **kwargs)

class BarCodeReturn(forms.TextInput):
    def __init__(self, *args, **kwargs):
        kwargs.setdefault('attrs',{'class': 'field barcode-return large'})
        super(BarCodeReturn, self).__init__(*args, **kwargs)

class MatrixCodeInput(forms.TextInput):
    def __init__(self, *args, **kwargs):
        kwargs.setdefault('attrs',{'class': 'field matrixcode large'})
        super(MatrixCodeInput, self).__init__(*args, **kwargs)


class LargeCheckBoxInput(forms.CheckboxInput):
    input_type = 'checkbox'
    is_boolean = True
    def __init__(self, *args, **kwargs):
        kwargs.setdefault('attrs',{'class': 'field checkbox'})
        super(LargeCheckBoxInput, self).__init__(*args, **kwargs)

class LeftCheckBoxInput(forms.CheckboxInput):
    input_type = 'checkbox'
    is_boolean = True
    def __init__(self, *args, **kwargs):
        kwargs.setdefault('attrs',{'class': 'field checkbox leftHalf'})
        super(LeftCheckBoxInput, self).__init__(*args, **kwargs)

class RightCheckBoxInput(forms.CheckboxInput):
    input_type = 'checkbox'
    is_boolean = True
    def __init__(self, *args, **kwargs):
        kwargs.setdefault('attrs',{'class': 'field checkbox rightHalf'})
        super(RightCheckBoxInput, self).__init__(*args, **kwargs)

class CustomRadioInput(forms.CheckboxInput):
    input_type = 'radio'
    is_boolean = True
    def __init__(self, *args, **kwargs):
        kwargs.setdefault('attrs',{'class': 'field radio'})
        super(CustomRadioInput, self).__init__(*args, **kwargs)
        
        
class CustomSelectMultiple(forms.SelectMultiple):
    is_multiselect = True       
    def __init__(self, *args, **kwargs):
        kwargs.setdefault('attrs',{'class': 'field select large'})
        super(CustomSelectMultiple, self).__init__(*args, **kwargs)
       
    
# Fields

class CommentField(forms.CharField):
    widget = CommentInput

class LargeTextField(forms.CharField):
    widget = LargeTextArea

class SmallTextField(forms.CharField):
    widget = SmallTextArea

class BarCodeField(forms.CharField):
    widget = BarCodeInput

class BarCodeReturnField(forms.CharField):
    widget = BarCodeReturn
    
class MatrixCodeField(forms.CharField):
    widget = MatrixCodeInput

class LargeCharField(forms.CharField):
    widget = LargeInput
    
class LeftHalfCharField(forms.CharField):
    widget = LeftHalfInput
    
class RightHalfCharField(forms.CharField):
    widget = RightHalfInput
    
class LeftHalfDateField(widgets.AdminDateWidget):
    widget = LeftHalfDate
    
class RightHalfDateField(forms.DateField):
    widget = RightHalfDate
    
class LeftThirdCharField(forms.CharField):
    widget = LeftThirdInput
    
class MiddleThirdCharField(forms.CharField):
    widget = MiddleThirdInput
    
class RightThirdCharField(forms.CharField):
    widget = RightThirdInput
    
class LargeChoiceField(forms.ChoiceField):
    widget = LargeSelect
    
class LeftHalfChoiceField(forms.ChoiceField):
    widget = LeftHalfSelect
    
class RightHalfChoiceField(forms.ChoiceField):
    widget = RightHalfSelect
    
class MiddleThirdChoiceField(forms.ChoiceField):
    widget = MiddleThirdSelect
    
class LeftThirdChoiceField(forms.ChoiceField):
    widget = LeftThirdSelect

class RightThirdChoiceField(forms.ChoiceField):
    widget = RightThirdSelect

class CustomModelChoiceField(forms.ModelChoiceField):
    widget = LargeSelect

class LargeCheckBoxField(forms.BooleanField):
    widget = LargeCheckBoxInput

class LeftCheckBoxField(forms.BooleanField):
    widget = LeftCheckBoxInput

class RightCheckBoxField(forms.BooleanField):
    widget = RightCheckBoxInput
    
class CustomRadioField(forms.BooleanField):
    widget = CustomRadioInput
    
