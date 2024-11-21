from django import forms
from .models import Menu, MenuItem, RecipeIngredient, MenuCategory
from inventory.models import Ingredient
from inventory.models import Category





class RecipeIngredientForm(forms.ModelForm):
    ingredient = forms.ModelChoiceField(
        queryset=Ingredient.objects.all(),
        label="Ingredient",
        widget=forms.Select(attrs={"class": "form-control"}),
    )
    category = forms.ModelChoiceField(
        queryset=Category.objects.none(),  # Initially empty
        label="Deplete From Category",
        widget=forms.Select(attrs={"class": "form-control"}),
    )

    def __init__(self, *args, **kwargs):
        ingredient = kwargs.pop('ingredient', None)
        super().__init__(*args, **kwargs)

        # Customize the ingredient label to include unit multiplier and type
        self.fields['ingredient'].label_from_instance = lambda obj: f"{obj.name} ({obj.unit_multiplier}{obj.unit_type})"

        # Filter categories based on the selected ingredient
        if ingredient:
            self.fields['category'].queryset = Category.objects.filter(ingredient=ingredient)
        else:
            self.fields['category'].queryset = Category.objects.all()  # Default to all if no ingredient

    class Meta:
        model = RecipeIngredient
        fields = ['ingredient', 'quantity', 'category']
        widgets = {
            'quantity': forms.NumberInput(attrs={"class": "form-control", "step": "0.01"}),
        }







###########################################################################################################################################################3

class MenuForm(forms.ModelForm):
    class Meta:
        model = Menu
        fields = ['name', 'is_active']

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