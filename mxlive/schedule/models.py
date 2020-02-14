from django.db import models
from django.conf import settings
from django.utils.translation import ugettext_lazy as _
from django.utils import timezone

from colorfield.fields import ColorField
from datetime import datetime, timedelta

from mxlive.lims.models import Project, Beamline


class AccessType(models.Model):
    name = models.CharField(blank=True, max_length=30)
    color = ColorField(default="#000000")

    def __str__(self):
        return self.name


class BeamlineProject(models.Model):
    project = models.ForeignKey(Project, related_name="projects", on_delete=models.CASCADE, blank=True, null=True)
    number = models.CharField(max_length=10, verbose_name=_('Project ID'))
    title = models.CharField(max_length=255, verbose_name=_('Title'))
    expiration = models.DateField(verbose_name=_('Expiration Date'))
    email = models.EmailField(blank=True, null=True)

    class Meta:
        unique_together = ("number",)
        verbose_name = "Active Projects"

    def __str__(self):
        return "{} {}".format(self.number, self.project and "({})".format(self.project) or "")


class BeamlineSupport(models.Model):
    staff = models.ForeignKey(Project, related_name="support", on_delete=models.CASCADE)
    date = models.DateField()

    def __str__(self):
        return "{} {}".format(self.staff.first_name, self.staff.last_name)


class Beamtime(models.Model):
    project = models.ForeignKey(BeamlineProject, related_name="beamtime", on_delete=models.CASCADE, null=True)
    beamline = models.ForeignKey(Beamline, related_name="beamtime", on_delete=models.CASCADE)
    comments = models.TextField(blank=True)
    access = models.ManyToManyField(AccessType)
    start = models.DateTimeField(verbose_name=_('Start'))
    end = models.DateTimeField(verbose_name=_('End'))

    notify = models.BooleanField(default=False)
    sent = models.BooleanField(default=False)

    @property
    def start_time(self):
        return datetime.strftime(timezone.localtime(self.start), '%Y-%m-%dT%H')

    @property
    def end_time(self):
        return datetime.strftime(timezone.localtime(self.end), '%Y-%m-%dT%H')

    @property
    def start_times(self):
        st = self.start
        slot = settings.HOURS_PER_SHIFT
        start_times = []
        while st < self.end:
            start_times.append(datetime.strftime(timezone.localtime(st), '%Y-%m-%dT%H'))
            st += timedelta(hours=slot)

        return start_times


    def access_types(self):
        return [a.name for a in self.access.all()]

    def display(self):
        return "{}{}".format(self.project.__str__(), self.comments and "..." or "")

    def __str__(self):
        return self.beamline.name


