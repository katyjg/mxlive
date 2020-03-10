from django.db import models
from django.conf import settings
from django.utils.translation import ugettext_lazy as _
from django.utils import timezone
from django.template.loader import render_to_string
from model_utils import Choices
from model_utils.models import TimeStampedModel, TimeFramedModel

from colorfield.fields import ColorField
from datetime import datetime, timedelta

from mxlive.lims.models import Project, Beamline

from geopy import geocoders
import pytz
#from tzwhere import tzwhere
#tz = tzwhere.tzwhere()


class AccessType(models.Model):
    name = models.CharField(blank=True, max_length=30)
    color = ColorField(default="#000000")
    email_subject = models.CharField(max_length=100, verbose_name=_('Email Subject'))
    email_body = models.TextField(blank=True)

    def __str__(self):
        return self.name


class BeamlineSupport(models.Model):
    staff = models.ForeignKey(Project, related_name="support", on_delete=models.CASCADE)
    date = models.DateField()

    def __str__(self):
        return "{} {}".format(self.staff.first_name, self.staff.last_name)


class Beamtime(models.Model):
    project = models.ForeignKey(Project, related_name="beamtime", on_delete=models.CASCADE, null=True, blank=True)
    beamline = models.ForeignKey(Beamline, related_name="beamtime", on_delete=models.CASCADE)
    comments = models.TextField(blank=True)
    access = models.ForeignKey(AccessType, on_delete=models.SET_NULL, null=True)
    maintenance = models.BooleanField(default=False)
    start = models.DateTimeField(verbose_name=_('Start'))
    end = models.DateTimeField(verbose_name=_('End'))

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

    def display(self, detailed=False):
        return render_to_string('schedule/beamtime.html', {'bt': self, 'detailed': detailed})

    def notification(self):
        return self.notifications.first()

    def __str__(self):
        return "{} on {}".format(self.project, self.beamline.acronym)


class Downtime(TimeFramedModel):
    SCOPE_CHOICES = Choices(
        (0, 'FACILITY', _('Facility')),
        (1, 'BEAMLINE', _('Beamline'))
    )
    scope = models.IntegerField(choices=SCOPE_CHOICES, default=SCOPE_CHOICES.FACILITY)
    beamline = models.ForeignKey(Beamline, related_name="downtime", on_delete=models.CASCADE)
    comments = models.TextField(blank=True)

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


class EmailNotification(models.Model):
    beamtime = models.ForeignKey(Beamtime, related_name="notifications", on_delete=models.CASCADE)
    email_subject = models.CharField(max_length=100, verbose_name=_('Email Subject'))
    email_body = models.TextField(blank=True)
    send_time = models.DateTimeField(verbose_name=_('Send Time'), null=True)
    sent = models.BooleanField(default=False)

    def beamline(self):
        return self.beamtime.beamline.acronym

    def name(self):
        name = 'User'
        if self.beamtime.project:
            name = self.beamtime.project.contact_person or '{person.first_name} {person.last_name}'.format(person=self.beamtime.project)
        return name

    def start_date(self):
        return datetime.strftime(timezone.localtime(self.beamtime.start), '%A, %B %-d')

    def start_time(self):
        return datetime.strftime(timezone.localtime(self.beamtime.start), '%-I%p')

    def recipient_list(self):
        return [e for e in [self.beamtime.project.email, self.beamtime.project.contact_email] if e]

    def unsendable(self):
        late = timezone.now() > (self.send_time - timedelta(minutes=30))
        empty = not self.recipient_list()
        return any([late, empty])

    def format_info(self):
        return {
            'name': self.name(),
            'beamline': self.beamline(),
            'start_date': self.start_date(),
            'start_time': self.start_time()
        }

    def save(self, *args, **kwargs):
        # Get user's local timezone
        if not self.pk:
            locator = geocoders.Nominatim()
            try:
                address = "{user.city}, {user.province}, {user.country}".format(user=self.beamtime.project)
                _, (latitude, longitude) = locator.geocode(address)
                usertz = tz.tzNameAt(latitude, longitude)
            except:
                usertz = settings.TIME_ZONE
            t = self.beamtime.start - timedelta(days=7 + (self.beamtime.start.weekday() > 4 and self.beamtime.start.weekday() - 4 or 0))
            self.send_time = pytz.timezone(usertz).localize(datetime(year=t.year, month=t.month, day=t.day, hour=10))
            self.email_subject = self.beamtime.access.email_subject.format(**self.format_info())
            self.email_body = self.beamtime.access.email_body.format(**self.format_info())

        super().save(*args, **kwargs)
