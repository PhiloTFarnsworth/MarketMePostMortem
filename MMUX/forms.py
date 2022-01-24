from django import forms
from .models import User, Relationship, Profile
from MMcalendar.models import RELCHOICES

class LoginForm(forms.ModelForm):
    class Meta:
        model = User
        fields = ['username', 'password']

class RegisterForm(forms.ModelForm):
    confirm = forms.CharField(widget=forms.PasswordInput())
    class Meta:
        model = User
        fields = [
            'username',
            'password',
            'confirm',
            'first_name',
            'last_name',
            'email',
            'serviceTool',
            'defaultTZ',
 
            ]
        widgets = {
            'password': forms.PasswordInput()
        }
        labels = {
            'confirm': 'Confirm Password',
            'serviceTool': 'Service Manager',
            'socialTool': 'Social Media Manager',
            'mediaTool': 'Multi-media Manager'
        }
        help_texts = {
            'serviceTool': "Enable MarketMe's service offering tool",
            'socialTool': "Enable MarketMe's social Manager Tool",
            'mediaTool': "Enable MarketMe's Multi-Media Manager."
        }

class UserSettings(forms.ModelForm):
    class Meta:
        model = User
        fields = ['first_name', 
            'last_name', 
            'serviceTool', 
            'defaultTZ',
            ##'socialTool', Stretch ideas
            ##'mediaTool' Stretch ideas
            ]
        labels = {
            'serviceTool': 'Service Manager',
            'socialTool': 'Social Media Manager',
            'mediaTool': 'Multi-media Manager'
        }
        help_texts = {
            'serviceTool': "Enable MarketMe's service offering tool",
            'socialTool': "Enable MarketMe's social Manager Tool",
            'mediaTool': "Enable MarketMe's Multi-Media Manager."
        }

class RelationshipManager(forms.ModelForm):
    level = forms.ChoiceField(choices=RELCHOICES)
    class Meta:
        model = Relationship
        fields = ['level']

class ProfileForm(forms.ModelForm):
    class Meta:
        model = Profile
        fields = [
            'publicContact',
            'location',
            'markupContents',
            'primaryColor',
            'image'
        ]
        widgets = {
            ## Some people just want to see the world burn.  There's more than
            ## a few python packages that enable color inputs, but since we
            ## we're going to store the Hex value as string anyway, I think it's 
            ## a working solution.
            'primaryColor': forms.TextInput(attrs={'type': 'color'})
        }
        labels = {
            'primaryColor': 'Favorite Color?',
            'markupContents': 'Contents',
            'mailingList': 'Mailing List',
            'publicContact': 'Client-Facing Email Address'
        }
        help_texts = {
            'markupContents': 'See our Markup guide to make a personalized portal for your business'
        }