# define models here
from django.db import models
from lims.jsonfield import JSONField
from django.utils.translation import ugettext_lazy as _
import os
import hashlib

from imm.lims.models import Container
from imm.lims.models import Experiment
from imm.lims.models import Beamline
from imm.lims.models import Crystal
from imm.lims.models import Result
from imm.lims.models import ActivityLog
from imm.lims.models import IDENTITY_FORMAT
from imm.enum import Enum

from django.contrib.auth.models import User
from django.utils.encoding import smart_str

from django.conf import settings

def get_storage_path(instance, filename):
    return os.path.join('uploads/', 'links', filename)

def handle_uploaded_file(f):
    destination = open(get_storage_path(f))
    for chunk in f.chunks():
        destination.write(chunk)
    destination.close()

class Link(models.Model):
    TYPE = Enum(
        'iframe',
        'flash',
        'image',
        'inline',
    )
    CATEGORY = Enum(
        'News',
        'How To',
    )
    description = models.TextField(blank=False)
    category = models.IntegerField(max_length=1, choices=CATEGORY.get_choices(), blank=True, null=True)    
    frame_type = models.IntegerField(max_length=1, choices=TYPE.get_choices(), blank=True, null=True)
    url = models.URLField(verify_exists=True, max_length=200, blank=True)
    document = models.FileField(_('document'), blank=True, upload_to=get_storage_path)
    created = models.DateTimeField('date created', auto_now_add=True, editable=False)
    modified = models.DateTimeField('date modified',auto_now=True, editable=False)

    def __unicode__(self):
        return self.description

    def is_editable(self):
        return True

    def is_deletable(self):
        return True

    def identity(self):
        return self.description

    def save(self, *args, **kwargs):
        super(Link, self).save(*args, **kwargs)

