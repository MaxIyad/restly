from django.shortcuts import render, redirect, get_object_or_404
from .models import Ingredient, Category
from django.http import HttpResponseBadRequest
from settings.models import Settings 
from .forms import IngredientForm, CategoryForm
from django import forms
from django.forms import modelform_factory
from django.contrib import messages 
from django.http import JsonResponse

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
    categories = Category.objects.prefetch_related('ingredient_set').all()

    # Create a form factory for updating the 'quantity' field
    InventoryForm = modelform_factory(
        Ingredient,
        fields=['quantity'],
        widgets={'quantity': forms.NumberInput(attrs={'step': '0.01', 'class': 'form-control', 'placeholder': 'Optional'})},
        field_classes={'quantity': forms.FloatField},
    )

    # Dictionary to store forms for each ingredient
    ingredient_forms = {}

    if request.method == 'POST':
        updated_count = 0
        for ingredient in Ingredient.objects.all():
            # Make the field optional by overriding the 'required' attribute
            InventoryForm.base_fields['quantity'].required = False

            form = InventoryForm(request.POST, instance=ingredient, prefix=f"ingredient-{ingredient.id}")
            ingredient_forms[ingredient.id] = form  # Save the form in the dictionary

            if form.is_valid():
                # Only save the ingredient if 'quantity' is not empty
                if form.cleaned_data['quantity'] is not None:
                    form.save()
                    updated_count += 1
        if updated_count > 0:
            messages.success(request, f"Inventory updated successfully! {updated_count} ingredient{'s' if updated_count > 1 else ''} updated.")
        else:
            messages.info(request, "No changes were made to the inventory.")

        return redirect('inventory')

    # Populate forms for GET requests
    for ingredient in Ingredient.objects.all():
        InventoryForm.base_fields['quantity'].required = False  # Ensure field is optional for GET requests
        ingredient_forms[ingredient.id] = InventoryForm(instance=None, prefix=f"ingredient-{ingredient.id}")

    context = {
        'categories': categories,
        'ingredient_forms': ingredient_forms,  # Pass the forms to the template
    }
    return render(request, 'inventory/take_inventory.html', context)



def drag_inventory(request):
    if request.method == 'POST':
        # Handle row deletion
        if 'delete_id' in request.POST:
            ingredient_id = request.POST['delete_id']
            ingredient = get_object_or_404(Ingredient, id=ingredient_id)
            ingredient.delete()
            return JsonResponse({'success': True, 'message': 'Row deleted successfully.'})

        # Handle reordering
        if 'order' in request.POST:
            new_order = request.POST.getlist('order[]')  # Expecting a list of IDs
            for index, ingredient_id in enumerate(new_order):
                ingredient = Ingredient.objects.get(id=ingredient_id)
                ingredient.order = index
                ingredient.save()
            return JsonResponse({'success': True, 'message': 'Order updated successfully.'})

    # For GET requests, render the drag-and-drop page
    ingredients = Ingredient.objects.all()
    context = {'ingredients': ingredients}
    return render(request, 'inventory/drag_inventory.html', context)