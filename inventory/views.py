from django.shortcuts import render, redirect, get_object_or_404
from .models import Ingredient, Category
from django.http import HttpResponseBadRequest
from settings.models import Settings 
from .forms import IngredientForm, CategoryForm
from django import forms
from django.forms import modelform_factory
from django.contrib import messages 
from django.http import JsonResponse
from django.db import models
from django.forms import modelformset_factory
from django.db import transaction
from simple_history.utils import update_change_reason


def ingredient_list(request):
    # Get all categories and associated ingredients ordered by their `order` field
    categories = Category.objects.prefetch_related(
        models.Prefetch('ingredient_set', queryset=Ingredient.objects.order_by('order'))
    )
    settings_instance = Settings.objects.first()

    context = {
        'categories': categories,
        'settings': settings_instance,
    }
    return render(request, 'inventory/ingredient_list.html', context)





def row_add(request):
    # Use a formset to handle multiple rows
    IngredientFormSet = modelformset_factory(
        Ingredient,
        form=IngredientForm,
        extra=1,  # Allow for one empty form initially
        can_delete=False  # Allow rows to be removed
    )

    if request.method == 'POST':
        formset = IngredientFormSet(request.POST, queryset=Ingredient.objects.none())
        if formset.is_valid():
            # Save all rows to the database
            formset.save()
            messages.success(request, "Ingredients added successfully!")
            return redirect('inventory')
        else:
            messages.error(request, "There was an error saving the ingredients. Please try again.")
    else:
        # Initialize with no rows
        formset = IngredientFormSet(queryset=Ingredient.objects.none())

    return render(request, 'inventory/row_add.html', {'formset': formset})






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
        widgets={'quantity': forms.NumberInput(attrs={'step': '0.01', 'class': 'form-control'})},
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
                    update_change_reason(ingredient, "Inventory")                 
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




def order_inventory(request):
    CategoryFormSet = modelformset_factory(
        Category,
        form=CategoryForm,
        extra=0,
        can_delete=False,
    )

    if 'delete_category_id' in request.POST:
        delete_category_id = request.POST.get('delete_category_id')
        try:
            category = Category.objects.get(id=delete_category_id)
            category.delete()
            messages.success(request, f"Category '{category.name.title()}' deleted successfully!")
        except Category.DoesNotExist:
            messages.error(request, "The category you are trying to delete does not exist.")
        return redirect('order_inventory')
    
    if request.method == 'POST':
        # Handle category re-ordering
        for key, value in request.POST.items():
            if key.startswith('category-order-'):  # Expecting keys like 'category-order-<category_id>'
                try:
                    category_id = int(key.split('-')[-1])
                    order_value = int(value)
                    category = Category.objects.get(id=category_id)
                    category.order = order_value
                    category.save()
                except (ValueError, Category.DoesNotExist):
                    continue

        messages.success(request, "Category order updated successfully!")
        return redirect('order_inventory')

    # For GET requests, fetch categories and ingredients
    categories = Category.objects.prefetch_related(
        models.Prefetch('ingredient_set', queryset=Ingredient.objects.order_by('order'))
    )
    category_form = CategoryForm()

    context = {
        'categories': categories,
        'category_form': category_form,
    }
    return render(request, 'inventory/order_inventory.html', context)




def print_inventory(request):
    # Fetch all categories and their respective ingredients
    categories = Category.objects.prefetch_related(
        models.Prefetch('ingredient_set', queryset=Ingredient.objects.order_by('order'))
    )
    
    # Pass categories to the template
    context = {'categories': categories}
    return render(request, 'inventory/print_inventory.html', context)


def delivery_inventory(request):
    categories = Category.objects.prefetch_related('ingredient_set').all()

    # Create a form factory for updating the 'quantity' field
    InventoryForm = modelform_factory(
        Ingredient,
        fields=['quantity'],
        widgets={'quantity': forms.NumberInput(attrs={'step': '0.01', 'class': 'form-control'})},
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
                with transaction.atomic():
                    ingredient.refresh_from_db()
                    if form.cleaned_data['quantity'] is not None:
                        additional_quantity = form.cleaned_data['quantity']
                        ingredient.quantity = ingredient.quantity + additional_quantity
                        ingredient.save()
                        update_change_reason(ingredient, "Delivery") 
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
    return render(request, 'inventory/delivery_inventory.html', context)






def inventory_history(request):
    # Fetch the historical records grouped by change_id (bulk edits or solo)
    historical_records = (
        Ingredient.history
        .filter(history_change_reason__isnull=False)  # Only include tracked changes
        .order_by('-history_date')  # Order by most recent changes
    )
    
    # Group records by change_id
    grouped_changes = {}
    for record in historical_records:
        group_key = record.history_change_reason
        if group_key not in grouped_changes:
            grouped_changes[group_key] = []
        grouped_changes[group_key].append(record)

    context = {
        'grouped_changes': grouped_changes,
    }
    return render(request, 'inventory/inventory_history.html', context)