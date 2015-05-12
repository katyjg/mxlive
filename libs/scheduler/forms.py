from django import forms
from django.forms.fields import DateField
from django.db.models import Q
from scheduler.models import *
from scheduler import widgets
from datetime import datetime, timedelta
from django.contrib.admin.widgets import AdminDateWidget

class DeleteForm(forms.ModelForm):
    id = forms.IntegerField(widget=forms.HiddenInput)
    
    class Meta:
        fields = ('id',)
        model = Visit
        
        
class DeleteOnCallForm(DeleteForm):
    class Meta:
        fields = ('id',)
        model = OnCall       
        
        
class AdminOnCallForm(forms.ModelForm):
    date = forms.DateField(widget=forms.HiddenInput)
    local_contact = forms.ModelChoiceField(queryset=SupportPerson.objects.all(), required=True)
    
    class Meta:
        model = OnCall
        fields = ('date','local_contact')


class AdminStatusForm(forms.ModelForm):
    mode = forms.ChoiceField(choices=Stat.STATUS_CHOICES, required=True)
    start_date = DateField(widget=widgets.LeftHalfDate, required=True)
    end_date = DateField(required=False, widget=forms.HiddenInput)
    first_shift = forms.ChoiceField(choices=Stat.SHIFT_CHOICES, widget=widgets.RightHalfSelect, required=True)
    last_shift = forms.ChoiceField(required=False, widget=forms.HiddenInput)
    num_shifts = forms.IntegerField(widget=widgets.LeftHalfInput, initial=1, label='Number of Shifts' )

    class Meta:
        model = Stat
        fields = ('mode','start_date','end_date','first_shift','last_shift','num_shifts')

    def clean(self):
        '''Override clean to check for overlapping visits'''
        cleaned_data = self.cleaned_data
        data = super(AdminStatusForm, self).clean()
        data['first_shift'] = int(data['first_shift'])

        extra_shifts = ( data['num_shifts'] - ( 3 - data['first_shift'] ))
        extra_days = extra_shifts/3 + ( bool(extra_shifts%3) and 1 or 0 )
        end_date = datetime.strptime(str(data['start_date']), '%Y-%m-%d') + timedelta(days=extra_days)
        
        data['last_shift'] = ( data['first_shift'] + data['num_shifts'] - 1 ) % 3                  
        data['end_date'] = end_date.date()
        return data


