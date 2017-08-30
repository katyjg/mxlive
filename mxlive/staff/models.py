# define models here
from django.db import models
from django.contrib import messages
from django.utils.translation import ugettext_lazy as _
from enum import Enum
from model_utils import Choices
from jsonfield.fields import JSONField
from lims.models import ActivityLog, Beamline, Container, Sample, Group
import hashlib
import os


def get_storage_path(instance, filename):
    return os.path.join('uploads/', 'links', filename)


def handle_uploaded_file(f):
    destination = open(get_storage_path(f))
    for chunk in f.chunks():
        destination.write(chunk)
    destination.close()


class StaffBaseClass(models.Model):
    def is_deletable(self):
        return True

    def delete(self, *args, **kwargs):
        request = kwargs.get('request', None)
        message = '%s (%s) deleted.' % (
        self.__class__.__name__[0].upper() + self.__class__.__name__[1:].lower(), self.__unicode__())
        if request is not None:
            ActivityLog.objects.log_activity(request, self, ActivityLog.TYPE.DELETE, message, )
        super(StaffBaseClass, self).delete()

    class Meta:
        abstract = True


class Link(StaffBaseClass):
    TYPE = Choices(
        (0,'IFRAME','iframe'),
        (1,'FLASH','flash'),
        (2,'IMAGE','image'),
        (3,'INLINE','inline'),
        (4,'LINK','link'),
    )
    CATEGORY = Choices(
        (0,'NEWS','News'),
        (1,'HOW_TO','How To'),
    )
    description = models.TextField(blank=False)
    category = models.IntegerField(choices=CATEGORY, blank=True, null=True)
    frame_type = models.IntegerField(choices=TYPE, blank=True, null=True)
    url = models.CharField(max_length=200, blank=True)
    document = models.FileField(_('document'), blank=True, upload_to=get_storage_path)
    created = models.DateTimeField('date created', auto_now_add=True, editable=False)
    modified = models.DateTimeField('date modified', auto_now=True, editable=False)

    def __unicode__(self):
        return self.description

    def is_editable(self):
        return True

    def identity(self):
        return self.description

    def save(self, *args, **kwargs):
        super(Link, self).save(*args, **kwargs)


class UserList(StaffBaseClass):
    name = models.CharField(max_length=60, unique=True)
    description = models.TextField(blank=True, null=True)
    address = models.GenericIPAddressField()
    users = models.ManyToManyField("lims.Project", blank=True)
    active = models.BooleanField(default=False)
    created = models.DateTimeField('date created', auto_now_add=True, editable=False)
    modified = models.DateTimeField('date modified', auto_now_add=True, editable=False)

    def is_deletable(self):
        return False

    def is_editable(self):
        return True

    def current_users(self):
        return ';'.join(self.users.values_list('username', flat=True))

    def identity(self):
        return self.name

    def __unicode__(self):
        return str(self.name)

    class Meta:
        verbose_name = "Access List"
