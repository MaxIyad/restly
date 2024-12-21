from django import forms
from .models import Sale
from accounts.models import Customer



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

class CustomerForm(forms.ModelForm):
    class Meta:
        model = Customer
        fields = ['name', 'phone', 'email', 'address', 'allergens', 'notes']
        widgets = {
            'name': forms.TextInput(attrs={'class': 'form-control'}),
            'phone': forms.TextInput(attrs={'class': 'form-control'}),
            'email': forms.EmailInput(attrs={'class': 'form-control'}),
            'address': forms.Textarea(attrs={'class': 'form-control'}),
            'allergens': forms.Textarea(attrs={'class': 'form-control'}),
            'notes': forms.Textarea(attrs={'class': 'form-control'}),
        }
