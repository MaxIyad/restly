from django import forms
from .models import Ingredient, Category, Allergen, PreppedIngredient, Unit

class IngredientForm(forms.ModelForm):

    allergens = forms.ModelMultipleChoiceField(
        queryset=Allergen.objects.all(),
        widget=forms.CheckboxSelectMultiple,
        required=False,
        label="Allergens"
    )

    class Meta:
        model = Ingredient
        fields = ['name', 'category', 'unit_type', 'unit_multiplier', 'unit_cost', 'threshold', 'allergens']
        widgets = {
            'category': forms.Select(),
            'unit_type': forms.Select(),
        }
        labels = {
            'name': 'Ingredient Name',
            'category': 'Category',
            'unit_type': 'Unit Type',
            'unit_multiplier': 'Delivery Unit Amount',
            'unit_cost': 'Delivery Unit Cost',
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

class UnitForm(forms.ModelForm):
    class Meta:
        model = Unit
        fields = ['name', 'multiplier']
        labels = {
            'name': 'Unit Name',
            'multiplier': 'Multiplier',
        }
        

    def clean(self):
        cleaned_data = super().clean()
        name = cleaned_data.get('name')
        multiplier = cleaned_data.get('multiplier')
        
        # Allow the form to be valid if both fields are empty
        if not name and not multiplier:
            return cleaned_data  # Valid empty form
        
        # Ensure both fields are filled if one is provided
        if (name and not multiplier) or (multiplier and not name):
            raise forms.ValidationError(
                "Both 'name' and 'multiplier' are required if one is provided."
            )
        
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




