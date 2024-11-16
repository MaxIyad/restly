from django import forms
from .models import Ingredient, Category

class IngredientForm(forms.ModelForm):
    
    class Meta:
        model = Ingredient
        fields = ['name', 'quantity', 'category', 'unit_type', 'unit_multiplier', 'unit_cost', 'threshold']
        widgets = {
            'category': forms.Select(),
            'unit_type': forms.Select(),
        }
        labels = {
            'name': 'Ingredient Name',
            'quantity': 'Quantity',
            'category': 'Category',
            'unit_type': 'Unit Type',
            'unit_multiplier': 'Unit Multiplier',
            'unit_cost': 'Unit Cost',
            'threshold': 'Threshold',
        }

class CategoryForm(forms.ModelForm):
    class Meta:
        model = Category
        fields = ['name']
        labels = {
            'name': 'Category Name',
        }