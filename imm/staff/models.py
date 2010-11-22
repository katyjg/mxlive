# define models here
from django.db import models

from imm.lims.models import Container
from imm.lims.models import Experiment
from imm.lims.models import Crystal
from imm.lims.models import Result
from imm.lims.models import perform_action
from imm.enum import Enum
from imm.messaging.models import Message

from django.contrib.auth.models import User

from django.conf import settings

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
    
    def identity(self):
        return self.name
    
    def num_containers(self):
        return self.containers.count()
    
    def get_experiments(self):
        """ Returns the list of Experiments associated with this Runlist """
        return_value = []
        for container in self.containers.all():
            for crystal in container.crystal_set.all():
                if crystal.experiment not in return_value:
                    return_value.append(crystal.experiment)
        return return_value
    
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
        
        # fetch the containers and crystals
        containers = {}
        crystals = {}
        for container in self.containers.all():
            container_json = container.json_dict()
            containers[container.pk] = container_json
            for crystal_pk in container_json['crystals']:
                crystal = Crystal.objects.get(pk=crystal_pk)
                crystals[crystal.pk] = crystal.json_dict()
        
        # determine the list of Experiments in the Runlist
        experiments = []
        for experiment in self.experiments.all():
            experiment_json = experiment.json_dict()
            experiments.append(experiment_json)
        
        return {'containers': containers, 
                'crystals': crystals, 
                'experiments': experiments}