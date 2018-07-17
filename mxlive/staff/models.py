# define models here
from django.db import models
from lims.models import ActivityLog, Beamline, Container, Sample, Group
from model_utils import Choices
import imghdr
import os


def get_storage_path(instance, filename):
    return os.path.join('uploads/', 'links', filename)


class StaffBaseClass(models.Model):

    def delete(self, *args, **kwargs):
        request = kwargs.get('request', None)
        message = '%s (%s) deleted.' % (self.__class__.__name__[0].upper() + self.__class__.__name__[1:].lower(),
                                        self.__unicode__())
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

    def allowed_users(self):
        return ';'.join(self.users.values_list('username', flat=True))

    def current_users(self):
        return ';'.join(self.connections.filter(status__in=['Connected', 'Disconnected'])
                        .values_list('user__username', flat=True).distinct())

    def identity(self):
        return self.name

    def __unicode__(self):
        return str(self.name)

    class Meta:
        verbose_name = "Access List"


class UserCategory(models.Model):
    name = models.CharField(max_length=100)
    projects = models.ManyToManyField("lims.Project", blank=True, related_name="categories")

    def current_users(self):
        return '; '.join(self.projects.values_list('username', flat=True))

    def num_users(self):
        return self.projects.count()
    num_users.short_description = 'Number'

    def __unicode__(self):
        return self.name

    class Meta:
        verbose_name = "User Category"
        verbose_name_plural = "User Categories"


class RemoteConnection(StaffBaseClass):
    STATES = Choices(
        ('CONNECTED', 'Connected'),
        ('DISCONNECTED', 'Disconnected'),
        ('FAILED', 'Failed'),
        ('FINISHED', 'Finished'),
    )
    name = models.CharField(max_length=48)
    user = models.ForeignKey("lims.Project")
    list = models.ForeignKey(UserList, related_name="connections")
    status = models.CharField(choices=STATES, default=STATES.CONNECTED, max_length=20)
    created = models.DateTimeField('date created', auto_now_add=True, editable=True)
    end = models.DateTimeField('date ended', null=True, blank=True)

    def is_active(self):
        return self.status in ['Connected', 'Disconnected']

    def total_time(self):
        return (self.end - self.created).total_seconds()/3600.
    total_time.short_description = "Duration"