# menu/views.py:
from django.shortcuts import render, get_object_or_404, redirect
from django.http import JsonResponse
from .models import Menu, MenuItem, RecipeIngredient
from inventory.models import Ingredient
from .forms import MenuForm, MenuCategoryForm, MenuCategory, RecipeIngredientForm, MenuItemForm
from django.contrib import messages
from decimal import Decimal
from django.db.models import Prefetch
from settings.models import Settings
from django.db import models
from reports.models import Order

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
    settings_instance = Settings.objects.first()

    category_form = MenuCategoryForm()
    item_form = MenuItemForm()

    if request.method == "POST":

        if "toggle_item_id" in request.POST:
            item_id = int(request.POST["toggle_item_id"])
            item = get_object_or_404(MenuItem, id=item_id, category__menu=menu)
            item.is_active = not item.is_active
            item.save()
            messages.success(request, f"Menu item '{item.name}' activation toggled.")
            return redirect("menu_detail", menu_slug=menu.slug)

        elif "toggle_category_id" in request.POST:
            category_id = int(request.POST["toggle_category_id"])
            category = get_object_or_404(MenuCategory, id=category_id, menu=menu)
            category.is_active = not category.is_active
            category.save()
            messages.success(request, f"Category '{category.name}' activation toggled.")
            return redirect("menu_detail", menu_slug=menu.slug)
        
        elif "delete_category_id" in request.POST:
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
        'settings': settings_instance,
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
    settings_instance = Settings.objects.first()

    total_ingredient_cost = sum(
        Decimal(ri.quantity) * Decimal(ri.ingredient.unit_cost) for ri in recipe_ingredients
    )

    # Update the calculated price for each ingredient
    for recipe_ingredient in recipe_ingredients:
        recipe_ingredient.calculated_price = (
            Decimal(recipe_ingredient.quantity) * Decimal(recipe_ingredient.ingredient.unit_cost)
        )

    # Filter ingredients by category
    selected_category_id = request.GET.get('category_id')
    inventory_categories = Category.objects.all()
    ingredients = Ingredient.objects.filter(category_id=selected_category_id) if selected_category_id else []

    if request.method == "POST":
        action = request.POST.get("action")
        if action == "add_ingredient":
            ingredient_id = request.POST.get("ingredient_id")
            ingredient = get_object_or_404(Ingredient, id=ingredient_id)
            RecipeIngredient.objects.create(
                menu_item=menu_item,
                ingredient=ingredient,
                category=ingredient.category,
                quantity=1.0  # Default quantity
            )
            messages.success(request, f"Ingredient '{ingredient.name}' added.")
            return redirect(request.path + f"?category_id={selected_category_id}")
        
        elif action == "remove_ingredient":
            recipe_ingredient_id = request.POST.get("ingredient_id")
            recipe_ingredient = get_object_or_404(RecipeIngredient, id=recipe_ingredient_id)
            recipe_ingredient.delete()
            messages.success(request, f"Ingredient '{recipe_ingredient.ingredient.name}' removed.")
            return redirect(request.path)

        elif action == "save_quantities":
            # Save ingredient quantities
            for key, value in request.POST.items():
                if key.startswith("quantity-"):
                    recipe_ingredient_id = key.split("-")[1]
                    recipe_ingredient = get_object_or_404(RecipeIngredient, id=recipe_ingredient_id)
                    try:
                        recipe_ingredient.quantity = Decimal(value)
                        recipe_ingredient.save()
                    except Exception as e:
                        messages.error(request, f"Error updating quantity for {recipe_ingredient.ingredient.name}: {e}")
            messages.success(request, "Quantities updated successfully.")
            return redirect(request.path)

        elif action == "update_cost":
            # Update cost and margin
            cost = request.POST.get("cost")
            try:
                if cost is not None:
                    cost = Decimal(cost)
                    if cost < 0:
                        messages.error(request, "Cost cannot be negative.")
                    else:
                        menu_item.cost = cost
                        menu_item.save()
                        messages.success(request, f"Updated cost for {menu_item.name} successfully.")
            except Exception as e:
                messages.error(request, f"Error updating cost: {e}")
            return redirect(request.path)

    context = {
        'menu': menu,
        'category': category,
        'menu_item': menu_item,
        'recipe_ingredients': recipe_ingredients,
        'total_ingredient_cost': total_ingredient_cost,
        'inventory_categories': inventory_categories,
        'settings': settings_instance,
        'ingredients': ingredients,
        'selected_category_id': int(selected_category_id) if selected_category_id else None,
        
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

    if not category.is_active:
        messages.error(request, f"Cannot simulate order. The category '{category.name}' is inactive.")
        return redirect('menu_detail', menu_slug=menu_slug)
    
    if not menu_item.is_active:
        messages.error(request, f"Cannot simulate order. The menu item '{menu_item.name}' is inactive.")
        return redirect('menu_detail', menu_slug=menu_slug)

    recipe_ingredients = menu_item.recipe_ingredients.all()
    warnings = []

    # Calculate total cost
    total_cost = Decimal(0)
    for recipe_ingredient in recipe_ingredients:
        ingredient = recipe_ingredient.ingredient
        category_to_deplete = recipe_ingredient.category

        if category_to_deplete is None:
            warnings.append(f"Category for {ingredient.name} is not specified!")
            continue

        try:
            ingredient_in_category = Ingredient.objects.get(
                name=ingredient.name,
                category=category_to_deplete
            )
        except Ingredient.DoesNotExist:
            warnings.append(f"{ingredient.name} does not exist in the {category_to_deplete.name} category!")
            continue

        # Deduct quantity
        ingredient_in_category.quantity -= recipe_ingredient.quantity
        ingredient_in_category.save()

        # Calculate cost
        total_cost += Decimal(recipe_ingredient.quantity) * Decimal(ingredient_in_category.unit_cost)

        if ingredient_in_category.quantity < 0:
            warnings.append(
                f"{ingredient.name} in category {category_to_deplete.name} is now in deficit ({ingredient_in_category.quantity})."
            )

    # Calculate revenue and profit
    price = menu_item.cost or Decimal(0)
    total_revenue = price
    total_profit = total_revenue - total_cost

    # Record the order
    Order.objects.create(
        customer_name="Unknown",
        taken_by=request.user,  # Current logged-in user
        total_cost=total_cost,
        total_revenue=total_revenue,
        total_profit=total_profit,
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