from django.db import models
from django.contrib.auth.models import User
from imm.enum import Enum

class Message(models.Model):
    STATE = Enum('Unread', 'Read', 'Deleted')
    sender = models.ForeignKey(User, related_name='outbox')
    recipient = models.ForeignKey(User, related_name='inbox')
    subject = models.CharField(max_length=80)
    body = models.TextField()
    status = models.IntegerField(max_length=1, choices=STATE.get_choices(), default=STATE.UNREAD)
    date_sent = models.DateTimeField(auto_now_add=True)
    date_read = models.DateTimeField(null=True, blank=True)
    date_deleted = models.DateTimeField(null=True, blank=True)
    
    def __unicode__(self):
        return '%s:%s - %s' % (self.sender, self.recipient, self.subject)    

