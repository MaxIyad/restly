# inventory/views.py:

from django.shortcuts import render, redirect, get_object_or_404
from .models import Ingredient, Category, Allergen, Unit
from django.forms.models import inlineformset_factory
from settings.models import Settings 
from .forms import IngredientForm, CategoryForm, AllergenForm, PreppedIngredientForm, UnitForm
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
from django.core.exceptions import ValidationError



import pandas as pd
from django.http import HttpResponse
from django.shortcuts import render


def ingredient_list(request):
    # Get all categories and associated ingredients ordered by their `order` field
    categories = Category.objects.prefetch_related(
        models.Prefetch(
            "ingredient_set",
            queryset=Ingredient.objects.filter(visible=True).order_by("order")
        )
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
    }
    return render(request, 'inventory/ingredient_list.html', context)





def row_add(request):
    IngredientFormSet = modelformset_factory(Ingredient, form=IngredientForm, extra=1, can_delete=False)
    UnitInlineFormSet = inlineformset_factory(Ingredient, Unit, form=UnitForm, extra=1, can_delete=True)

    if request.method == 'POST':
        formset = IngredientFormSet(request.POST, queryset=Ingredient.objects.none())
        if formset.is_valid():
            ingredients = formset.save()
            for ingredient in ingredients:
                unit_formset = UnitInlineFormSet(request.POST, instance=ingredient)
                if unit_formset.is_valid():
                    unit_formset.save()
            messages.success(request, "Ingredients and units added successfully!")
            return redirect('inventory')
        else:
            messages.error(request, "There was an error saving the ingredients. Please try again.")
    else:
        formset = IngredientFormSet(queryset=Ingredient.objects.none())

    return render(request, 'inventory/row_add.html', {'formset': formset, 'unit_formset': UnitInlineFormSet})












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
    categories = Category.objects.prefetch_related('ingredient_set__units').all()
    
    if request.method == 'POST':
        updated_count = 0
        with transaction.atomic():
            for ingredient in Ingredient.objects.prefetch_related('units'):
                for unit in ingredient.units.all():
                    quantity_key = f"unit_quantity_{unit.id}"
                    if quantity_key in request.POST and request.POST[quantity_key]:
                        try:
                            unit_quantity = float(request.POST[quantity_key])
                            unit.quantity = unit_quantity  # Update unit's quantity
                            unit.save()
                            updated_count += 1
                        except ValueError:
                            messages.error(request, f"Invalid quantity for {unit.name}.")
            messages.success(request, f"Inventory updated for {updated_count} units.")

        return redirect('inventory')

    context = {
        'categories': categories,
    }
    return render(request, 'inventory/take_inventory.html', context)

'''def take_inventory(request):
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
    return render(request, 'inventory/take_inventory.html', context)'''



