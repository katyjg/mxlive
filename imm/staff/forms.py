import logging

from imm import objforms
from imm.lims.models import Shipment
from imm.lims.models import Carrier
from imm.lims.models import Container
from imm.lims.models import Experiment
from imm.lims.models import Dewar
from imm.lims.models import Beamline
from imm.lims.models import Project
from imm.staff.models import Link

from imm.staff.models import Runlist

from django.forms.util import ErrorList

from django import forms
from django.forms import widgets

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
        required=True, initial=''
        )
    barcode = objforms.widgets.BarCodeField(required=True)
    staff_comments = objforms.widgets.CommentField(required=False)
    storage_location = objforms.widgets.CommentField(required=False)
    
    class Meta:
        model = Dewar
        fields = ('label', 'barcode', 'staff_comments', 'storage_location')
        
    def __init__(self, *args, **kwargs):
        super(DewarReceiveForm, self).__init__(*args, **kwargs)
        self.fields['label'].queryset = Dewar.objects.filter(label=self.initial.get('label', None)) or Dewar.objects.filter(status=Dewar.STATES.SENT)

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
                if experiment.exp_status != Experiment.EXP_STATES.REVIEWED:
                    return 'Experiment "%s" has not been reviewed. Click "Cancel" to complete Experiments.' % experiment.name

    def clean_return_code(self):
        cleaned_data = self.cleaned_data['return_code']
        # put this here instead of .clean() because objforms does not display form-wide error messages
        if self.instance.status != Shipment.STATES.ON_SITE:
            raise forms.ValidationError('Shipment already returned.')
        return cleaned_data
    
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
