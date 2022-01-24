from django import forms
from .models import Calendar, Service, Event, AvailabilityRule, RELCHOICES

class NewCalendarForm(forms.ModelForm):
    class Meta:
        model = Calendar
        fields = ['name']


class ServiceForm(forms.ModelForm):
    class Meta:
        model = Service
        fields = [
            'summary',
            ##'categories',
            'description',
            'duration',
            'price',
            'relationRequired',
            'active'
            ]
        labels = {
            'summary': 'Name',
            'relationRequired': 'Visibility'
        }
        help_texts = {
            'duration': "Please enter as hours:minutes, e.g. 1 hour, 45 minutes is written as 1:45",
            'active': "Specifies whether a service is available at the moment."
        }
        ##widgets = {
        ##    'duration': forms.MultiWidget(widgets=[forms.NumberInput,forms.NumberInput]),
        ##}
##(attrs={'max':12, 'min':0}), (attrs={'max':60, 'min':0, 'step':15})}


## This form will be primarily for custom events users want to put on their
## own calendar.  Internally debating whether users can have a method where
## they define a start time for an object, or do we instead just have events
## created from clicking a time area on the calendar...
class EventForm(forms.ModelForm):
    hours = forms.NumberInput(attrs={'max':12})
    minutes = forms.NumberInput(attrs={'max':60, 'step':15})
    class Meta:
        model = Event
        fields = [
            'summary',
            ##'categories',
            'description',
            'eventClass',
            'price',
            ##'relationRequired',
            'dtstart',
            'location'
            ]
        labels = {
            'summary': 'Name',
            'relationRequired': 'Visibility',
            'dtstart': 'Start Time'
        }

##TODO: REFORM begin, end to accomodate datetimes
class AvailabilityForm(forms.ModelForm):
    class Meta:
        model = AvailabilityRule
        fields = [
            'name',
            'begin',
            'end',
            'unavailable',
            ##'relationship', Stretch goal: Availability rules for each level of relationship
            'scope'
            ##'active'  ## Streamline creation form, we can create some sort of toggle view on this.
        ]
        labels = {
            'unavailable': 'Unavailable for Day'
        }
        ## There's probably some long boring reason why time inputs are actually text by default and don't
        ## support this firefox/chrome supported tool.  
        widgets = {
            'begin': forms.TextInput(attrs={'type': 'time'}),
            'end': forms.TextInput(attrs={'type': 'time'})
        }