def order_inventory(request):
    

    if request.method == 'POST':
        # Get all ingredient IDs in the POST request
        ingredient_ids = [int(key.split('-')[-1]) for key in request.POST.keys() if key.startswith("visible-")]

        # Update visibility for all ingredients
        for ingredient in Ingredient.objects.all():
            ingredient.visible = ingredient.id in ingredient_ids  # Mark as visible if checkbox exists
            ingredient.save()

        messages.success(request, "Ingredient visibility updated successfully!")

        # Handle other updates (e.g., categories, names, etc.)
        error_messages = []  # Collect error messages for invalid updates
        valid_updates = []  # Collect objects for bulk saving after validation

        # Handle ingredient deletion
        if 'delete_id' in request.POST:
            try:
                ingredient_id = int(request.POST.get('delete_id'))
                ingredient = Ingredient.objects.get(id=ingredient_id)
                ingredient.delete()
                return JsonResponse({"success": True, "message": "Ingredient deleted successfully!"})
            except Ingredient.DoesNotExist:
                return JsonResponse({"success": False, "error": "Ingredient does not exist."})
            except Exception as e:
                return JsonResponse({"success": False, "error": str(e)})
        
        if 'delete_category_id' in request.POST:
            try:
                category_id = int(request.POST.get('delete_category_id'))
                category = Category.objects.get(id=category_id)
                category.delete()
                messages.success(request, f"Category '{category.name}' and its ingredients were deleted successfully!")
                return redirect('order_inventory')
            except Category.DoesNotExist:
                messages.error(request, "The category you are trying to delete does not exist.")
                return redirect('order_inventory')
            except Exception as e:
                messages.error(request, f"An unexpected error occurred: {e}")
                return redirect('order_inventory')

        # Handle category deletion
        if 'add_category' in request.POST:
            category_form = CategoryForm(request.POST)
            if category_form.is_valid():
                category_form.save()
                messages.success(request, "Category added successfully!")
            else:
                messages.error(request, "Error adding category. Please correct the errors below.")
        else:
            category_form = CategoryForm()

        # Process updates for ingredients and categories
        for key, value in request.POST.items():            
            try:
                if key.startswith('ingredient-category-'):
                    ingredient_id = int(key.split('-')[-1])
                    new_category_id = int(value)
                    ingredient = Ingredient.objects.get(id=ingredient_id)
                    new_category = Category.objects.get(id=new_category_id)
                    if ingredient.category.id != new_category.id:  # Only update if the category has changed
                        ingredient.category = new_category
                        ingredient.save()
                elif key.startswith('category-name-'):
                    category_id = int(key.split('-')[-1])
                    category = Category.objects.get(id=category_id)
                    category.name = value.strip()
                    category.full_clean()  # Validate before saving
                    category.save()
                elif key.startswith('category-order-'):
                    category_id = int(key.split('-')[-1])
                    category = Category.objects.get(id=category_id)
                    category.order = int(value)
                    category.save()
                # Update ingredient order
                elif key.startswith('order-'):
                    ingredient_id = int(key.split('-')[-1])
                    ingredient = Ingredient.objects.get(id=ingredient_id)
                    ingredient.order = int(value)
                    ingredient.save()  # Ensure save is called immediately after updating the field

                # Update ingredient name
                elif key.startswith('name-'):
                    ingredient_id = int(key.split('-')[-1])
                    ingredient = Ingredient.objects.get(id=ingredient_id)
                    ingredient.name = value.strip()
                    ingredient.full_clean()  # Validate before saving
                    ingredient.save()

                # Update ingredient quantity
                elif key.startswith('quantity-'):
                    ingredient_id = int(key.split('-')[-1])
                    ingredient = Ingredient.objects.get(id=ingredient_id)
                    ingredient.quantity = float(value)
                    ingredient.save()

                # Update ingredient unit type
                elif key.startswith('unit_type-'):
                    ingredient_id = int(key.split('-')[-1])
                    ingredient = Ingredient.objects.get(id=ingredient_id)
                    ingredient.unit_type = value.strip()
                    ingredient.save()

                # Update ingredient unit multiplier
                elif key.startswith('unit_multiplier-'):
                    ingredient_id = int(key.split('-')[-1])
                    ingredient = Ingredient.objects.get(id=ingredient_id)
                    ingredient.unit_multiplier = float(value)
                    ingredient.save()

            except (ValueError, Ingredient.DoesNotExist) as e:
                error_messages.append(f"Error processing {key}: {e}")
            except ValidationError as e:
                error_messages.append(f"Validation error for {key}: {e.message_dict}")

        # Save all valid updates for ingredients
        for obj in valid_updates:
            try:
                obj.save()  # Explicit save for each object
            except Exception as e:
                error_messages.append(f"Error saving object {obj.id}: {e}")

        # Display messages
        if error_messages:
            for error in error_messages:
                messages.error(request, error)
        else:
            messages.success(request, "Updates saved successfully!")       

        return redirect('order_inventory')

    # Handle GET requests
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
    """Export filtered inventory history."""
    # Get filter parameters from request
    start_date = request.GET.get('start_date')
    end_date = request.GET.get('end_date')
    change_type = request.GET.get('change_type')  # New parameter to filter by change type

    # Fetch historical records with filtering
    historical_records = Ingredient.history.filter(history_change_reason__isnull=False)

    if start_date:
        start_datetime = datetime.combine(datetime.strptime(start_date, "%Y-%m-%d").date(), time.min)
        historical_records = historical_records.filter(history_date__gte=start_datetime)
    if end_date:
        end_datetime = datetime.combine(datetime.strptime(end_date, "%Y-%m-%d").date(), time.max)
        historical_records = historical_records.filter(history_date__lte=end_datetime)

    # Filter by change type if provided
    if change_type:
        historical_records = historical_records.filter(history_change_reason=change_type)

    # Prepare data for export
    data = []
    for record in historical_records.order_by("-history_date"):
        try:
            category_name = record.category.name.title() if record.category else "N/A"
        except Category.DoesNotExist:
            category_name = "Deleted Category"

        data.append({
            "Name": record.name.title(),
            "Category": category_name,
            "Change Type": record.history_type,
            "Quantity": record.quantity,
            "Date": record.history_date.strftime("%Y-%m-%d %H:%M:%S"),
            "Reason": record.history_change_reason,
        })

    # Convert data to DataFrame and export
    df = pd.DataFrame(data)
    return export_data(df, file_format, f"Filtered_{change_type}_History")


