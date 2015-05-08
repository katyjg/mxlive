from django.db import models
from dateutil import rrule
from datetime import datetime, date, timedelta
from django.utils.translation import ugettext_lazy as _
import os
from django.conf import settings

#import django.dispatch

from django.db.models.signals import post_save

def get_storage_path(instance, filename):
    return os.path.join('uploads/contacts/', 'photos', filename)


class Beamline(models.Model):
    '''
    Basic beamline information for ``Visit`` entries.
    
    '''
    name = models.CharField(blank=False,max_length=30)
    description = models.CharField(max_length=200)

    def __unicode__(self):
        """Human readable string for Beamline"""
        return self.name        
        
class Proposal(models.Model):
    '''
    Basic proposal information for ``Visit`` entries.
    '''
    first_name = models.CharField(max_length=20)
    last_name = models.CharField(max_length=20)
    email = models.EmailField(blank=True, null=True)
    proposal_id = models.CharField(max_length=7)
    description = models.CharField(max_length=200)
    expiration = models.DateTimeField(blank=True, null=True)
    account = models.CharField('PI Account', help_text="Principle Investigator's Account Name" ,max_length=300, blank=True, null=True)

    def __unicode__(self):
        """Human readable string for ``Proposal``"""
        if not self.expiration:
            return '%s, %s (%s) - SUBMITTED' % (self.last_name, self.first_name[0], self.proposal_id)
        detail = ''
        #if Proposal.objects.filter(last_name__exact=self.last_name).values('description').distinct().count() > 1:
        if 'IS' in self.last_name:
            length = 30 - len(self.last_name)
            detail = '- %s%s' % ((self.first_name + ', ' + self.description)[:length], (length < len(self.first_name + ', ' + self.description) and '...' or ' '))
            return '%s (%s)%s' % (self.last_name, self.proposal_id, detail)
        elif Proposal.objects.filter(last_name__exact=self.last_name).values('description').distinct().count() > 1:
            length = 30 - len(self.last_name)
            detail = '- %s%s' % (self.description[:length],(length < len(self.description) and '...' or ' '))
        return '%s, %s (%s)%s' % (self.last_name, self.first_name[0], self.proposal_id, detail)
    
    def display(self):
        return '%s, %s #%s' % (self.last_name, self.first_name, self.proposal_id)
 
    def account_list(self):
        return self.account and [a for a in self.account.replace(' ','').split(',')] or [self.last_name.lower()]
 
    class Meta:
        unique_together = (
            ("proposal_id"),
            )
        verbose_name = "Active Proposal"   
        ordering = ['last_name']
        
    expiration.is_active_filter = True
        
class SupportPerson(models.Model):
    '''
    Identification and contact information for ``OnCall`` entries.
    '''
    STAFF_CHOICES = (
        (0, u'Beamline Staff'),
        (1, u'Students and Postdocs'),
        (2, u'CLS Technical Support'),
    )
    first_name = models.CharField(max_length=50)
    last_name = models.CharField(max_length=50)
    position = models.CharField(max_length=100)
    email = models.EmailField()
    phone_number = models.CharField(max_length=20, help_text="Ten digit number", blank=True)
    image = models.ImageField(_('image'), blank=True, upload_to=get_storage_path)
    #image = FilerImageField(blank=True, null=True)
    office = models.CharField(blank=True, max_length=50)
    category = models.IntegerField(blank=False, choices=STAFF_CHOICES)
    
    def __unicode__(self):
        """Human readable string for ``SupportPerson``"""
        return '%s, %s' % (self.last_name, self.first_name)

    def initials(self):
        return '%c%c' % (self.first_name[0].upper(), self.last_name[0].upper())    
    
    class Meta:
        unique_together = (
            ("first_name", "last_name", "email"),
            )
        verbose_name_plural = "Personnel"

class VisitManager(models.Manager):
    use_for_related_fields = True
   
    def shift_occurences(self, dt=None, shift=None):
        '''
        Returns a queryset of for instances that have any overlap with a 
        particular shift.
        
        * ``dt`` may be either a datetime.date object, or
          ``None``. If ``None``, default to the current day.
        
        * ``shift`` an enumerated item from  ``Visit.SHIFT_CHOICES``.
        '''
        dt = dt or datetime.date(datetime.now())
        qs = self.filter(
            models.Q(
                start_date__lte=dt,
                first_shift__lte=shift,
                last_shift__gte=shift,
                end_date__gte=dt,
            )
        )
        
        return qs
                
    def week_occurences(self, dt=None):
        '''
        Returns a queryset of for instances that have any overlap with a 
        particular week.
        
        * ``dt`` is any date within the week of interest
          ``None``. If ``None``, default to the current week.
        
        * ``shift`` an enumerated item from  ``Visit.SHIFT_CHOICES``.
        '''
        if dt is None:
            dt = datetime.now()
        
        year, week, day = dt.isocalendar()
        d = date(year, 1, 4) # The Jan 4th must be in week 1  according to ISO

        start = d + timedelta(weeks=(week-1), days=-d.weekday())
        end = start + timedelta(days=6)

        qs = self.filter(
            models.Q(
                end_date__gte=start,
                #end_date__lte=end,
            ) |
            models.Q(
                #start_date__gte=start,
                start_date__lte=end,
            )                 
        )
        
        return qs
  

