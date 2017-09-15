# define models here
from django.db import models
from django.contrib import messages
from django.utils.translation import ugettext_lazy as _
from enum import Enum
from model_utils import Choices
from jsonfield.fields import JSONField
from lims.models import ActivityLog, Beamline, Container, Sample, Group
import hashlib
import imghdr
import os


def get_storage_path(instance, filename):
    return os.path.join('uploads/', 'links', filename)


def handle_uploaded_file(f):
    destination = open(get_storage_path(f))
    for chunk in f.chunks():
        destination.write(chunk)
    destination.close()


class StaffBaseClass(models.Model):

    def delete(self, *args, **kwargs):
        request = kwargs.get('request', None)
        message = '%s (%s) deleted.' % (
        self.__class__.__name__[0].upper() + self.__class__.__name__[1:].lower(), self.__unicode__())
        if request is not None:
            ActivityLog.objects.log_activity(request, self, ActivityLog.TYPE.DELETE, message, )
        super(StaffBaseClass, self).delete()

    class Meta:
        abstract = True


class Announcement(StaffBaseClass):
    title = models.CharField(max_length=50, blank=True)
    description = models.TextField(blank=True)
    priority = models.IntegerField(blank=True)
    attachment = models.FileField(blank=True, upload_to=get_storage_path)
    url = models.CharField(max_length=200, blank=True)

    def has_document(self):
        return self.attachment and not self.has_image()

    def has_image(self):
        return self.attachment and imghdr.what(self.attachment)

    def __unicode__(self):
        return self.title


class UserList(StaffBaseClass):
    name = models.CharField(max_length=60, unique=True)
    description = models.TextField(blank=True, null=True)
    address = models.GenericIPAddressField()
    users = models.ManyToManyField("lims.Project", blank=True)
    active = models.BooleanField(default=False)
    created = models.DateTimeField('date created', auto_now_add=True, editable=False)
    modified = models.DateTimeField('date modified', auto_now_add=True, editable=False)

    def current_users(self):
        return ';'.join(self.users.values_list('username', flat=True))

    def identity(self):
        return self.name

    def __unicode__(self):
        return str(self.name)

    class Meta:
        verbose_name = "Access List"
