from django import forms
from .models import Sale, Cart

class AddToCartForm(forms.Form):
    ingredient_id = forms.IntegerField(widget=forms.HiddenInput())
    quantity = forms.FloatField(min_value=0.01, widget=forms.NumberInput(attrs={'step': 0.01}))

class PaymentForm(forms.ModelForm):
    class Meta:
        model = Sale
        fields = ['payment_method', 'total_amount', 'change_given']