# menu/views.py:
from django.shortcuts import render, get_object_or_404, redirect
from django.http import JsonResponse
from .models import Menu, MenuItem, RecipeIngredient
from inventory.models import Ingredient
from .forms import MenuForm, MenuCategoryForm, MenuCategory, RecipeIngredientForm, MenuItemForm
from django.contrib import messages
from decimal import Decimal
from django.db.models import Prefetch
from django.db import models

from django.http import JsonResponse
from inventory.models import Category


def menu_list(request):
    menus = Menu.objects.all()
    error_flag = False
    

    if request.method == "POST":

        
        # Check for activation changes
        menu_id = request.POST.get('menu_id')
        if menu_id:
            menu = Menu.objects.get(id=menu_id)
            menu.is_active = not menu.is_active 
            menu.save()
            messages.success(request, f"Menu '{menu.name}' is now active!")
            return redirect('menu_list')
        
        if "delete_menu_id" in request.POST:
            menu_id = int(request.POST["delete_menu_id"])
            menu = get_object_or_404(Menu, id=menu_id)
            menu.delete()
            messages.success(request, f"Menu '{menu.name}' deleted successfully!")
            return redirect("menu_list")

        # Handle new menu creation
        form = MenuForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, "Menu added successfully!")
            return redirect('menu_list')
        else:
            error_flag = True
    else:
        form = MenuForm()

    context = {
        'menus': menus,
        'form': form,
        'error_flag': error_flag,
    }
    return render(request, 'menu/menu_list.html', context)



def menu_detail(request, menu_slug):
    menu = get_object_or_404(Menu, slug=menu_slug)
    categories = menu.categories.prefetch_related("items")

    category_form = MenuCategoryForm()
    item_form = MenuItemForm()

    if request.method == "POST":

        if "delete_category_id" in request.POST:
            category_id = int(request.POST["delete_category_id"])
            category = get_object_or_404(MenuCategory, id=category_id, menu=menu)
            category.delete()
            messages.success(request, f"Category '{category.name}' deleted successfully!")
            return redirect("menu_detail", menu_slug=menu.slug)

        elif "delete_item_id" in request.POST:
            item_id = int(request.POST["delete_item_id"])
            item = get_object_or_404(MenuItem, id=item_id, category__menu=menu)
            item.delete()
            messages.success(request, f"Menu item '{item.name}' deleted successfully!")
            return redirect("menu_detail", menu_slug=menu.slug)
        
        elif "add_category" in request.POST: 
            category_form = MenuCategoryForm(request.POST, menu=menu)
            if category_form.is_valid():
                category = category_form.save(commit=False)
                category.menu = menu
                category.save()
                messages.success(request, f"Category '{category.name}' added to menu '{menu.name}'.")
                return redirect('menu_detail', menu_slug=menu_slug)
            else:
                messages.error(request, "Failed to add category. Please check the form.")

        elif "add_menu_item" in request.POST:  
            category_id = request.POST.get("category_id")
            category = get_object_or_404(MenuCategory, id=category_id, menu=menu)
            item_form = MenuItemForm(request.POST)
            if item_form.is_valid():
                menu_item = item_form.save(commit=False)
                menu_item.category = category
                menu_item.save()
                messages.success(request, f"Menu item '{menu_item.name}' added to category '{category.name}'.")
                return redirect('menu_detail', menu_slug=menu_slug)
            else:
                messages.error(request, "Failed to add menu item. Please check the form.")

    context = {
        'menu': menu,
        'categories': categories,
        'category_form': category_form,
        'menu_item_form': item_form,
    }
    return render(request, 'menu/menu_detail.html', context)





'''
def category_detail(request, menu_slug, category_slug):
    menu = get_object_or_404(Menu, slug=menu_slug)
    category = get_object_or_404(MenuCategory, slug=category_slug, menu=menu)
    menu_items = category.items.all()

    if request.method == "POST":
        if "add_menu_item" in request.POST:
            # Handle adding a new menu item
            menu_item_form = MenuItemForm(request.POST)
            if menu_item_form.is_valid():
                menu_item = menu_item_form.save(commit=False)
                menu_item.category = category
                menu_item.save()
                messages.success(request, f"Menu item '{menu_item.name}' added to category '{category.name}'.")
                return redirect('category_detail', menu_name=menu_slug, category_name=category_slug)

    else:
        menu_item_form = MenuItemForm()

    context = {
        'menu': menu,
        'category': category,
        'menu_items': menu_items,
        'menu_item_form': menu_item_form,
    }
    return render(request, 'menu/category_detail.html', context)

'''





######################################################################################################















