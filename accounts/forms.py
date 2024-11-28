from django import forms
from django.contrib.auth import get_user_model
from captcha.fields import CaptchaField


CustomUser = get_user_model()

class SignupForm(forms.Form):
    username = forms.CharField(max_length=150, required=True)
    email = forms.EmailField(required=True)
    password = forms.CharField(min_length=8, max_length=128, required=True, widget=forms.PasswordInput)
    confirm_password = forms.CharField(min_length=8, max_length=128, required=True, widget=forms.PasswordInput)
    pin = forms.CharField(min_length=4, max_length=20, required=True, widget=forms.PasswordInput)
    confirm_pin = forms.CharField(min_length=4, max_length=20, required=True, widget=forms.PasswordInput)

    def clean_email(self):
        email = self.cleaned_data.get("email")
        if CustomUser.objects.filter(email=email).exists():
            raise forms.ValidationError("Email is already in use.")
        return email

    def clean_username(self):
        username = self.cleaned_data.get("username")
        if " " in username:
            raise forms.ValidationError("The username cannot contain spaces.")
        if CustomUser.objects.filter(username=username).exists():
            raise forms.ValidationError("Username is already taken.")
        return username

    def clean(self):
        cleaned_data = super().clean()
        password = cleaned_data.get("password")
        confirm_password = cleaned_data.get("confirm_password")
        pin = cleaned_data.get("pin")
        confirm_pin = cleaned_data.get("confirm_pin")

        if password != confirm_password:
            raise forms.ValidationError("Passwords do not match.")
        if pin != confirm_pin:
            raise forms.ValidationError("PINs do not match.")
        return cleaned_data
        



class LoginForm(forms.Form):
    username = forms.CharField(max_length=150, label="Username")
    password = forms.CharField(max_length=128, widget=forms.PasswordInput, label="Password")
    captcha = CaptchaField(label="Captcha")
