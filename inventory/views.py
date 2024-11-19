from django.shortcuts import render, redirect, get_object_or_404
from .models import Ingredient, Category
from settings.models import Settings 
from .forms import IngredientForm, CategoryForm
from django import forms

from django.forms import modelformset_factory

def ingredient_list(request):
    # Get all categories and associated ingredients
    categories = Category.objects.prefetch_related('ingredient_set').all()
    # Retrieve the settings instance, or use a default if it doesn't exist
    settings_instance = Settings.objects.first()

    context = {
        'categories': categories,
        'settings': settings_instance,
    }
    return render(request, 'inventory/ingredient_list.html', context)

def row_add(request):
    if request.method == 'POST':
        form = IngredientForm(request.POST)
        if form.is_valid():
            form.save()
            return redirect('inventory')
    else:
        form = IngredientForm()

    return render(request, 'inventory/row_add.html', {'form': form})

def category_add(request):
    if request.method == 'POST':
        form = CategoryForm(request.POST)
        if form.is_valid():
            form.save()
            return redirect('inventory')  # Redirect to the inventory list
    else:
        form = CategoryForm()

    return render(request, 'inventory/category_add.html', {'form': form})


def take_inventory(request):
    # Create a formset for the Ingredient model with the quantity field editable
    IngredientFormSet = modelformset_factory(
        Ingredient,
        fields=('quantity',),
        extra=0,
        widgets={
            'quantity': forms.NumberInput(attrs={
                'class': 'form-control',
                'placeholder': 'Enter new quantity'
            })
        }
    )

    # Handle POST request
    if request.method == 'POST':
        formset = IngredientFormSet(request.POST, queryset=Ingredient.objects.all())
        if formset.is_valid():
            # Save the updated quantities to the database
            for form in formset:
                ingredient = form.instance  # Get the associated Ingredient instance
                if form.cleaned_data['quantity'] is not None:
                    ingredient.quantity = form.cleaned_data['quantity']
                    ingredient.save()  # Explicitly save the instance
            return redirect('inventory')  # Redirect to inventory list after saving

    else:
        formset = IngredientFormSet(queryset=Ingredient.objects.all())

    # Group forms by category for display
    categories = {}
    for form in formset:
        category = form.instance.category
        if category not in categories:
            categories[category] = []
        categories[category].append(form)

    context = {
        'categories': categories,  # Grouped forms by category
        'formset': formset,        # The entire formset
    }
    return render(request, 'inventory/take_inventory.html', context)

'''
def take_inventory(request):
    # Prefetch related ingredients for efficiency
    categories = Category.objects.prefetch_related('ingredient_set').all()

    # Dynamically create a formset for all ingredients
    IngredientFormSet = modelformset_factory(
        Ingredient,
        fields=('id', 'quantity'),
        extra=0,  # No extra forms
        labels={'quantity': 'New Quantity'},
        widgets={'quantity': forms.NumberInput(attrs={'class': 'form-control', 'placeholder': 'Enter new quantity'})}
    )

    if request.method == 'POST':
        formset = IngredientFormSet(request.POST)
        if formset.is_valid():
            formset.save()  # Save the updated quantities
            return redirect('take_inventory')  # Redirect to clear the form

    else:
        formset = IngredientFormSet(queryset=Ingredient.objects.all())

    context = {
        'categories': categories,
        'formset': formset,
    }
    return render(request, 'inventory/take_inventory.html', context)'''