def ingredient_details(request, category_slug, slug):
    category = get_object_or_404(Category, slug=category_slug)
    ingredient = get_object_or_404(
        Ingredient,
        category=category,
        slug=slug
    )
    history = ingredient.history.all().order_by('-history_date')

    AllergenFormSet = modelform_factory(
        Ingredient,
        fields=['allergens'],
        widgets={'allergens': forms.CheckboxSelectMultiple},
    )
    allergen_form = AllergenFormSet(instance=ingredient)

    if request.method == "POST":
        allergen_form = AllergenFormSet(request.POST, instance=ingredient)
        if allergen_form.is_valid():
            allergen_form.save()
            messages.success(request, "Allergens updated successfully!")
            return redirect('ingredient_details', category_slug=category_slug, slug=slug)
        else:
            messages.error(request, "Error updating allergens. Please try again.")

    # Pre-process history for the template
    processed_history = []
    for record in history:
        change_type = "Changed"
        if record.history_type == '+':
            change_type = "Added"
        elif record.history_type == '-':
            change_type = "Removed"
        elif record.history_change_reason == "Inventory":
            change_type = "Quantity: Inventory"
        elif record.history_change_reason == "Delivery":
            change_type = "Quantity: Delivery"
        elif record.history_change_reason == "Order":
            change_type = "Order"
        elif record.history_change_reason in ["Unit Multiplier", "Unit Type"]:
            change_type = "Unit"

        processed_history.append({
            "date": record.history_date,
            "change_type": change_type,
            "order": record.order,
            "quantity": record.quantity,
            "unit_type": record.unit_type,
            "unit_multiplier": record.unit_multiplier,
            "user": "admin",  # Placeholder for user
        })

    context = {
        'ingredient': ingredient,
        'history': history,
        'allergen_form': allergen_form,
    }
    return render(request, 'inventory/ingredient_details.html', context)





def allergen_add(request):
    if request.method == 'POST':
        form = AllergenForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, "Allergen added successfully!")
            return redirect('allergen_add') 
        else:
            messages.error(request, "Error adding allergen. Please correct the errors.")
    else:
        form = AllergenForm()

    allergens = Allergen.objects.all().order_by('name')  

    context = {
        'form': form,
        'allergens': allergens,
    }
    return render(request, 'inventory/allergen_add.html', context)

def allergen_details(request, allergen_id):
    allergen = get_object_or_404(Allergen, id=allergen_id)
    ingredients = allergen.ingredients.all().select_related('category')

    context = {
        'allergen': allergen,
        'ingredients': ingredients,
    }
    return render(request, 'inventory/allergen_details.html', context)


def allergen_delete(request, allergen_id):
    allergen = get_object_or_404(Allergen, id=allergen_id)
    if request.method == 'POST':
        allergen.delete()
        messages.success(request, "Allergen deleted successfully!")
        return redirect('allergen_add')
    





def prepped_ingredient_add(request):
    if request.method == 'POST':
        form = PreppedIngredientForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, "Prepped ingredient added successfully!")
            return redirect('inventory')
        else:
            messages.error(request, "Error adding prepped ingredient. Please correct the errors below.")
    else:
        form = PreppedIngredientForm()

    return render(request, 'inventory/prepped_ingredient_add.html', {'form': form})


def prepped_ingredient_list(request):
    prepped_ingredients = PreppedIngredient.objects.select_related('parent_ingredient', 'category').all()
    context = {
        'prepped_ingredients': prepped_ingredients,
    }
    return render(request, 'inventory/prepped_ingredient_list.html', context)




def waste_inventory(request):
    categories = Category.objects.prefetch_related('ingredient_set').all()

    # Create a form factory for updating the 'quantity' and 'waste_reason' fields
    InventoryForm = modelform_factory(
        Ingredient,
        fields=['quantity', 'waste_reason'],
        widgets={
            'quantity': forms.NumberInput(attrs={'step': '0.01', 'class': 'form-control'}),
            'waste_reason': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Reason for wastage'}),
        },
    )

    ingredient_forms = {}

    if request.method == 'POST':
        updated_count = 0
        for ingredient in Ingredient.objects.all():
            InventoryForm.base_fields['quantity'].required = False
            InventoryForm.base_fields['waste_reason'].required = False

            form = InventoryForm(request.POST, instance=ingredient, prefix=f"ingredient-{ingredient.id}")
            ingredient_forms[ingredient.id] = form

            if form.is_valid():
                with transaction.atomic():
                    ingredient.refresh_from_db()
                    if form.cleaned_data['quantity'] is not None:
                        wasted_quantity = form.cleaned_data['quantity']
                        ingredient.quantity = ingredient.quantity - wasted_quantity
                        ingredient.waste_reason = form.cleaned_data['waste_reason']
                        ingredient.save()
                        update_change_reason(ingredient, "Waste")
                        updated_count += 1

        if updated_count > 0:
            messages.success(request, f"Waste recorded successfully! {updated_count} ingredient{'s' if updated_count > 1 else ''} updated.")
        else:
            messages.info(request, "No changes were made to the inventory.")

        return redirect('inventory')

    for ingredient in Ingredient.objects.all():
        InventoryForm.base_fields['quantity'].required = False
        InventoryForm.base_fields['waste_reason'].required = False
        ingredient_forms[ingredient.id] = InventoryForm(instance=None, prefix=f"ingredient-{ingredient.id}")

    context = {
        'categories': categories,
        'ingredient_forms': ingredient_forms,
    }
    return render(request, 'inventory/waste_inventory.html', context)