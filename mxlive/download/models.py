from django.db import models
import hashlib
from django.core.exceptions import ObjectDoesNotExist
from users.models import Project


class SecurePath( models.Model ):
    """Stores Download Keys for given paths"""
    path = models.CharField(max_length=200)
    key = models.CharField(max_length=200, db_index=True)
    owner = models.ForeignKey(Project)
    created = models.DateTimeField(auto_now_add=True, db_index=True)
        
    def save(self, *args, **kwargs):
        # create new key and save if key is not already
        # in the database
        
        h = hashlib.new('ripemd160') # no successful collisoin attacks yet
        h.update(self.path)
        self.key = h.hexdigest()
        try:
            obj = SecurePath.objects.get(key=self.key)
        except ObjectDoesNotExist:
            super(SecurePath, self).save(*args, **kwargs)

    def __str__( self ):
        return self.key

