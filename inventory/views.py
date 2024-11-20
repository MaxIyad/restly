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
from django.utils.dateparse import parse_date
from datetime import datetime, time
from django.contrib.messages import get_messages


import pandas as pd
from django.http import HttpResponse
from django.shortcuts import render


def ingredient_list(request):
    # Get all categories and associated ingredients ordered by their `order` field
    categories = Category.objects.prefetch_related(
        models.Prefetch('ingredient_set', queryset=Ingredient.objects.order_by('order'))
    )
    settings_instance = Settings.objects.first()

    # Retrieve messages
    storage = get_messages(request)
    messages_list = list(storage)

    # Separate success and error messages
    success_messages = [message for message in messages_list if 'success' in message.tags]
    error_messages = [message for message in messages_list if 'error' in message.tags]

    # Determine the single message to display
    if success_messages:
        display_message = success_messages[0]  # Show the first success message if it exists
    elif error_messages:
        display_message = error_messages[0]  # Otherwise, show the first error message
    else:
        display_message = None  # If no success or error messages, show nothing

    context = {
        'categories': categories,
        'settings': settings_instance,
        'message': display_message,  # Pass the single message to the template
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

    # Handle ingredient deletion
    if 'delete_id' in request.POST:
        delete_id = request.POST.get('delete_id')
        try:
            ingredient = Ingredient.objects.get(id=delete_id)
            ingredient.delete()
            return JsonResponse({"success": True, "message": f"Ingredient '{ingredient.name.title()}' deleted successfully!"})
        except Ingredient.DoesNotExist:
            return JsonResponse({"success": False, "error": "The ingredient you are trying to delete does not exist."})
        except Exception as e:
            return JsonResponse({"success": False, "error": str(e)})

    # Handle category deletion
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
        # Handle ingredient reordering
        for key, value in request.POST.items():
            if key.startswith('order-'):  # Expecting keys like 'order-<ingredient_id>'
                try:
                    ingredient_id = int(key.split('-')[-1])
                    order_value = int(value)
                    ingredient = Ingredient.objects.get(id=ingredient_id)
                    ingredient.order = order_value
                    ingredient.save()
                except (ValueError, Ingredient.DoesNotExist):
                    continue

        # Handle category reordering
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

        # Handle adding a new category
        category_form = CategoryForm(request.POST)
        if category_form.is_valid():
            category_form.save()
            messages.success(request, "New category added successfully!")
            return redirect('order_inventory')
        else:
            messages.error(request, "Error adding the new category. Please fix the issues and try again.")

        messages.success(request, "Orders updated successfully!")
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
    # Get filter parameters from request
    start_date = request.GET.get('start_date')
    end_date = request.GET.get('end_date')

    # Fetch the historical records
    historical_records = Ingredient.history.filter(history_change_reason__isnull=False)

    # Apply date filters if provided
    if start_date:
        start_datetime = datetime.combine(datetime.strptime(start_date, "%Y-%m-%d").date(), time.min)
        historical_records = historical_records.filter(history_date__gte=start_datetime)
    if end_date:
        end_datetime = datetime.combine(datetime.strptime(end_date, "%Y-%m-%d").date(), time.max)
        historical_records = historical_records.filter(history_date__lte=end_datetime)

    # Group records by change reason only if there are filtered results
    grouped_changes = {}
    if start_date or end_date:
        for record in historical_records.order_by('-history_date'):
            group_key = record.history_change_reason
            if group_key not in grouped_changes:
                grouped_changes[group_key] = []
            grouped_changes[group_key].append(record)

    context = {
        'grouped_changes': grouped_changes,
        'start_date': start_date,
        'end_date': end_date,
    }
    return render(request, 'inventory/inventory_history.html', context)


def export_data(data, file_format, filename_prefix):
    """Utility function to handle data export based on format."""
    current_date = datetime.now().strftime("%m-%d-%Y")  # Format date as MM-DD-YYYY
    filename = f"{filename_prefix}_{current_date}.{file_format}"

    if file_format == "csv":
        response = HttpResponse(content_type="text/csv")
        response["Content-Disposition"] = f'attachment; filename="{filename}"'
        data.to_csv(path_or_buf=response, index=False)
        return response

def export_inventory(request, file_format):
    """Export inventory data."""
    categories = Category.objects.prefetch_related(
        models.Prefetch("ingredient_set", queryset=Ingredient.objects.order_by("order"))
    )
    data = []
    for category in categories:
        for ingredient in category.ingredient_set.all():
            data.append({
                "Category": category.name.title(),
                "Name": ingredient.name.title(),
                "Quantity": ingredient.quantity,
                "Unit": f"{ingredient.unit_multiplier}{ingredient.unit_type}",
                "Unit Cost": ingredient.unit_cost,
                "Total Cost": ingredient.total_cost,
            })
    df = pd.DataFrame(data)
    return export_data(df, file_format, "Inventory")

def export_history(request, file_format):
    """Export history data."""
    # Get filter parameters from request
    start_date = request.GET.get('start_date')
    end_date = request.GET.get('end_date')

    # Fetch the historical records
    historical_records = Ingredient.history.filter(history_change_reason__isnull=False)

    # Apply date filters if provided
    if start_date:
        historical_records = historical_records.filter(history_date__gte=start_date)
    if end_date:
        historical_records = historical_records.filter(history_date__lte=end_date)

    # Prepare data for export
    data = []
    for record in historical_records.order_by("-history_date"):
        try:
            category_name = record.category.name.title() if record.category else "N/A"
        except Category.DoesNotExist:
            category_name = "Deleted Category"  # Fallback for deleted categories

        data.append({
            "Name": record.name.title(),
            "Category": category_name,
            "Change Type": record.history_type,
            "Quantity": record.quantity,
            "Date": record.history_date,
            "Reason": record.history_change_reason,
        })

    # Convert to DataFrame and export
    df = pd.DataFrame(data)
    return export_data(df, file_format, "Filtered_Inventory_History")