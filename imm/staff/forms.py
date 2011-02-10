import logging

from imm import objforms
from imm.lims.models import Shipment
from imm.lims.models import Carrier
from imm.lims.models import Container
from imm.lims.models import Experiment
from imm.lims.models import Dewar
from imm.lims.models import Beamline
from imm.staff.models import Link

from imm.staff.models import Runlist

from django.forms.util import ErrorList

from django import forms
from django.forms import widgets

class ShipmentReceiveForm(objforms.forms.OrderedForm):
    """ Form used to receive a Shipment, based on the courier tracking_code """
    tracking_code = objforms.widgets.BarCodeField(required=True)
    staff_comments = objforms.widgets.CommentField(required=False)
    
    class Meta:
        model = Shipment
        fields = ('tracking_code', 'staff_comments')
        
    def clean_tracking_code(self):
        cleaned_data = self.cleaned_data['tracking_code']
        if cleaned_data != self.instance.tracking_code:
            raise forms.ValidationError('Mismatched tracking code. Expected "%s". Did you scan the correct Shipment?' % self.instance.tracking_code)
        # put this here instead of .clean() because objforms does not display form-wide error messages
        if self.instance.status != Shipment.STATES.SENT:
            raise forms.ValidationError('Shipment already received.')
        return cleaned_data
    
class DewarForm(objforms.forms.OrderedForm):
    comments = objforms.widgets.CommentField(required=False)
    storage_location = objforms.widgets.CommentField(required=False)
    class Meta:
        model = Dewar
        fields = ('comments', 'storage_location')
    
class DewarReceiveForm(objforms.forms.OrderedForm):
    """ Form used to receive a Dewar, based on the Dewar upc code """
    label = forms.ModelChoiceField(
        queryset=Dewar.objects.filter(status=Dewar.STATES.SENT),
        widget=objforms.widgets.LargeSelect,
        help_text='Please select the Dewar to receive.',
        required=True
        )
    barcode = objforms.widgets.BarCodeField(required=True)
    staff_comments = objforms.widgets.CommentField(required=False)
    storage_location = objforms.widgets.CommentField(required=False)
    
    class Meta:
        model = Dewar
        fields = ('label', 'barcode', 'staff_comments', 'storage_location')
        
    def clean(self):
        cleaned_data = self.cleaned_data
        barcode = cleaned_data.get("barcode")
        label = cleaned_data.get("label")
        if label:
            try:
                instance = self.Meta.model.objects.get(label__exact=label)
                if instance.status != Dewar.STATES.SENT:
                    raise forms.ValidationError('Dewar already received.')
                if instance.barcode() != barcode:
                    self._errors['barcode'] = self._errors.get('barcode', ErrorList())
                    self._errors['barcode'].append('Incorrect barcode.')
                    raise forms.ValidationError('Incorrect barcode.')
                self.instance = instance
            except Dewar.DoesNotExist:
                raise forms.ValidationError('No Dewar found with matching tracking code. Did you scan the correct Shipment?')
        return cleaned_data
      
class ShipmentReturnForm(objforms.forms.OrderedForm):
    """ Form used to return a Shipment """
    carrier = forms.ModelChoiceField(
        queryset=Carrier.objects.all(),
        widget=objforms.widgets.LargeSelect,
        help_text='Please select the carrier company.',
        required=True
        )
    return_code = objforms.widgets.LargeCharField(required=True)

    class Meta:
        model = Shipment
        fields = ('carrier', 'return_code')
        
    def warning_message(self):
        """ Returns a warning message to display in the form - accessed in objforms/plain.py """
        shipment = self.instance
        if shipment:
            for experiment in shipment.project.experiment_set.all():
                if experiment.status != Experiment.STATES.CLOSED:
                    return 'Experiment "%s" is not complete. Click "Cancel" to complete Experiments.' % experiment.name

    def clean_return_code(self):
        cleaned_data = self.cleaned_data['return_code']
        # put this here instead of .clean() because objforms does not display form-wide error messages
        if self.instance.status != Shipment.STATES.ON_SITE:
            raise forms.ValidationError('Shipment already returned.')
        return cleaned_data
    
