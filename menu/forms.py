# menu/forms.py
from django import forms
from .models import Menu, MenuItem, RecipeIngredient, MenuCategory
from inventory.models import Ingredient
from inventory.models import Category



class RecipeIngredientForm(forms.ModelForm):
    ingredient_name = forms.ChoiceField(
        label="Ingredient",
        widget=forms.Select(attrs={"class": "form-control"})
    )
    category = forms.ModelChoiceField(
        queryset=Category.objects.none(),
        label="Deplete From Category",
        widget=forms.Select(attrs={"class": "form-control"})
    )

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        # Populate ingredient_name choices
        ingredient_names = Ingredient.objects.values_list('name', flat=True).distinct()
        self.fields['ingredient_name'].choices = [(name, name) for name in ingredient_names]

        # Categories will be populated dynamically in the view
        self.fields['category'].queryset = Category.objects.all()

    class Meta:
        model = RecipeIngredient
        fields = ['ingredient_name', 'quantity', 'category']
        widgets = {
            'quantity': forms.NumberInput(attrs={"class": "form-control", "step": "0.01"}),
        }




###########################################################################################################################################################3

class MenuForm(forms.ModelForm):
    class Meta:
        model = Menu
        fields = ['name']

class MenuCategoryForm(forms.ModelForm):
    class Meta:
        model = MenuCategory
        fields = ['name']
        labels = {'name': 'Category Name'}

class MenuItemForm(forms.ModelForm):
    class Meta:
        model = MenuItem
        fields = ['name', 'description']
        labels = {
            'name': 'Menu Item Name',
            'description': 'Description',
        }