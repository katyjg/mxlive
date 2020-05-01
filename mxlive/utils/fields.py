import re
from datetime import datetime, date

from django.db import models
from django.db.models import FileField
from django.core.files.storage import FileSystemStorage
from django import forms
from django.template.defaultfilters import filesizeformat
from django.utils.translation import ugettext_lazy as _
from collections import Sequence


class LocalStorage(FileSystemStorage):
    def size(self, name):
        if self.exists(name):
            return super(LocalStorage, self).size(name)
        else:
            return 0


class RestrictedFileField(FileField):
    """
    Same as FileField, but you can specify:
        * content_types - list containing allowed content_types. Example: ["application/pdf", "image/jpeg"]
        * max_upload_size - a number indicating the maximum file size allowed for upload.
            2.5MB - 2621440
            5MB - 5242880
            10MB - 10485760
            20MB - 20971520
            50MB - 5242880
            100MB 104857600
            250MB - 214958080
            500MB - 429916160
    """

    def __init__(self, *args, **kwargs):
        self.file_types = kwargs.pop("file_types", ["application/pdf", "image/jpeg", "image/png"])
        self.max_size = kwargs.pop("max_size", 2621440)
        kwargs['storage'] = kwargs.get('storage', LocalStorage())
        kwargs["help_text"] = "Maximum size {0}, Formats: {1}.".format(
            filesizeformat(self.max_size),
            ",".join([t.split("/")[-1].upper() for t in self.file_types])
        )
        super(RestrictedFileField, self).__init__(*args, **kwargs)
        # print self.widget

    def clean(self, *args, **kwargs):
        data = super(RestrictedFileField, self).clean(*args, **kwargs)
        _file = data.file
        try:
            content_type = _file.content_type
            if content_type in self.file_types:
                if _file._size > self.max_size:
                    raise forms.ValidationError(
                        _("{1} file exceeds maximum of {0}.").format(filesizeformat(self.max_size),
                                                                     filesizeformat(_file._size)))
            else:
                raise forms.ValidationError(_("File type not supported."))
        except AttributeError:
            pass

        return data

    def formfield(self, **kwargs):
        ff = super(RestrictedFileField, self).formfield(**kwargs)
        ff.widget.attrs.update(max_size=self.max_size, file_types=self.file_types)
        ff.max_size = self.max_size
        ff.file_types = {k: 1 for k in self.file_types}
        return ff


def json_default(obj):
    """JSON serializer for objects not serializable by default json code"""
    if isinstance(obj, datetime) or isinstance(obj, date):
        serial = obj.isoformat()
        return serial
    elif isinstance(obj, set):
        return list(obj)
    raise TypeError("Type not serializable")


STRING_LIST_PATTERN = re.compile(r"<([^><]+)>")
FORM_FIELD_SPLITTER = re.compile(r"[,;<>]+")


class StringListField(models.TextField):
    description = "A field to store a list of strings in the database. '<' or '>' not allowed within strings"

    def from_db_value(self, value, expression, connection):
        return self.to_python(value)

    def to_python(self, value):
        if value is None:
            return tuple()
        if not isinstance(value, str):
            return value
        return tuple(STRING_LIST_PATTERN.findall(value))

    def get_prep_value(self, value):
        if isinstance(value, (tuple, list)):
            return "".join(["<{}>".format(v.strip()) for v in value])
        else:
            return ""

    def value_to_string(self, obj):
        value = self.value_from_object(obj)
        return self.get_prep_value(value)

    def get_prep_lookup(self, lookup_type, value):
        if isinstance(value, (tuple, list)):
            return self.get_prep_value(value)
        elif isinstance(value, str):
            return value.strip()
        else:
            return "{}".format(value)

    def formfield(self, **kwargs):
        defaults = {'form_class': DelimitedTextFormField}
        defaults.update(kwargs)
        return super(StringListField, self).formfield(**defaults)


class DelimitedTextFormField(forms.CharField):
    widget = forms.TextInput

    def to_python(self, value):
        value = super(DelimitedTextFormField, self).to_python(value)
        return filter(None, [v.strip() for v in FORM_FIELD_SPLITTER.split(value)])

    def prepare_value(self, value):
        if isinstance(value, Sequence) and not isinstance(value, str):
            return "; ".join(value)
        else:
            return value

    def clean(self, value):
        return self.to_python(value)


class AutoCodeField(models.CharField):
    def __init__(self, *args, **kwargs):
        kwargs['max_length'] = 50
        kwargs['editable'] = False
        kwargs['serialize'] = False
        self.calc = kwargs.pop('calc')
        super(AutoCodeField, self).__init__(*args, **kwargs)

    def pre_save(self, instance, add):
        setattr(instance, self.attname, self.calc)
        return getattr(instance, self.attname)

    def deconstruct(self):
        name, path, args, kwargs = super(AutoCodeField, self).deconstruct()
        for k in ['max_length', 'editable', 'serialize']:
            del kwargs[k]
        return name, path, args, kwargs
