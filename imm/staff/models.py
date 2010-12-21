# define models here
from django.db import models

try: 
    import cPickle as pickle
except ImportError:
    import pickle

from imm.lims.models import Container
from imm.lims.models import Experiment
from imm.lims.models import Crystal
from imm.lims.models import Result
from imm.lims.models import perform_action
from imm.enum import Enum
from imm.messaging.models import Message

from django.contrib.auth.models import User
from django.utils.encoding import smart_str

from django.conf import settings

class PickledObject(str):
    """A subclass of string so it can be told whether a string is
       a pickled object or not (if the object is an instance of this class
       then it must [well, should] be a pickled one)."""
    pass

class PickledObjectField(models.Field):
    __metaclass__ = models.SubfieldBase
    
    def to_python(self, value):
        if isinstance(value, PickledObject):
            # If the value is a definite pickle; and an error is raised in de-pickling
            # it should be allowed to propogate.
            return pickle.loads(smart_str(value))
        else:
            try:
                return pickle.loads(smart_str(value))
            except:
                # If an error was raised, just return the plain value
                return value
    
    def get_db_prep_save(self, value):
        if value is not None and not isinstance(value, PickledObject):
            value = PickledObject(pickle.dumps(value))
        return value
    
    def get_internal_type(self): 
        return 'TextField'
    
    def get_db_prep_lookup(self, lookup_type, value):
        if lookup_type == 'exact':
            value = self.get_db_prep_save(value)
            return super(PickledObjectField, self).get_db_prep_lookup(lookup_type, value)
        elif lookup_type == 'in':
            value = [self.get_db_prep_save(v) for v in value]
            return super(PickledObjectField, self).get_db_prep_lookup(lookup_type, value)
        else:
            raise TypeError('Lookup type %s is not supported.' % lookup_type)


        
class AutomounterLayout(models.Model):
    # contains just the locational information of an automounter
    
    # Discussion with KO
    # Each side has a field, if the field contains just an id, it's a cane that fills the whole side.
    # if the side is a list, it's a list of pucks, max size 4.
    # if the field is none, that whole side is empty
    
    left = PickledObjectField(null=True)
    middle = PickledObjectField(null=True)
    right = PickledObjectField(null=True)
    
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
                check_list = list([container.pk])
                self.left = check_list
                self.save()
                return True
            if type(check_list) == type(list()):
                if len(check_list) < 4:
                    check_list.append(container.pk)
                    self.left = check_list
                    self.save()
                    return True
            
            check_list = self.middle
            if check_list == None:
                check_list = list([container.pk])
                self.middle = check_list
                self.save()
                return True
            if type(check_list) == type(list()):
                if len(check_list) < 4:
                    check_list.append(container.pk)
                    self.middle = check_list
                    self.save()
                    return True
                
            check_list = self.right
            if check_list == None:
                check_list = list([container.pk])
                self.right = check_list
                self.save()
                return True
            if type(check_list) == type(list()):
                if len(check_list) < 4:
                    check_list.append(container.pk)
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
                    check_list.remove(container.pk)
                    self.left = check_list
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
                    check_list.remove(container.pk)
                    self.middle = check_list
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
                    check_list.remove(container.pk)
                    self.right = check_list
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
    
    def json_dict(self):
        # gives a json dictionary of the automounter config
        # TODO: Currently not real full json, just for debugging purposes.
        
        return {'left': self.left or 'None',
                'middle': self.middle or 'None',
                'right': self.right or 'None'}
    
                  
class Runlist(models.Model):
    STATES = Enum(
        'Pending', 
        'Loaded', 
        'Completed',
        'Closed',
    )
    TRANSITIONS = {
        STATES.PENDING: [STATES.LOADED],
        STATES.LOADED: [STATES.COMPLETED],
        STATES.COMPLETED: [STATES.PENDING, STATES.CLOSED],
    }
    ACTIONS = {
        'load': { 'status': STATES.LOADED, 'methods': ['check_for_other_loaded_runlists'] },
        'unload': { 'status': STATES.COMPLETED },
        'accept': { 'status': STATES.CLOSED, 'methods': ['send_accept_message'] },
        'reject': { 'status': STATES.PENDING },
    }
    status = models.IntegerField(max_length=1, choices=STATES.get_choices(), default=STATES.PENDING)
    name = models.CharField(max_length=600)
    containers = models.ManyToManyField(Container)
    priority = models.IntegerField(default=0)
    created = models.DateTimeField('date created', auto_now_add=True, editable=False)
    modified = models.DateTimeField('date modified',auto_now=True, editable=False)
    comments = models.TextField(blank=True, null=True)
    experiments = models.ManyToManyField(Experiment)
    automounter = models.ForeignKey(AutomounterLayout)
    
#    def __init__(self, *args, **kwargs):
#        mounter = AutomounterLayout()
#        mounter.save()
#        super(Runlist, self).__init__(*args, **kwargs)
#        self.automounter = mounter      
    
    def identity(self):
        return self.name
    
    def num_containers(self):
        return self.containers.count()
    
    def get_experiments(self):
        """ Returns the list of Experiments associated with this Runlist """
        # this is stupid. Why not use the experiments field
#        return_value = []
#        for container in self.containers.all():
#            for crystal in container.crystal_set.all():
#                if crystal.experiment not in return_value:
#                    return_value.append(crystal.experiment)
#        return return_value
        return self.experiments.all()
    
   # experiments = property(get_experiments)
    
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
    
    def get_children(self):
        return self.containers.all()
    
    def check_for_other_loaded_runlists(self, data=None):
        """ Checks for other Runlists in the 'loaded' state """
        already_loaded = Runlist.objects.exclude(pk=self.pk).filter(status=Runlist.STATES.LOADED).count()
        if already_loaded:
            raise ValueError('Another Runlist is already loaded.')
        
    def send_accept_message(self, data=None):
        """ Create a imm.messaging.models.Message instance when the Runlist is 'accepted' """
        admin = User.objects.get(username=settings.ADMIN_MESSAGE_USERNAME)
        
        # ensure we only send the message once to each user by keeping track of the 
        # users while iterating over the containers
        users = []
        for container in self.containers.all():
            user = container.project.user
            if user not in users:
                users.append(user)
                
        # not create a message for the user indicating the Runlist has been accepted
        for user in users:
            message = Message(sender=admin, recipient=user, subject="Admin Message", body=data.get('message', ''))
            message.save()
            
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
            auto_pos = self.automounter.get_position(container)
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
        
    def save(self, *args, **kwargs):
        super(Runlist, self).save(*args, **kwargs)
        self.automounter.reset()
        for container in self.containers.all():
            self.automounter.add_container(container)
        
            
#        if self.pk is not None:
#            orig = Runlist.objects.get(pk=self.pk)
#            # these two seem to always match. Doesn't actually give me old and new. 
#            logging.critical(self.containers.all())
#            logging.critical(orig.containers.all())
#            for container in self.containers.all():
#                logging.critical("self.pk exists, checking container")
#                if container not in orig.containers.all():
#                    logging.critical("adding")
#                    self.automounter.add_container(container)
#            for container in orig.containers.all():
#                if container not in self.containers.all():
#                    logging.critical("removing")
#                    self.automounter.remove_container(container)
#            super(Runlist, self).save(*args, **kwargs)
#        else:
#            logging.critical("pk doesn't exist, add all")
#            super(Runlist, self).save(*args, **kwargs)
#            logging.critical(self.containers.all())
#            for container in self.containers.all():
#                logging.critical("Adding")
#                self.automounter.add_container(container)
        
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
