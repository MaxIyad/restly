from django import forms
from .models import Sale


class AddToCartForm(forms.Form):
    menu_item_id = forms.IntegerField(widget=forms.HiddenInput())
    variation_id = forms.IntegerField(required=False, widget=forms.HiddenInput())
    quantity = forms.IntegerField(min_value=1, widget=forms.NumberInput(attrs={'step': 1}))

class PaymentForm(forms.ModelForm):
    class Meta:
        model = Sale
        fields = ['payment_method', 'total_amount', 'change_given']
        widgets = {
            'payment_method': forms.Select(attrs={'class': 'form-control'}),
            'total_amount': forms.NumberInput(attrs={'readonly': 'readonly'}),
            'change_given': forms.NumberInput(attrs={'class': 'form-control'}),
        }