class ExperimentSelectForm(objforms.forms.OrderedForm):
    experiment = forms.ModelMultipleChoiceField(queryset=Experiment.objects.all(), 
                                                error_messages={'required' : 'Please select an Experiment.'})
    
    class Meta:
        model = Experiment
        fields = ('experiment',)
    
    def primary_error_message(self):
        error = ''
        if self.errors:
            error = 'Error.'
        if self.errors.has_key('experiment'):
            error = self.errors['experiment'][0]
        return error
    
class ContainerSelectForm(objforms.forms.OrderedForm):
    experiment = forms.ModelMultipleChoiceField(queryset=Experiment.objects.all(),
                                                error_messages={'required' : 'Please select an Experiment.'})
    container = forms.ModelMultipleChoiceField(queryset=Container.objects.all(),
                                               error_messages={'required' : 'Please select a Container.'})
    
    class Meta:
        model = Container
        fields = ('experiment', 'container')
    
    NUM_STALLS = 3
    NUM_PUCKS_PER_STALL = 4
    NUM_CASSETTES_PER_STALL = 1
    
    def clean(self):
        cleaned_data = self.cleaned_data
        containers = cleaned_data.get('container', [])
        
        if containers:
            
            # check for invalid container types
            for container in containers:
                if container.kind not in [Container.TYPE.CASSETTE, Container.TYPE.UNI_PUCK]:
                    raise forms.ValidationError('Container "%s" has an invalid type "%s".' % (container.label, Container.TYPE[container.kind]))
                
            # check for cassette and pucks
            num_cassettes = 0
            num_pucks = 0
            for container in containers:
                num_cassettes +=  int(container.kind == Container.TYPE.CASSETTE)
                num_pucks += int(container.kind == Container.TYPE.UNI_PUCK)
                
            # check for > 3 cassettes
            if num_cassettes > self.NUM_STALLS * self.NUM_CASSETTES_PER_STALL:
                raise forms.ValidationError('Cannot have more than %d Containers of type "%s".' % 
                                            (self.NUM_STALLS * self.NUM_CASSETTES_PER_STALL, Container.TYPE[Container.TYPE.CASSETTE]))
                
            # check for > 12 pucks
            if num_pucks > self.NUM_STALLS * self.NUM_PUCKS_PER_STALL:
                raise forms.ValidationError('Cannot have more than %d Containers of type "%s".' % 
                                            (self.NUM_STALLS * self.NUM_PUCKS_PER_STALL, Container.TYPE[Container.TYPE.UNI_PUCK]))
            
            # fill the 3 stalls with either 1 cassette or 4 pucks
            for i in range(3):
                if num_cassettes:
                    num_cassettes -= self.NUM_CASSETTES_PER_STALL
                elif num_pucks:
                    num_pucks -= self.NUM_PUCKS_PER_STALL
            
            # check for leftovers
            if num_cassettes > 0:
                raise forms.ValidationError('Too many Containers of type "%s".' % Container.TYPE[Container.TYPE.CASSETTE])
            
            if num_pucks > 0:
                raise forms.ValidationError('Too many Containers of type "%s".' % Container.TYPE[Container.TYPE.UNI_PUCK])
                
        return cleaned_data
    
    def primary_error_message(self):
        error = ''
        if self.errors:
            error = 'Error.'
        if self.errors.has_key('__all__'):
            error = self.errors['__all__'][0]
        elif self.errors.has_key('container'):
            error = self.errors['container'][0]
        return error
    
class RunlistForm(objforms.forms.OrderedForm):
    """ Form used to create a Runlist """
    name = objforms.widgets.LargeCharField(required=True)
    beamline = forms.ModelChoiceField(
        queryset=Beamline.objects.all(),
        widget=objforms.widgets.LargeSelect,
        required=True
        )
    comments = objforms.widgets.CommentField(required=False)

    class Meta:
        model = Runlist
        fields = ('name', 'beamline', 'comments') #, 'experiments', 'containers')
        
    def _update(self):
        cleaned_data = self.cleaned_data
       # experiments = cleaned_data.get('experiments', [])
        
        # containers don't have experiments. Need to go to crystals in container, iterate them, 
            # and add container once one crystal is in the experiment...
        #choices = Container.objects.all().filter(crystal.experiment=experiments)
        
        #self.fields['containers'].queryset = choices
        
        
