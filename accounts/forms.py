from django import forms
from django.contrib.auth import get_user_model
from captcha.fields import CaptchaField


CustomUser = get_user_model()

class SignupForm(forms.Form):
    username = forms.CharField(max_length=150, required=True)
    pin = forms.CharField(min_length=4, max_length=4, required=True, widget=forms.PasswordInput)
    confirm_pin = forms.CharField(min_length=4, max_length=4, required=True, widget=forms.PasswordInput)

    def clean_username(self):
        username = self.cleaned_data.get("username")
        if CustomUser.objects.filter(username=username).exists():
            raise forms.ValidationError("Username is already taken.")
        return username

    def clean(self):
        cleaned_data = super().clean()
        pin = cleaned_data.get("pin")
        confirm_pin = cleaned_data.get("confirm_pin")

        if pin != confirm_pin:
            raise forms.ValidationError("PINs do not match.")
        



class LoginForm(forms.Form):
    username = forms.CharField(max_length=150)
    pin = forms.CharField(max_length=4, widget=forms.PasswordInput)
    captcha = CaptchaField()