class Runlist(models.Model):
    STATES = Enum(
        'Pending', 
        'Loaded', 
        'Unloaded',
        'Incomplete',
        'Completed',
        'Closed',
    )
    TRANSITIONS = {
        STATES.PENDING: [STATES.LOADED],
        STATES.LOADED: [STATES.UNLOADED],
        STATES.INCOMPLETE: [STATES.COMPLETED],
        STATES.COMPLETED: [STATES.PENDING, STATES.CLOSED],
    }
    ACTIONS = {
        'load': { 'status': STATES.LOADED, 'methods': ['check_for_other_loaded_runlists'] },
        'unload': { 'status': STATES.COMPLETED },
    }
    status = models.IntegerField(max_length=1, choices=STATES.get_choices(), default=STATES.PENDING)
    name = models.CharField(max_length=600)
    containers = models.ManyToManyField(Container)
    priority = models.IntegerField(default=0)
    created = models.DateTimeField('date created', auto_now_add=True, editable=False)
    modified = models.DateTimeField('date modified',auto_now=True, editable=False)
    comments = models.TextField(blank=True, null=True)
    experiments = models.ManyToManyField(Experiment)
    beamline = models.ForeignKey(Beamline, blank=False)

    left = JSONField(null=True)
    middle = JSONField(null=True)
    right = JSONField(null=True)
    
    def identity(self):
        return self.name
    
    def num_containers(self):
        return self.containers.count()
    
    def get_experiments(self):
        """ Returns the list of Experiments associated with this Runlist """
        return self.experiments.all()
    
    def container_list(self):
        containers = [c.label for c in self.containers.all()]
        if len(containers) > 5:
            containers = containers[:5] + ['...']
        return ', '.join(containers)

    def __unicode__(self):
        return self.name
    
    def is_deletable(self):
        return True
    
    def is_editable(self):
        return self.status == self.STATES.PENDING
    
    def is_loadable(self):
        return self.status == self.STATES.PENDING
    
    def is_unloadable(self):
        return self.status == self.STATES.LOADED
    
    def is_acceptable(self):
        return self.status == self.STATES.COMPLETED
    
    def is_rejectable(self):
        return self.status == self.STATES.COMPLETED

    def is_pdfable(self):
        return self.num_containers() > 0
    
    def check_for_other_loaded_runlists(self, data=None):
        """ Checks for other Runlists in the 'loaded' state """
        already_loaded = Runlist.objects.exclude(pk=self.pk).filter(status=Runlist.STATES.LOADED).count()
        if already_loaded:
            raise ValueError('Another Runlist is already loaded.')
        
    def send_accept_message(self, data=None):
        """ Create a message when the Runlist is 'accepted' """
        pass
            
    def label_hash(self):
        # use date of last runlist modification to determine when contents were last changed
        txt = str(self.modified)
        h = hashlib.new('ripemd160') # no successful collision attacks yet
        h.update(txt)
        return h.hexdigest()

    def container_to_location(self, container, location):
        if container.kind == Container.TYPE.CASSETTE:
            if location[0] == "L":
                if self.left == None:
                    self.left = container.pk
                    self.save()
                    return True
                elif self.left == ['']*4:
                    self.left = container.pk
                    self.save()
                    return True
                return False
            if location[0] == "M":
                if self.middle == None or self.middle == ['']*4:
                    self.middle = container.pk
                    self.save()
                    return True
                return False
            if location[0] == "R":
                if self.right == None or self.right == ['']*4:
                    self.right = container.pk
                    self.save()
                    return True
                return False
        elif container.kind == Container.TYPE.UNI_PUCK:
            #define which port to load into
            if location[0] == "L":
                port = self.left
            elif location[0] == "M":
                port = self.middle
            elif location[0] == "R":
                port = self.right

            #define the position in the port
            if location[1] == "A":
                position = 0
            elif location[1] == "B":
                position = 1
            elif location[1] == "C":
                position = 2
            elif location[1] == "D":
                position = 3

            #check if it's empty
            if port != None:
                if isinstance(port, int):
                    return False
            elif port == None:
                port = ['']*4
            
            #make the change
            port[position] = container.pk
            if location[0] == "L":
                self.left = port
            elif location[0] == "M":
                self.middle = port
            elif location[0] == "R":
                self.right = port            

            self.save()
            return True
        return False


    def add_container(self, container):
        # check container type
        if container.kind == Container.TYPE.CASSETTE:
            # cassette take all 4 potential spots. 
            if self.left == None:
                self.left = container.pk
                self.save()
                return True
            if self.middle == None:
                self.middle = container.pk
                self.save()
                return True
            if self.right == None:
                self.right = container.pk
                self.save()
                return True
            return False
        elif container.kind == Container.TYPE.UNI_PUCK:
            check_list = self.left  
            if check_list == None:
                check_list = ['']*4
            if type(check_list) == type(list()):
                for i in range(4):
                    if check_list[i] == '':
                        check_list[i] = container.pk
                        self.left = check_list
                        self.save()
                        return True
            
            check_list = self.middle
            if check_list == None:
                check_list = ['']*4
            if type(check_list) == type(list()):
                for i in range(4):
                    if check_list[i] == '':
                        check_list[i] = container.pk
                        self.middle = check_list
                        self.save()
                        return True
                
            check_list = self.right
            if check_list == None:
                check_list = ['']*4
            if type(check_list) == type(list()):
                for i in range(4):
                    if check_list[i] == '':
                        check_list[i] = container.pk
                        self.right = check_list
                        self.save()
                        return True
            
            return False
        else:
            # invalid container
            return False
    
    def remove_container(self, container):
        # need a remove method to iterate through potential lists. 
        if self.left != None:
            check_list = self.left
            if type(check_list) == type(list()):
                # iterate through the list.
                if container.pk in check_list:
                    for i in (i for i,x in enumerate(check_list) if x == container.pk):
                        self.left[i] = ''
                        self.save()
                        return True
            elif check_list == container.pk:
                check_list = None
                self.left = check_list
                self.save()
                return True
        if self.middle != None:
            check_list = self.middle
            if type(check_list) == type(list()):
                # iterate through the list.
                if container.pk in check_list:
                    for i in (i for i,x in enumerate(check_list) if x == container.pk):
                        self.middle[i] = ''
                        self.save()
                        return True
            elif check_list == container.pk:
                check_list = None
                self.middle = check_list
                self.save()
                return True
            
        if self.right != None:
            check_list = self.right
            if type(check_list) == type(list()):
                # iterate through the list.
                if container.pk in check_list:
                    for i in (i for i,x in enumerate(check_list) if x == container.pk):
                        self.right[i] = ''
                        self.save()
                        return True
            elif check_list == container.pk:
                check_list = None
                self.right = check_list
                self.save()
                return True
            
        return False
    
    def get_position(self, container):
        import logging
        # gets the position of a container in the automounter. Returns none if not in
        # making an array for the postfix letter
        postfix = ['A', 'B', 'C', 'D']
        if self.left != None:
           check_list = self.left
           if type(check_list) == type(list()):
               # iterate through the list.
               if container.pk in check_list:
                   # needs to return LA, LB, LC, or LD
                   return 'L' + postfix[check_list.index(container.pk)]
           elif check_list == container.pk:
               return 'L'
        
        if self.middle != None:
           check_list = self.middle
           if type(check_list) == type(list()):
               # iterate through the list.
               if container.pk in check_list:
                   return 'M' + postfix[check_list.index(container.pk)]
           elif check_list == container.pk:
               return 'M'
           
        if self.right != None:
           check_list = self.right
           if type(check_list) == type(list()):
               # iterate through the list.
               if container.pk in check_list:
                   return 'R' + postfix[check_list.index(container.pk)]
           elif check_list == container.pk:
               return 'R'  
    
        return None
    
    def reset(self):
        # resets the item to blank
        self.left = None
        self.middle = None
        self.Right = None
        self.save()
    
    def load(self, request=None):
        for obj in self.containers.all():
            obj.load(request)
        self.change_status(self.STATES.LOADED)    
        message = '%s (%s) loaded into automounter.' % (self.__class__.__name__.upper(), self.name)
        if request is not None:
            ActivityLog.objects.log_activity(request, self, ActivityLog.TYPE.MODIFY, message)

    def unload(self, request=None):
        for obj in self.containers.all():
            obj.unload(request)
        self.change_status(self.STATES.UNLOADED)    
        message = '%s (%s) unloaded from automounter.' % (self.__class__.__name__.upper(), self.name)
        if request is not None:
            ActivityLog.objects.log_activity(request, self, ActivityLog.TYPE.MODIFY, message)

    def change_status(self, status):
        if status == self.status:
            return
        if status not in self.TRANSITIONS[self.status]:
            raise ValueError("Invalid transition on '%s.%s':  '%s' -> '%s'" % (self.__class__, self.pk, STATES[self.status], STATES[status]))
        self.status = status
        self.save()

    def json_dict(self):
        """ Returns a json dictionary of the Runlist """
        # meta data first
        meta = {'id': self.pk, 'name': self.name}
                    
        # fetch the containers and crystals
        containers = {}
        crystals = {}
        
        for container in self.containers.all():
            container_json = container.json_dict()
            # if container is in automounter, override it's location
            auto_pos = self.get_position(container)
            if auto_pos != None:
                
                container_json['load_position'] = auto_pos
            containers[container.pk] = container_json
            for crystal_pk in container_json['crystals']:
                crystal = Crystal.objects.get(pk=crystal_pk)
                crystals[crystal.pk] = crystal.json_dict()
        
        # determine the list of Experiments in the Runlist
        experiments = []
        for experiment in self.experiments.all():
            experiment_json = experiment.json_dict()
            experiments.append(experiment_json)
        
        return {'meta': meta,
                'containers': containers, 
                'crystals': crystals, 
                'experiments': experiments}

        
def update_automounter(signal, sender, instance, **kwargs):
    if sender != Runlist:
        return
    # this checks containers on save, and calls the correct automounter functions as needed
    # compare containers in instance and current model.
    try:
        current = Runlist.objects.get(pk=instance.pk)
    except:
        current = None
        # can't do anything here as 
        return

    for container in instance.containers.all():
        if len(current.containers.all()) == 0:
            instance.automounter.add_container(container)
        if container not in current.containers.all():
            instance.automounter.add_container(container)
    for container in current.containers.all():
        if container not in instance.containers.all():
            instance.automounter.remove_container(container)
        
from django.db.models.signals import pre_save

#pre_save.connect(update_automounter, sender=Runlist)