class RunlistEmptyForm(objforms.forms.OrderedForm):
    """ Form used to load/complete a Runlist """
    name = forms.CharField(widget=widgets.HiddenInput)
    
    class Meta:
        model = Runlist
        fields = ('name',)
        
class RunlistAcceptForm(objforms.forms.OrderedForm):
    """ Form used to load/complete a Runlist """
    message = objforms.widgets.CommentField(initial="Here is a default message to send when a Runlist is accepted.")
    
    class Meta:
        model = Runlist
        fields = ('message',)
        

class LinkForm(objforms.forms.OrderedForm):
    description = objforms.widgets.SmallTextField(required=True)
    category = forms.ChoiceField(choices=Link.CATEGORY.get_choices(), widget=objforms.widgets.LeftHalfSelect, required=False)
    frame_type = forms.ChoiceField(choices=Link.TYPE.get_choices(), widget=objforms.widgets.RightHalfSelect, required=False)
    url = forms.URLField(widget=objforms.widgets.LargeInput, label='External Web site', required=False)
    document = forms.Field(widget=objforms.widgets.LargeFileInput, required=False)

    class Meta:
        model = Link
        fields = ('description','category','frame_type','url','document')

    def _update(self):
        cleaned_data = self.cleaned_data

'''
    def save(self):
        print "saving"
        link = Link(description=self.cleaned_data['description'],category=self.cleaned_data['category'],frame_type=self.cleaned_data['frame_type'],url=self.cleaned_data['url'])
        link.save()
        return link


frm.cleaned_data['name']
        uploaded_file = self.cleaned_data['document']
        import re
        stored_name = re.sub(r'[^a-zA-Z0-9._]+', '-', uploaded_file.name)
        self.bound_object.document.save(stored_name, uploaded_file)
        self.bound_object.mimetype = uploaded_file.content_type
        

 
    def save(self, *args, **kwargs):
        super(GalleryUpload, self).save(*args, **kwargs)
        gallery = self.process_zipfile()
        super(GalleryUpload, self).delete()
        return gallery

    def process_zipfile(self):
        if os.path.isfile(self.zip_file.path):
            # TODO: implement try-except here
            zip = zipfile.ZipFile(self.zip_file.path)
            bad_file = zip.testzip()
            if bad_file:
                raise Exception('"%s" in the .zip archive is corrupt.' % bad_file)
            count = 1
            if self.gallery:
                gallery = self.gallery
            else:
                gallery = Gallery.objects.create(title=self.title,
                                                 title_slug=slugify(self.title),
                                                 description=self.description,
                                                 is_public=self.is_public,
                                                 tags=self.tags)
            from cStringIO import StringIO
            for filename in zip.namelist():
                if filename.startswith('__'): # do not process meta files
                    continue
                data = zip.read(filename)
                if len(data):
                    try:
                        # the following is taken from django.newforms.fields.ImageField:
                        #  load() is the only method that can spot a truncated JPEG,
                        #  but it cannot be called sanely after verify()
                        trial_image = Image.open(StringIO(data))
                        trial_image.load()
                        # verify() is the only method that can spot a corrupt PNG,
                        #  but it must be called immediately after the constructor
                        trial_image = Image.open(StringIO(data))
                        trial_image.verify()
                    except Exception:
                        # if a "bad" file is found we just skip it.
                        continue
                    while 1:
                        title = ' '.join([self.title, str(count)])
                        slug = slugify(title)
                        try:
                            p = Photo.objects.get(title_slug=slug)
                        except Photo.DoesNotExist:
                            photo = Photo(title=title,
                                          title_slug=slug,
                                          caption=self.caption,
                                          is_public=self.is_public,
                                          tags=self.tags)
                            photo.image.save(filename, ContentFile(data))
                            gallery.photos.add(photo)
                            count = count + 1
                            break
                        count = count + 1
            zip.close()
            return gallery




























'''