class Visit(models.Model):
    '''
    Represents the start and end time for a specific beamline information for ``OnCall`` entries.
    
    '''
    HELP = {
        'proposal': "Proposal titles are only shown for users with multiple proposals with different titles.",
        'description': "If an LDAP account for someone other than the PI should be used, give the account name here.",
        'mail_in': "If selected, a symbol indicating mail-in access will be displayed along with the user's last name.",
        'purchased': "If selected, only 'Purchased Access' will appear on the public CMCF schedule.",
        'remote': "If selected, a symbol indicating remote access will be displayed along with the user's last name.",
        'maintenance': "If selected, the beamline mode (colour) on the public CMCF schedule will indicate maintenance activities.",
        'notify': "If selected, an e-mail notification will be sent to the PI and to cmcf-support one week prior to the start date." 
    }
    
    SHIFT_CHOICES = (
        (0, u'08:00 - 16:00'),
        (1, u'16:00 - 24:00'),
        (2, u'24:00 - 08:00'),
    )
    
    description = models.CharField(max_length=60, blank=True)
    beamline = models.ForeignKey(Beamline)
    proposal = models.ForeignKey(Proposal, null=True)
    start_date = models.DateField(null=False)
    first_shift = models.IntegerField(choices=SHIFT_CHOICES, null=False)
    end_date = models.DateField(null=False)
    last_shift = models.IntegerField(choices=SHIFT_CHOICES, null=False)
    remote = models.BooleanField(default=False)
    mail_in = models.BooleanField(default=False)
    purchased = models.BooleanField(default=False)
    maintenance = models.BooleanField(default=False)  
    created = models.DateTimeField('date created', auto_now_add=True, editable=False)
    modified = models.DateTimeField('date modified',auto_now=True, editable=False)
    objects = VisitManager()  
    notify = models.BooleanField(default=False)  
    sent = models.BooleanField(default=False)

    def __unicode__(self):
        """Human readable string for ``Visit``"""
        return (self.proposal and self.proposal_display()) or '%s, %s to %s' % (self.description, self.start_date, self.end_date)
    
    def proposal_display(self):
        return self.proposal and self.proposal.display() or self.description
    
    def proposal_account(self):
        return self.proposal and self.proposal.account_list()[0] or None
    
    def long_notify(self):
        return self.brief_notify(long=True)
      
    def brief_notify(self, long=False):
        sd = self.first_shift < 2 and self.start_date or self.start_date + timedelta(days=1)
        fs = self.first_shift < 2 and self.get_first_shift_display() or '00:00 - 08:00'
        ed = self.last_shift < 2 and self.end_date or self.end_date + timedelta(days=1)
        ls = self.last_shift < 2 and self.get_last_shift_display() or '00:00 - 08:00'
        pre = (self.purchased and 'PURCHASED ACCESS') or (self.mail_in and 'MAIL-IN') or (self.remote and 'REMOTE') or ''
        pre = (pre and '%s - ' % pre) or ''
        suf = ((sd != ed or fs != ls) and ' (to %s - %s)' % (ed.strftime('%a, %b %d, %Y'), ls[:5])) or ''
        if long:
            return '%s%s - %s - %s%s' %(pre,self.proposal_display(),sd.strftime('%a, %b %d, %Y'),fs[:5],suf) 
        return '%s%s - %s' %(pre,self.proposal_display(),sd.strftime('%a, %b %d, %Y'))
                            
    def email_notify(self):
        startwd = (self.first_shift < 2 and self.start_date or self.start_date + timedelta(days=1)).strftime('%a')
        startsh = self.first_shift < 2 and self.get_first_shift_display()[:5] or '00:00'
        kind = (self.purchased and 'PURCHASED ACCESS') or (self.mail_in and 'MAIL-IN') or (self.remote and 'REMOTE') or ''
        if self.proposal:
            p = self.proposal
            return '%s, %s. %s\t\t(Starts %s %s)%s' % (p.proposal_id, p.first_name[0].upper(), p.last_name, startwd, startsh, (kind and '-%s' % kind or ''))
        else:
            return 'No proposal assigned\t\t(Starts %s %s)%s' % (startwd, startsh, (kind and ' -%s' % kind or ''))
                             
    def get_shifts(self, dt, ids=False):
        """Get all shifts for given date"""
        shifts = [None, None, None]

        if self.start_date <= dt <= self.end_date:
            day_first = 0
            day_last = 2
            if self.start_date == dt:
                day_first = self.first_shift
            if self.end_date == dt:
                day_last = self.last_shift
            for i in range(day_first, day_last+1):
                if ids:
                    shifts[i] = [self.description, self]
                else:
                    shifts[i] = self.description
        return shifts
    
    def get_visit_shifts(self):
        """Get all shifts for given visit"""
        day = self.start_date
        shifts = []
        while day <= self.end_date:
            for i in range(3):
                x = '%s - %s' % (day.strftime('%a, %b %d, %Y'), self.SHIFT_CHOICES[i][1])
                if self.start_date == self.end_date:
                    if i >= self.first_shift and i <= self.last_shift:
                        if x not in shifts: shifts.append(x)
                elif self.start_date == day:
                    if i >= self.first_shift:
                        if x not in shifts: shifts.append(x)
                elif self.start_date < day and self.end_date > day:
                    if x not in shifts: shifts.append(x)
                elif self.end_date == day:
                    if i <= self.last_shift:
                        if x not in shifts: shifts.append(x)
            day = day + timedelta(days=1)
        return shifts
                  
    def get_num_shifts(self):
        num = 0
        one_day = timedelta(days=1)
        if self.start_date != self.end_date:
            for i in range(3):
                if i >= self.first_shift: num += 1
            next_day = self.start_date + one_day
            while next_day < self.end_date:
                num += 3
                next_day += one_day
            for i in range(3):
                if i <= self.last_shift: num += 1
        else:
            for i in range(3):
                if i >= self.first_shift and i <= self.last_shift: num += 1
        return num
    
    class Meta:
        unique_together = (
            ("beamline", "start_date", "first_shift"),
            ("beamline", "end_date", "last_shift"),
            )
        get_latest_by = "date"
        verbose_name = "Beamline Visit"

   
