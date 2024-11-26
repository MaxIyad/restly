from django import forms
from .models import Ingredient, Category, Allergen, PreppedIngredient

class IngredientForm(forms.ModelForm):

    allergens = forms.ModelMultipleChoiceField(
        queryset=Allergen.objects.all(),
        widget=forms.CheckboxSelectMultiple,
        required=False,
        label="Allergens"
    )

    class Meta:
        model = Ingredient
        fields = ['name', 'quantity', 'category', 'unit_type', 'unit_multiplier', 'unit_cost', 'threshold', 'allergens']
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
            'threshold': 'Threshold (Quantity)',
        }

    def clean(self):
        cleaned_data = super().clean()
        name = cleaned_data.get('name')
        category = cleaned_data.get('category')

        if name and category:
            # Check if an ingredient with the same name exists in the category
            if Ingredient.objects.filter(name__iexact=name, category=category).exists():
                raise forms.ValidationError(f"An ingredient named '{name}' already exists in the '{category}' category.")

        return cleaned_data


class CategoryForm(forms.ModelForm):
    class Meta:
        model = Category
        fields = ['name']
        labels = {
            'name': 'Category Name',
        }

    def clean_name(self):
        name = self.cleaned_data['name'].lower()
        if Category.objects.filter(name=name).exists():
            raise forms.ValidationError(f"A category with the name '{name.title()}' already exists.")
        return name


class AllergenForm(forms.ModelForm):
    class Meta:
        model = Allergen
        fields = ['name']



class PreppedIngredientForm(forms.ModelForm):
    class Meta:
        model = PreppedIngredient
        fields = ['name', 'category', 'parent_ingredient', 'quantity', 'prep_quantity', 'unit_type']
        widgets = {
            'category': forms.Select(),
            'parent_ingredient': forms.Select(),
        }
        labels = {
            'name': 'Prepped Ingredient Name',
            'quantity': 'Available Quantity',
            'prep_quantity': 'Quantity Required Per Unit',
        }