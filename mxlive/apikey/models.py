from django.db import models
from fields import IPNetworkField
import uuid

class APIKey(models.Model):
    client_name = models.CharField(max_length=60)
    client_email = models.EmailField(max_length=75, blank=True, null=True)
    allowed_hosts = IPNetworkField()
    allowed_methods = models.CharField(max_length=255, blank=True, default="")
    key = models.CharField(max_length=255, db_index=True, editable=False)
    active = models.BooleanField(default=False)
    created = models.DateTimeField('date created', auto_now_add=True, editable=False)
    modified = models.DateTimeField('date modified', auto_now_add=True, editable=False)

    def save(self, *args, **kwargs):
        # create new key and save if key is not already
        # set
        if self.key is None or self.key == "":
            key = "%s" % uuid.uuid4()       
            self.key = key.upper()
        super(APIKey, self).save(*args, **kwargs)
    
    
    def __unicode__(self):
        return str(self.key)
    
    class Meta:
        verbose_name = 'API Key'
        
class APIKeyUsage(models.Model):
    api_key = models.ForeignKey(APIKey)
    method = models.CharField(max_length=60)
    host   = models.GenericIPAddressField()
    created = models.DateTimeField('date created', auto_now_add=True, editable=False)
        
    def __unicode__(self):
        return str(self.api_key.key)

    class Meta:
        verbose_name = 'API Key Usage'
    