class OnCallManager(models.Manager):
    use_for_related_fields = True
    
    def week_occurences(self, dt=None):
        '''
        Returns a queryset of for instances that have any overlap with a 
        particular week.
        
        * ``dt`` is any date within the week of interest
          ``None``. If ``None``, default to the current week.
        
        '''
        if dt is None:
            dt = datetime.now()
    
        start = dt - timedelta(days=dt.weekday())
        end = start + timedelta(days=6)

        
        qs = self.filter(
            models.Q(
                date__gte=start,
                date__lte=end,
            )                
        )
        
        return qs

class OnCall(models.Model):
    local_contact = models.ForeignKey(SupportPerson)
    date = models.DateField()
    objects = OnCallManager()
    
    def __unicode__(self):
        """Human readable string for ``Visit``"""
        return '%s, %s' % (self.local_contact.initials(), self.date)
        
    def initials(self):
        return self.local_contact.initials()
    
    class Meta:
        unique_together = (("local_contact", "date"),)
        get_latest_by = "date"
        verbose_name = "Local Contact"
        verbose_name_plural = "Local Contacts"

class Stat(models.Model):
    STATUS_CHOICES = (
	('Maintenance',	'Maintenance Mode'),
	('Shutdown', 	'Shutdown Mode'),
	('Development', 	'Development Mode'),
	('NormalMode', 	'Normal Mode'),
	('Special', 	'Special Request/Commissioning'),
    ('FacilityRepair',  'Unplanned Facility Repairs'),
    )
    SHIFT_CHOICES = (
        (0, u'08:00 - 16:00'),
        (1, u'16:00 - 24:00'),
        (2, u'24:00 - 08:00'),
    )
    
    mode = models.CharField(max_length=60, choices=STATUS_CHOICES)
    start_date = models.DateField(blank=True)
    first_shift = models.IntegerField(blank=True, choices=SHIFT_CHOICES)
    end_date = models.DateField(blank=True)
    last_shift = models.IntegerField(blank=False, choices=SHIFT_CHOICES)
    objects = VisitManager()    

    def __unicode__(self):
        """Human readable string for ``Visit``"""
        return '%s, %s to %s' % (self.mode, self.start_date, self.end_date)
    
    def get_shifts(self, dt):
        """Get all shifts for given date"""
        shifts = [None, None, None]
        
        if self.start_date <= dt <= self.end_date:
            day_first = 0
            day_last = 2
            if self.start_date == dt:
                day_first = self.first_shift
            if self.end_date == dt:
                day_last = self.last_shift
            for i in range(day_first, day_last+1):
                shifts[i] = self.mode
        
        return shifts
        
    class Meta:
        unique_together = (
            ("mode", "start_date", "first_shift"),
            ("mode", "end_date", "last_shift"),
            )
        get_latest_by = "date"
        verbose_name = "Facility Status"
        verbose_name_plural = "Facility Statuses"


def get_shift_lists(blname='08B1-1', first_date=datetime.now(), last_date=datetime.now()):
    data = {}
    for v in Visit.objects.filter(end_date__gte=first_date).filter(start_date__lte=last_date).filter(beamline__name=blname):
        prop = v.proposal_display()
        if prop not in data.keys(): data[prop] = []
        day = v.start_date
        last_day = v.end_date
        while day <= last_day:
            for sh in v.get_visit_shifts():
                if sh not in data[prop]:
                    data[prop].append(sh)
            day = day + timedelta(days=1)
    return data

def get_shift_mode(dt, shift):
    """Get all shifts for given date"""
    stats = Stat.objects.filter(start_date__lte=dt).filter(end_date__gte=dt).filter(first_shift__lte=shift).filter(last_shift__gte=shift)
    shift = len(stats) and stats[0].mode or None
    return shift
    
