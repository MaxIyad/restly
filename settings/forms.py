from django import forms
from .models import Settings

class SettingsForm(forms.ModelForm):
    class Meta:
        model = Settings
        fields = ['use_imperial_units', 'currency_type']