def menu_item_detail(request, menu_slug, category_slug, menu_item_slug):
    menu = get_object_or_404(Menu, slug=menu_slug)
    category = get_object_or_404(MenuCategory, slug=category_slug, menu=menu)
    menu_item = get_object_or_404(MenuItem, slug=menu_item_slug, category=category)
    recipe_ingredients = menu_item.recipe_ingredients.select_related('ingredient', 'category')

    total_ingredient_cost = Decimal(0)  # Use Decimal for monetary values
    for ingredient in recipe_ingredients:
        ingredient.calculated_price = Decimal(ingredient.quantity) * Decimal(ingredient.ingredient.unit_cost)
        total_ingredient_cost += ingredient.calculated_price

    # Calculate margin (default to 0 if no cost)
    margin = Decimal(0)
    if menu_item.cost and total_ingredient_cost > 0:
        margin = ((menu_item.cost - total_ingredient_cost) / total_ingredient_cost) * 100
        margin = round(margin, 2)

    if request.method == "POST":

        cost = request.POST.get("cost")
        margin = request.POST.get("margin")

        if cost:
            try:
                menu_item.cost = float(cost)
                menu_item.save()
                messages.success(request, f"Cost for '{menu_item.name}' updated successfully.")
            except ValueError:
                messages.error(request, "Invalid cost value.")

        elif margin:
            try:
                margin_percentage = float(margin)
                menu_item.cost = round(total_ingredient_cost * (1 + margin_percentage / 100), 2)
                menu_item.save()
                messages.success(request, f"Margin for '{menu_item.name}' updated successfully.")
            except ValueError:
                messages.error(request, "Invalid margin value.")



        # Menu item sell price form
        elif "update_cost" in request.POST:
            cost = request.POST.get("cost")
            if cost:
                try:
                    menu_item.cost = float(cost)
                    menu_item.save()
                    messages.success(request, f"Cost for '{menu_item.name}' updated successfully.")
                except ValueError:
                    messages.error(request, "Invalid cost value.")
            else:
                messages.error(request, "Cost cannot be empty.")

        elif "add_ingredient" in request.POST:
            ingredient_name = request.POST.get("ingredient_name")
            category_id = request.POST.get("category")
            quantity = request.POST.get("quantity")

            # Validation
            if not ingredient_name:
                messages.error(request, "Please select an ingredient to add.")
                return redirect('menu_item_detail', menu_slug=menu_slug, category_slug=category_slug, menu_item_slug=menu_item_slug)
            if not category_id:
                messages.error(request, "Please select a category for the ingredient.")
                return redirect('menu_item_detail', menu_slug=menu_slug, category_slug=category_slug, menu_item_slug=menu_item_slug)
            if not quantity:
                messages.error(request, "Please specify the quantity.")
                return redirect('menu_item_detail', menu_slug=menu_slug, category_slug=category_slug, menu_item_slug=menu_item_slug)

            # Create and save the ingredient
            ingredient = Ingredient.objects.filter(name=ingredient_name, category_id=category_id).first()

            if not ingredient:
                messages.error(request, "The selected ingredient does not exist.")
                return redirect('menu_item_detail', menu_slug=menu_slug, category_slug=category_slug, menu_item_slug=menu_item_slug)

            RecipeIngredient.objects.create(
                menu_item=menu_item,
                ingredient=ingredient,
                category=ingredient.category,
                quantity=quantity
            )
            messages.success(request, f"Ingredient '{ingredient.name}' added to '{menu_item.name}'.")
            return redirect('menu_item_detail', menu_slug=menu_slug, category_slug=category_slug, menu_item_slug=menu_item_slug)

        elif "remove_ingredient" in request.POST:
            ingredient_id = request.POST.get("ingredient_id")
            recipe_ingredient = get_object_or_404(RecipeIngredient, id=ingredient_id, menu_item=menu_item)
            recipe_ingredient.delete()
            messages.success(request, f"Ingredient '{recipe_ingredient.ingredient.name}' removed from '{menu_item.name}'.")
            return redirect('menu_item_detail', menu_slug=menu_slug, category_slug=category_slug, menu_item_slug=menu_item_slug)

    recipe_ingredient_form = RecipeIngredientForm()

    context = {
        'menu': menu,
        'margin': margin,
        'category': category,
        'menu_item': menu_item,
        'recipe_ingredients': recipe_ingredients,
        'total_ingredient_cost': total_ingredient_cost,
        'recipe_ingredient_form': recipe_ingredient_form,
    }
    return render(request, 'menu/menu_item_detail.html', context)


#################################################################################################################################################


def get_categories_for_ingredient(request):
    ingredient_name = request.GET.get('ingredient_name')
    if not ingredient_name:
        return JsonResponse({'error': 'No ingredient name provided'}, status=400)

    try:
        # Fetch all ingredients with the given name
        ingredients = Ingredient.objects.filter(name__iexact=ingredient_name)
        categories_data = []

        for ingredient in ingredients:
            categories_data.append({
                'id': ingredient.category.id,
                'name': ingredient.category.name,
                'unit_multiplier': ingredient.unit_multiplier,
                'unit_type': ingredient.unit_type,
            })

        return JsonResponse({'categories': categories_data})
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)








