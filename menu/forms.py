from django import forms
from .models import Menu, MenuItem, RecipeIngredient, MenuCategory
from inventory.models import Unit
from inventory.models import Ingredient, Category
from django.core.exceptions import ValidationError

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
    unit = forms.ModelChoiceField(
        queryset=Unit.objects.none(),
        label="Unit",
        widget=forms.Select(attrs={"class": "form-control"})
    )

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        # Populate ingredient_name choices
        ingredient_names = Ingredient.objects.values_list('name', flat=True).distinct()
        self.fields['ingredient_name'].choices = [(name, name) for name in ingredient_names]

        # Categories will be populated dynamically in the view
        self.fields['category'].queryset = Category.objects.all()

        # Populate unit choices if an ingredient is available
        if self.instance and self.instance.ingredient:
            self.fields['unit'].queryset = self.instance.ingredient.units.all()

    class Meta:
        model = RecipeIngredient
        fields = ['ingredient_name', 'quantity', 'category', 'unit']
        widgets = {
            'quantity': forms.NumberInput(attrs={"class": "form-control", "step": "0.000001"}),
        }

###################################################################################################

class MenuForm(forms.ModelForm):
    class Meta:
        model = Menu
        fields = ['name', 'is_secondary'] 
        labels = {
            'name': 'Menu Name',
            'is_secondary': 'Is Secondary Menu?',
        }
        widgets = {
            'is_secondary': forms.CheckboxInput(attrs={"class": "form-check-input"}),  # Bootstrap-styled checkbox
        }

class MenuCategoryForm(forms.ModelForm):
    class Meta:
        model = MenuCategory
        fields = ['name']
        labels = {'name': 'Category Name'}

    def __init__(self, *args, **kwargs):
        self.menu = kwargs.pop('menu', None)
        super().__init__(*args, **kwargs)

    def clean_name(self):
        name = self.cleaned_data['name']
        if self.menu and MenuCategory.objects.filter(name=name, menu=self.menu).exists():
            raise ValidationError(f"A category with the name '{name}' already exists in this menu.")
        return name

class MenuItemForm(forms.ModelForm):
    class Meta:
        model = MenuItem
        fields = ['name', 'description', 'cost',]
        labels = {
            'name': 'Menu Item Name',
            'description': 'Description',
            'cost': 'Cost',
        }
        widgets = {
            'cost': forms.NumberInput(attrs={"class": "form-control", "step": "0.01"}),  # Widget for cost input for menu_item_detail
        }


class MenuItemAssociationForm(forms.ModelForm):
    associated_secondary_items = forms.ModelMultipleChoiceField(
        queryset=MenuItem.objects.filter(is_secondary=True),
        required=False,
        widget=forms.CheckboxSelectMultiple
    )

    class Meta:
        model = MenuItem
        fields = ['associated_secondary_items']