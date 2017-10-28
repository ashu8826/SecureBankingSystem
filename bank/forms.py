# myapp/forms.py
from django import forms

from .models import *

class ExternalUserForm(forms.ModelForm):
    class Meta:
        model = ExternalUser
        exclude = ('Username', 'UserType', 'PublicKey')

    def __init__(self, *args, **kwargs):
        super(ExternalUserForm, self).__init__(*args, **kwargs)
        for key in self.fields:
            self.fields[key].required = True

class InternalUserForm(forms.ModelForm):
    class Meta:
        model = InternalUser
        exclude = ('Username', 'UserType', 'AccessPrivilege', 'PIIAccess', 'SSN')

    def __init__(self, *args, **kwargs):
        super(InternalUserForm, self).__init__(*args, **kwargs)
        for key in self.fields:
            self.fields[key].required = True

class PIIInfoForm(forms.ModelForm):
    class Meta:
        model = PIIInfo
        fields = ('SSN','VisaStatus')

    def __init__(self, *args, **kwargs):
        super(PIIInfoForm, self).__init__(*args, **kwargs)
        for key in self.fields:
            self.fields[key].required = True

class UserAccessForm(forms.ModelForm):
    class Meta:
        model = UserAccess
        exclude = ('Username', 'UserType', 'UserOperation')