class AdminVisitForm(forms.ModelForm):
    beamline = forms.ModelChoiceField(queryset=Beamline.objects.all(), required=True, widget=forms.HiddenInput)
    proposal = forms.ModelChoiceField(queryset=Proposal.objects.all(), required=True, widget=widgets.LargeSelect, label="Active Proposal")
    description = widgets.LargeCharField(required=False)
    num_shifts = forms.IntegerField(widget=widgets.LeftHalfInput, initial=1, label='Number of Shifts' )
    first_shift = forms.IntegerField(required=True, widget=forms.HiddenInput)
    start_date = forms.DateField(widget=forms.HiddenInput)
    last_shift = forms.IntegerField(required=False, widget=forms.HiddenInput)
    end_date = forms.DateField(required=False, widget=forms.HiddenInput)
    remote = widgets.LeftCheckBoxField(required=False)
    mail_in = widgets.RightCheckBoxField(required=False)
    purchased = widgets.LeftCheckBoxField(required=False, label="Purchased Access")
    maintenance = widgets.RightCheckBoxField(required=False, label="Beamline Maintenance")
    notify = widgets.LeftCheckBoxField(required=False, label="Send E-mail Notification")
    
    class Meta:
        model = Visit
        fields = ('beamline','proposal','remote','mail_in','purchased','maintenance','description','notify','num_shifts','first_shift','start_date','last_shift','end_date')

    def __init__(self, *args, **kwargs):
        super(AdminVisitForm, self).__init__(*args, **kwargs)
        if self._meta.fields:
            self.fields.keyOrder = self._meta.fields
            if self._meta.model and hasattr(self._meta.model, 'HELP'):
                for field in self._meta.fields:
                    if not self.fields[field].help_text:
                        try:
                            self.fields[field].help_text = self._meta.model.HELP[field]
                        except KeyError:
                            pass
        if self.initial:
            self.fields['proposal'].queryset=Proposal.objects.filter(Q(expiration__gte=self.initial['start_date']) | Q(expiration=None))

    def clean(self):
        '''Override clean to check for overlapping visits'''
        cleaned_data = self.cleaned_data
        data = super(AdminVisitForm, self).clean()
        # Overlaps should apply to relevant beamline and not include self if editing
        #obj = super(AdminVisitForm, self).save(commit=False)

        extra_shifts = ( data['num_shifts'] - ( 3 - data['first_shift'] ))
        extra_days = extra_shifts/3 + ( bool(extra_shifts%3) and 1 or 0 )
        end_date = datetime.strptime(str(data['start_date']), '%Y-%m-%d') + timedelta(days=extra_days)
        
        data['last_shift'] = ( data['first_shift'] + data['num_shifts'] - 1 ) % 3                  
        data['end_date'] = end_date.date()

        blvisits = Visit.objects.filter(beamline__exact=data['beamline'])
        
        overlaps = blvisits.filter(
            Q(end_date__gt=data['start_date'],end_date__lt=data['end_date'],) 
            |
            Q(start_date__gt=data['start_date'],start_date__lt=data['end_date'],)  
            |
            Q(end_date__exact=data['end_date'],end_date__gt=data['start_date'],
              first_shift__lte=data['last_shift'],)
            |
            Q(end_date__exact=data['end_date'],start_date__lt=data['end_date'],
              last_shift__gte=data['first_shift'],)
            |
            Q(end_date__exact=data['start_date'], start_date__lt=data['start_date'],
              last_shift__gte=data['first_shift'],)
            |
            Q(start_date__exact=data['end_date'], end_date__gt=data['end_date'],
              first_shift__lte=data['last_shift'],)
            |
            Q(end_date__exact=data['end_date'],start_date__exact=data['start_date'],
              last_shift__gte=data['first_shift'],last_shift__lte=data['last_shift'],)
            |
            Q(start_date__exact=data['start_date'],start_date__lt=data['end_date'],
              first_shift__gte=data['first_shift'],)
            |
            Q(start_date__exact=data['start_date'],end_date__gt=data['start_date'],
              first_shift__lte=data['first_shift'],)
            |
            Q(start_date__exact=data['start_date'],end_date__exact=data['end_date'],
              first_shift__gte=data['first_shift'],first_shift__lte=data['last_shift'],)
        )
        
        if overlaps.count() > 0:
            conflicts = [v.proposal.display() for v in overlaps.all()]
            msg = 'This visit overlaps with existing visits:\n %s!' % (', '.join(conflicts))
            self._errors['num_shifts'] = self.error_class([msg])
            raise forms.ValidationError(msg)
        
        if not Proposal.objects.filter(pk__exact=data['proposal'].pk).filter(Q(expiration__gte=data['end_date']) | Q(expiration=None)):
            msg = 'This proposal will expire before the visit is over (on %s).' % data['proposal'].expiration.strftime('%Y-%m-%d')
            self._errors['proposal'] = self.error_class([msg])
            raise forms.ValidationError(msg)
        
        return data
    
    
