from django.core.management.base import BaseCommand, CommandError
from django.core.mail import send_mail
from optparse import make_option
from scheduler.models import Visit, Proposal, Beamline
import datetime
from datetime import datetime, date, timedelta
from django.conf import settings
from django.template import loader

class Command(BaseCommand):
    args = '<visit_id>'
    help = 'Closes the specified poll for voting'

    def handle(self, *args, **options):
        """
        try:
            self.visit = Visit.objects.get(pk=args[0])
            self.proposal = self.visit.proposal
        except:
            raise CommandError('Visit %s does not exist' % args[0])
        """
        self.from_email = getattr(settings, 'FROM_EMAIL', "sender@no-reply.ca")
        self.url_root = getattr(settings, 'URL_ROOT', "")
        self.site_name = getattr(settings, 'SITE_NAME_SHORT', "")
        self.template_name = 'scheduler/user_email_body.txt'
        self.subject_template_name = "scheduler/user_email_subject.txt"

        today = datetime.now().date()
        for visit in Visit.objects.filter(start_date__exact=today+timedelta(days=7)).filter(notify__exact=True):
            self.save(visit)

    def message(self):
        """
        Render the body of the message to a string.
        
        """
        if callable(self.template_name):
            template_name = self.template_name()
        else:
            template_name = self.template_name
            
        return loader.render_to_string(template_name, dictionary={
                                            'visit': self.visit,
                                            'proposal': self.proposal,
                                            'type': self.type,
                                            'num_shifts': self.num,
                                            'start': [self.start_date, self.start_time],
                                            'site': [self.url_root, self.site_name],
                                            })

    def subject(self):
        """
        Render the subject of the message to a string.
        
        """
        now = datetime.now().date()
        date = now - timedelta(days=now.weekday())
        subject = loader.render_to_string(self.subject_template_name, dictionary={
                                            'date': date,
                                            'visit': self.visit,
                                            'site': [self.url_root, self.site_name],
                                            'type': self.type})
        return ''.join(subject.splitlines())


    def get_message_dict(self):
        """
        Generate the various parts of the message and return them in a
        dictionary, suitable for passing directly as keyword arguments
        to ``django.core.mail.send_mail()``.
    
        By default, the following values are returned:
        * ``from_email``
        * ``message``
        * ``recipient_list``
        * ``subject``
        
        """
        message_dict = {}
        for message_part in ('from_email', 'message', 'recipient_list', 'subject'):
            if message_part == 'recipient_list':
                attr = getattr(self, message_part)
            else:
                attr = getattr(self, message_part)
            message_dict[message_part] = callable(attr) and attr() or attr
        return message_dict
    
    def save(self, visit=None, fail_silently=False):
        """
        Build and send the email message.
        
        """
        self.visit = visit
        if self.visit.proposal and not self.visit.sent:
            self.proposal = self.visit.proposal
            self.type = (self.visit.remote and 'Remote') or (self.visit.mail_in and 'Mail-In') or 'Local' 
            self.recipient_list = [mail_tuple[1] for mail_tuple in settings.AUTO_SCHEDULERS]
            self.recipient_list.append(self.proposal.email)
            
            two_weeks = self.visit.start_date + timedelta(days=14)
            day = self.visit.start_date
            self.num = 0
            while day < two_weeks:
                for vis in Visit.objects.filter(proposal__exact=self.proposal).filter(start_date__lte=day):
                    self.num += len([v for v in vis.get_shifts(day) if v is not None])
                day = day + timedelta(days=1)
    
            self.start_date = self.visit.first_shift == 2 and self.visit.start_date + timedelta(days=1) or self.visit.start_date 
            self.start_time = self.visit.first_shift == 2 and "00:00" or self.visit.get_first_shift_display()
            
            message_dict = self.get_message_dict()
            send_mail(fail_silently=fail_silently, **message_dict)

            self.visit.sent = True
            self.visit.save()