def simulate_order(request, menu_slug, category_slug, menu_item_slug):
    menu = get_object_or_404(Menu, slug=menu_slug)
    category = get_object_or_404(MenuCategory, slug=category_slug, menu=menu)
    menu_item = get_object_or_404(MenuItem, slug=menu_item_slug, category=category)
    recipe_ingredients = menu_item.recipe_ingredients.all()
    warnings = []

    # Deduct ingredient quantities only from the specified category
    for recipe_ingredient in recipe_ingredients:
        ingredient = recipe_ingredient.ingredient
        category_to_deplete = recipe_ingredient.category

        if category_to_deplete is None:
            warnings.append(f"Category for {ingredient.name} is not specified!")
            continue

        # Fetch the ingredient with the matching name and category
        try:
            ingredient_in_category = Ingredient.objects.get(
                name=ingredient.name,
                category=category_to_deplete
            )
        except Ingredient.DoesNotExist:
            warnings.append(f"{ingredient.name} does not exist in the {category_to_deplete.name} category!")
            continue

        # Subtract the quantity, allowing for negative values
        ingredient_in_category.quantity -= recipe_ingredient.quantity
        ingredient_in_category.save()

        # Add a warning if the ingredient goes below zero
        if ingredient_in_category.quantity < 0:
            warnings.append(
                f"{ingredient.name} in category {category_to_deplete.name} is now in deficit ({ingredient_in_category.quantity})."
            )

    if warnings:
        messages.warning(request, " ".join(warnings))
    else:
        messages.success(request, f"Order for '{menu_item.name}' simulated successfully!")
  
    return redirect('menu_detail', menu_slug=menu_slug)


def order_menu(request, menu_slug):
    menu = get_object_or_404(Menu, slug=menu_slug)
    categories = menu.categories.prefetch_related(
        models.Prefetch('items', queryset=MenuItem.objects.order_by('order'))
    )
    error_messages = []  # Collect error messages for invalid updates

    if request.method == 'POST':

        # Handle item deletion
        if 'delete_item_id' in request.POST:
            try:
                item_id = int(request.POST.get('delete_item_id'))
                item = MenuItem.objects.get(id=item_id)
                item.delete()
                messages.success(request, f"Menu item '{item.name}' deleted successfully!")
                return redirect('order_menu', menu_slug=menu.slug)
            except MenuItem.DoesNotExist:
                messages.error(request, "Menu item does not exist.")
                return redirect('order_menu', menu_slug=menu.slug)

        # Handle category deletion
        if 'delete_category_id' in request.POST:
            try:
                category_id = int(request.POST.get('delete_category_id'))
                category = MenuCategory.objects.get(id=category_id, menu=menu)
                category.delete()
                messages.success(request, f"Category '{category.name}' and its items were deleted successfully!")
                return redirect('order_menu', menu_slug=menu.slug)
            except MenuCategory.DoesNotExist:
                messages.error(request, "Category does not exist.")
                return redirect('order_menu', menu_slug=menu.slug)

        # Process updates for categories and menu items
        for key, value in request.POST.items():
            try:
                if key.startswith('category-name-'):
                    category_id = int(key.split('-')[-1])
                    category = MenuCategory.objects.get(id=category_id, menu=menu)
                    category.name = value.strip()
                    category.full_clean()  # Validate before saving
                    category.save()
                elif key.startswith('category-order-'):
                    category_id = int(key.split('-')[-1])
                    category = MenuCategory.objects.get(id=category_id, menu=menu)
                    category.order = int(value)
                    category.save()
                elif key.startswith('item-name-'):
                    item_id = int(key.split('-')[-1])
                    item = MenuItem.objects.get(id=item_id, category__menu=menu)
                    item.name = value.strip()
                    item.full_clean()  # Validate before saving
                    item.save()
                elif key.startswith('item-order-'):
                    item_id = int(key.split('-')[-1])
                    item = MenuItem.objects.get(id=item_id, category__menu=menu)
                    item.order = int(value)
                    item.save()
                elif key.startswith('item-cost-'):
                    item_id = int(key.split('-')[-1])
                    item = MenuItem.objects.get(id=item_id, category__menu=menu)
                    item.cost = float(value)
                    item.save()
            except Exception as e:
                error_messages.append(f"Error processing {key}: {e}")

        if error_messages:
            for error in error_messages:
                messages.error(request, error)
        else:
            messages.success(request, "Menu order updated successfully!")

        return redirect('order_menu', menu_slug=menu.slug)

    category_form = MenuCategoryForm()

    context = {
        'menu': menu,
        'categories': categories,
        'category_form': category_form,
    }
    return render(request, 'menu/order_menu.html', context)