class AdminEditForm(forms.ModelForm):
    id = forms.IntegerField(widget=forms.HiddenInput)
    beamline = forms.ModelChoiceField(queryset=Beamline.objects.all(), required=True)
    proposal = forms.ModelChoiceField(queryset=Proposal.objects.all(),required=True, widget=widgets.LargeSelect, label="Active Proposal")
    description = widgets.LargeCharField(required=False)
    start_date = DateField(widget=widgets.LeftHalfDate, required=True)
    end_date = DateField(widget=widgets.RightHalfDate, required=True)
    first_shift = forms.ChoiceField(choices=Visit.SHIFT_CHOICES, widget=widgets.LeftHalfSelect, required=True)
    last_shift = forms.ChoiceField(choices=Visit.SHIFT_CHOICES, widget=widgets.RightHalfSelect, required=True)
    remote = widgets.LeftCheckBoxField(required=False)
    mail_in = widgets.RightCheckBoxField(required=False)
    purchased = widgets.LeftCheckBoxField(required=False, label="Purchased Access")
    maintenance = widgets.RightCheckBoxField(required=False, label="Beamline Maintenance")
    notify = widgets.LeftCheckBoxField(required=False, label="Send E-mail Notification")
    
    class Meta:
        model = Visit
        fields = ('id','beamline','proposal','remote','mail_in','purchased','maintenance','description','notify','start_date','end_date','first_shift','last_shift')

    def __init__(self, *args, **kwargs):
        super(AdminEditForm, self).__init__(*args, **kwargs)
        if self._meta.fields:
            self.fields.keyOrder = self._meta.fields
            if self._meta.model and hasattr(self._meta.model, 'HELP'):
                for field in self._meta.fields:
                    if not self.fields[field].help_text:
                        try:
                            self.fields[field].help_text = self._meta.model.HELP[field]
                        except KeyError:
                            pass
        self.fields['proposal'].queryset=Proposal.objects.filter(Q(expiration__gte=self.initial['start_date']) | Q(expiration=None))
    
    def clean(self):
        '''Override clean to check for overlapping visits'''
        data = super(AdminEditForm, self).clean()
   
        for field in self.fields:
            try: 
                if field != 'description':
                    val = data[field]
            except:
                msg = 'Please enter a valid %s' % (field)
                self._errors[field] = self.error_class([msg])
                raise forms.ValidationError(msg)
   
        # Overlaps should apply to relevant beamline and not include self if editing
        blvisits = Visit.objects.filter(beamline__exact=data['beamline']).exclude(pk=data['id'])
        
        overlaps = blvisits.filter(
            Q(end_date__gt=data['start_date'],end_date__lt=data['end_date'],) 
            |
            Q(start_date__gt=data['start_date'],start_date__lt=data['end_date'],)  
            |
            Q(end_date__exact=data['end_date'],end_date__gt=data['start_date'],
              first_shift__lte=data['last_shift'],)
            |
            Q(end_date__exact=data['end_date'],start_date__lt=data['end_date'],
              last_shift__gte=data['first_shift'],)
            |
            Q(end_date__exact=data['start_date'], start_date__lt=data['start_date'],
              last_shift__gte=data['first_shift'],)
            |
            Q(start_date__exact=data['end_date'], end_date__gt=data['end_date'],
              first_shift__lte=data['last_shift'],)
            |
            Q(end_date__exact=data['end_date'],start_date__exact=data['start_date'],
              last_shift__gte=data['first_shift'],last_shift__lte=data['last_shift'],)
            |
            Q(start_date__exact=data['start_date'],start_date__lt=data['end_date'],
              first_shift__gte=data['first_shift'],)
            |
            Q(start_date__exact=data['start_date'],end_date__gt=data['start_date'],
              first_shift__lte=data['first_shift'],)
            |
            Q(start_date__exact=data['start_date'],end_date__exact=data['end_date'],
              first_shift__gte=data['first_shift'],first_shift__lte=data['last_shift'],)
        )
        
        if overlaps.count() > 0:
            conflicts = [v.proposal.display() for v in overlaps.all()]
            msg = 'This visit overlaps with existing visits:\n %s!' % (', '.join(conflicts))
            self._errors['proposal'] = self.error_class([msg])
            raise forms.ValidationError(msg)

        if data['start_date'] > data['end_date'] or (data['start_date'] == data['end_date'] and data['first_shift'] > data['last_shift']):
            msg = 'Starting time cannot be after ending time!'
            self._errors['start_time'] = self.error_class([msg])
            raise forms.ValidationError(msg)
        
        if not Proposal.objects.filter(pk__exact=data['proposal'].pk).filter(Q(expiration__gte=data['end_date']) | Q(expiration=None)):
            msg = 'This proposal will expire before the visit is over (on %s).' % data['proposal'].expiration.strftime('%Y-%m-%d')
            self._errors['proposal'] = self.error_class([msg])
            raise forms.ValidationError(msg)

        return data    