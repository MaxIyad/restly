# menu/views.py:
from django.shortcuts import render, get_object_or_404, redirect
from django.http import JsonResponse
from .models import Menu, MenuItem, RecipeIngredient, MenuItemSecondaryAssociation, MenuItemVariation
from inventory.models import Ingredient
from .forms import MenuForm, MenuCategoryForm, MenuCategory, RecipeIngredientForm, MenuItemForm, MenuItemAssociationForm, MenuItemVariationForm
from django.contrib import messages
from decimal import Decimal, ROUND_HALF_UP
from django.db.models import Prefetch
from collections import defaultdict
from settings.models import Settings
from django.db import models
from reports.models import Order
from django.db import transaction

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
            if not menu.is_secondary:  # Only toggle activation for non-secondary menus
                menu.is_active = not menu.is_active
                menu.save()
                messages.success(request, f"Menu '{menu.name}' is now {'active' if menu.is_active else 'inactive'}!")
            else:
                messages.warning(request, "Secondary menus are always active and cannot be toggled.")
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

    primary_items = {cat.id: cat.items.filter(is_secondary=False) for cat in categories}
    secondary_items = {cat.id: cat.items.filter(is_secondary=True) for cat in categories}

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
        
        elif request.POST.get("action") == "simulate_order":
            menu_item_slug = request.POST.get("menu_item_slug")
            category_slug = request.POST.get("category_slug")
            return simulate_order(request, menu_slug, category_slug, menu_item_slug)
        
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


    for category in categories:
        category.primary_items = category.items.filter(is_secondary=False)
        category.secondary_items = category.items.filter(is_secondary=True)           

    context = {
        'menu': menu,
        'categories': categories,
        'category_form': category_form,
        'menu_item_form': item_form,
        'primary_items': primary_items,
        'secondary_items': secondary_items,
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
    recipe_ingredients = menu_item.menu_item_recipe_ingredients.select_related('ingredient', 'category')
    settings_instance = Settings.objects.first()
    secondary_menus = Menu.objects.filter(is_secondary=True)
    associated_form = MenuItemAssociationForm(instance=menu_item)
    secondary_associations = MenuItemSecondaryAssociation.objects.filter(menu_item=menu_item)
    variations = menu_item.variations.all()
    variation_form = MenuItemVariationForm()



    selected_secondary_menu_id = menu_item.associated_secondary_menu_id
    unassociated_secondary_items = MenuItem.objects.filter(
        is_secondary=True,
        category__menu_id=selected_secondary_menu_id
    ).exclude(
        id__in=menu_item.associated_secondary_items.values_list('id', flat=True)
    )

    # Gathers all secondary categories and their items, marking secondary menu item active states
    secondary_categories = []
    for secondary_menu in secondary_menus:
        categories = secondary_menu.categories.prefetch_related('items')
        for cat in categories:
            for item in cat.items.all():
                item.is_secondary_active = menu_item.associated_secondary_menu == secondary_menu and item.is_active
            secondary_categories.append(cat)






    secondary_items_by_category = defaultdict(list)
    for association in secondary_associations.select_related('secondary_item__category'):
        category_name = association.secondary_item.category.name
        secondary_items_by_category[category_name].append(association)


    # Update the calculated price for each ingredient
    for recipe_ingredient in recipe_ingredients:
        if recipe_ingredient.unit and recipe_ingredient.unit.multiplier:
            # Delivery Unit Cost = unit_cost / delivery_unit_amount
            delivery_unit_cost = Decimal(recipe_ingredient.ingredient.unit_cost) / Decimal(
                recipe_ingredient.ingredient.unit_multiplier
            )
            # Adjust cost for the recipe unit multiplier
            unit_cost = delivery_unit_cost * Decimal(recipe_ingredient.unit.multiplier)
            # Calculate the total ingredient cost
            calculated_price = Decimal(recipe_ingredient.quantity) * unit_cost
        else:
            calculated_price = Decimal(0)

        # Use `calculated_price` as needed instead of assigning it
        recipe_ingredient.calculated_price_value = calculated_price
                

    menu_item_cost = Decimal(menu_item.cost or 0)
    total_ingredient_cost = sum(
        Decimal(recipe_ingredient.quantity) * (
            (Decimal(recipe_ingredient.ingredient.unit_cost) / Decimal(recipe_ingredient.ingredient.unit_multiplier))
            * Decimal(recipe_ingredient.unit.multiplier)
        ) if recipe_ingredient.unit and recipe_ingredient.unit.multiplier else Decimal(0)
        for recipe_ingredient in recipe_ingredients
    )

    menu_item_cost = Decimal(menu_item.cost or 0)
    margin = Decimal(0)
    if total_ingredient_cost > 0:
        margin = Decimal((menu_item_cost - total_ingredient_cost) / total_ingredient_cost * 100).quantize(
            Decimal("0.001"), rounding=ROUND_HALF_UP
        )

    # Filter ingredients by category
    selected_category_id = request.GET.get('category_id')
    inventory_categories = Category.objects.all()
    ingredients = Ingredient.objects.filter(category_id=selected_category_id) if selected_category_id else []
    # CAlcautes total cost (secondary menu item + Menu item sell price)


    if request.method == "POST":
        action = request.POST.get("action")
        if action == "add_ingredient":
            ingredient_id = request.POST.get("ingredient_id")
            ingredient = get_object_or_404(Ingredient, id=ingredient_id)
            
            # Check if the ingredient has associated units
            default_unit = ingredient.units.first()
            if not default_unit:
                messages.error(request, f"Cannot add ingredient '{ingredient.name}': No unit associated with this ingredient.")
                return redirect(request.path + f"?category_id={selected_category_id}")

            # Create a new RecipeIngredient with the default unit
            RecipeIngredient.objects.create(
                menu_item=menu_item,
                ingredient=ingredient,
                category=ingredient.category,
                unit=default_unit,
                quantity=1.0  # Default quantity
            )
            messages.success(request, f"Ingredient '{ingredient.name}' added with default unit '{default_unit.name}'.")
            return redirect(request.path + f"?category_id={selected_category_id}")
        
        elif action == "update_associations":
            associated_form = MenuItemAssociationForm(request.POST, instance=menu_item)
            if associated_form.is_valid():
                associated_form.save()
                messages.success(request, f"Associations for '{menu_item.name}' updated successfully.")
                return redirect('menu_item_detail', menu_slug=menu.slug, category_slug=category.slug, menu_item_slug=menu_item.slug)
       
        elif action == "remove_ingredient":
            recipe_ingredient_id = request.POST.get("ingredient_id")
            recipe_ingredient = get_object_or_404(RecipeIngredient, id=recipe_ingredient_id)
            recipe_ingredient.delete()
            messages.success(request, f"Ingredient '{recipe_ingredient.ingredient.name}' removed.")
            return redirect(request.path)

        elif action == "save_quantities":
            errors = []
            for recipe_ingredient in recipe_ingredients:
                quantity_key = f"quantity-{recipe_ingredient.id}"
                unit_key = f"unit-{recipe_ingredient.id}"
                new_quantity = request.POST.get(quantity_key)
                selected_unit_id = request.POST.get(unit_key)
                try:
                    if new_quantity:
                        recipe_ingredient.quantity = Decimal(new_quantity)
                    if selected_unit_id:
                        recipe_ingredient.unit = recipe_ingredient.ingredient.units.get(id=selected_unit_id)
                    recipe_ingredient.save()
                except Exception as e:
                    errors.append(f"Error updating {recipe_ingredient.ingredient.name}: {e}")
            if errors:
                messages.error(request, "Errors updating ingredients: " + ", ".join(errors))
            else:
                messages.success(request, "Ingredient quantities and units updated.")
            return redirect(request.path)

            
        
        

        elif action == "add_association":
            item_ids = request.POST.getlist("associated_secondary_items")
            items_to_add = MenuItem.objects.filter(id__in=item_ids, is_secondary=True)
            menu_item.associated_secondary_items.add(*items_to_add)
            messages.success(request, "New associations added successfully.")
            return redirect('menu_item_detail', menu_slug=menu.slug, category_slug=category.slug, menu_item_slug=menu_item.slug)

        
        elif action == "toggle_secondary_item":
            secondary_item_id = request.POST.get("secondary_item_id")
            association = get_object_or_404(MenuItemSecondaryAssociation, menu_item=menu_item, secondary_item_id=secondary_item_id)
            association.is_active = not association.is_active
            association.save()
            messages.success(request, f"Secondary item '{association.secondary_item.name}' status updated.")
            return redirect(request.path)

        elif action == "bulk_update":
            for association in secondary_associations:
                checkbox_name = f"association_status_{association.secondary_item.id}"
                association.is_active = checkbox_name in request.POST
                association.save()

            messages.success(request, "Secondary item statuses updated successfully.")
            return redirect(request.path)
        
        elif action == "update_secondary_menu":
            secondary_menu_id = request.POST.get("associated_secondary_menu")
            if secondary_menu_id:
                secondary_menu = get_object_or_404(Menu, id=secondary_menu_id, is_secondary=True)
                menu_item.associated_secondary_menu = secondary_menu

                # Update associations
                secondary_items = MenuItem.objects.filter(category__menu=secondary_menu, is_secondary=True)
                for item in secondary_items:
                    MenuItemSecondaryAssociation.objects.get_or_create(menu_item=menu_item, secondary_item=item)

            else:
                menu_item.associated_secondary_menu = None
                MenuItemSecondaryAssociation.objects.filter(menu_item=menu_item).delete()

            menu_item.save()
            messages.success(request, "Secondary menu and associated items updated.")
            return redirect(request.path)



        elif action == "update_cost":
            try:
                cost = Decimal(request.POST.get("cost")).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)
                if cost < 0:
                    messages.error(request, "Cost cannot be negative.")
                else:
                    menu_item.cost = cost
                    menu_item.save()
                    messages.success(request, f"Updated cost for {menu_item.name}.")
            except Exception as e:
                messages.error(request, f"Error updating cost: {e}")
            return redirect(request.path)
        
        elif request.POST.get("action") == "add_variation":
            variation_form = MenuItemVariationForm(request.POST)
            if variation_form.is_valid():
                variation = variation_form.save(commit=False)
                variation.menu_item = menu_item
                variation.save()
                messages.success(request, f"Variation '{variation.name}' added successfully.")
                return redirect(request.path)
            else:
                messages.error(request, "Failed to add variation. Please check the form.")
        elif request.POST.get("action") == "delete_variation":
            variation_id = request.POST.get("variation_id")
            variation = get_object_or_404(MenuItemVariation, id=variation_id, menu_item=menu_item)
            variation.delete()
            messages.success(request, f"Variation '{variation.name}' deleted successfully.")
            return redirect(request.path)
        


    context = {
        'menu': menu,
        'category': category,
        'menu_item': menu_item,
        'recipe_ingredients': recipe_ingredients,
        'total_ingredient_cost': total_ingredient_cost,
        'inventory_categories': inventory_categories,
        'settings': settings_instance,
        'secondary_menus': Menu.objects.filter(is_secondary=True),
        'ingredients': ingredients,
        'secondary_categories': secondary_categories,
        'selected_category_id': int(selected_category_id) if selected_category_id else None,
        'associated_form': associated_form,
        'unassociated_secondary_items': unassociated_secondary_items,
        'secondary_associations': secondary_associations,
        'secondary_items_by_category': dict(secondary_items_by_category),
        'margin': margin,
        'variations': variations,
        'variation_form': variation_form,
        
        
    }
    return render(request, 'menu/menu_item_detail.html', context)




def variation_detail(request, menu_slug, category_slug, menu_item_slug, variation_slug):
    menu = get_object_or_404(Menu, slug=menu_slug)
    category = get_object_or_404(MenuCategory, slug=category_slug, menu=menu)
    menu_item = get_object_or_404(MenuItem, slug=menu_item_slug, category=category)
    variation = get_object_or_404(MenuItemVariation, slug=variation_slug, menu_item=menu_item)
    settings_instance = Settings.objects.first()


    variation_ingredients = variation.variation_recipe_ingredients.select_related('ingredient', 'category', 'unit')
    menu_item_ingredients = menu_item.menu_item_recipe_ingredients.select_related('ingredient', 'category', 'unit')

    # Compute price difference
    price_difference = variation.price - menu_item.cost

    # Compute ingredient differences
    variation_ingredient_map = {
        (ri.ingredient.id, ri.unit.id): ri for ri in variation_ingredients
    }
    menu_item_ingredient_map = {
        (ri.ingredient.id, ri.unit.id): ri for ri in menu_item_ingredients
    }

    differences = []
    for key, menu_item_ri in menu_item_ingredient_map.items():
        variation_ri = variation_ingredient_map.get(key)
        unit_name = menu_item_ri.unit.name if menu_item_ri.unit else "unit"
        if variation_ri:
            if variation_ri.quantity != menu_item_ri.quantity:
                quantity_difference = variation_ri.quantity - menu_item_ri.quantity
                differences.append({
                    'ingredient': f"{menu_item_ri.ingredient.name} ({unit_name})",
                    'menu_item_quantity': f"{menu_item_ri.quantity} {unit_name}(s)",
                    'variation_quantity': f"{variation_ri.quantity} {unit_name}(s)",
                    'quantity_difference': f"{quantity_difference} {unit_name}(s)",
                })
        else:
            differences.append({
                'ingredient': f"{menu_item_ri.ingredient.name} ({unit_name})",
                'menu_item_quantity': f"{menu_item_ri.quantity} {unit_name}(s)",
                'variation_quantity': f"0 {unit_name}s",
                'quantity_difference': f"{-menu_item_ri.quantity} {unit_name}(s)",
            })

    for key, variation_ri in variation_ingredient_map.items():
        if key not in menu_item_ingredient_map:
            unit_name = variation_ri.unit.name if variation_ri.unit else "unit"
            differences.append({
                'ingredient': f"{variation_ri.ingredient.name} ({unit_name})",
                'menu_item_quantity': f"0 {unit_name}s",
                'variation_quantity': f"{variation_ri.quantity} {unit_name}(s)",
                'quantity_difference': f"{variation_ri.quantity} {unit_name}(s)",
            })


    # Fetch recipe ingredients for the variation
    recipe_ingredients = variation.variation_recipe_ingredients.select_related('ingredient', 'category', 'unit')

    # Compute total ingredient cost using the property
    total_ingredient_cost = sum(ri.calculated_price for ri in recipe_ingredients)



    # Calculate margin
    variation_cost = Decimal(variation.price or 0)
    margin = Decimal(0)
    if total_ingredient_cost > 0:
        margin = Decimal((variation_cost - total_ingredient_cost) / total_ingredient_cost * 100).quantize(
            Decimal("0.001"), rounding=ROUND_HALF_UP
        )

    # Handle category and ingredient filtering
    selected_category_id = request.GET.get('category_id')
    inventory_categories = Category.objects.all()  # Fetch all inventory categories
    ingredients = []
    if selected_category_id:
        try:
            selected_category_id = int(selected_category_id)
            ingredients = Ingredient.objects.filter(category_id=selected_category_id)
        except ValueError:
            selected_category_id = None

    if request.method == "POST":
        action = request.POST.get("action")
        if action == "add_ingredient":
            ingredient_id = request.POST.get("ingredient_id")
            ingredient = get_object_or_404(Ingredient, id=ingredient_id)
            default_unit = ingredient.units.first()
            if not default_unit:
                messages.error(request, f"No unit associated with ingredient '{ingredient.name}'.")
                return redirect(request.path + f"?category_id={selected_category_id}")

            RecipeIngredient.objects.create(
                variation=variation,
                ingredient=ingredient,
                category=ingredient.category,
                unit=default_unit,
                quantity=1.0
            )
            messages.success(request, f"Ingredient '{ingredient.name}' added to variation '{variation.name}'.")
            return redirect(request.path + f"?category_id={selected_category_id}")

        elif action == "remove_ingredient":
            recipe_ingredient_id = request.POST.get("ingredient_id")
            recipe_ingredient = get_object_or_404(RecipeIngredient, id=recipe_ingredient_id, variation=variation)
            recipe_ingredient.delete()
            messages.success(request, f"Ingredient '{recipe_ingredient.ingredient.name}' removed.")
            return redirect(request.path)

        elif action == "save_quantities":
            errors = []
            for recipe_ingredient in recipe_ingredients:
                quantity_key = f"quantity-{recipe_ingredient.id}"
                unit_key = f"unit-{recipe_ingredient.id}"
                new_quantity = request.POST.get(quantity_key)
                selected_unit_id = request.POST.get(unit_key)
                try:
                    if new_quantity:
                        recipe_ingredient.quantity = Decimal(new_quantity)
                    if selected_unit_id:
                        recipe_ingredient.unit = recipe_ingredient.ingredient.units.get(id=selected_unit_id)
                    recipe_ingredient.save()
                except Exception as e:
                    errors.append(f"Error updating {recipe_ingredient.ingredient.name}: {e}")
            if errors:
                messages.error(request, "Errors updating ingredients: " + ", ".join(errors))
            else:
                messages.success(request, "Ingredient quantities and units updated.")
            return redirect(request.path)

        elif action == "update_variation":
            new_price = request.POST.get("price")
            if new_price:
                variation.price = Decimal(new_price).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)
                variation.save()
                messages.success(request, f"Variation '{variation.name}' price updated successfully.")
            return redirect(request.path)

    context = {
        'menu': menu,
        'category': category,
        'menu_item': menu_item,
        'variation': variation,
        'recipe_ingredients': recipe_ingredients,
        'total_ingredient_cost': total_ingredient_cost,
        'margin': margin,
        'inventory_categories': inventory_categories,
        'ingredients': ingredients,
        'settings': settings_instance,
        'ingredient_differences': differences,
        'price_difference': price_difference,
        'selected_category_id': int(selected_category_id) if selected_category_id else None,
    }
    return render(request, 'menu/variation_detail.html', context)






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

    # Handle variation if provided
    variation_slug = request.POST.get("variation_slug")
    if variation_slug:
        variation = get_object_or_404(MenuItemVariation, slug=variation_slug, menu_item=menu_item)
        recipe_ingredients = variation.variation_recipe_ingredients.all()
        price = variation.price
    else:
        # Default to menu item ingredients and price
        recipe_ingredients = menu_item.menu_item_recipe_ingredients.all()
        price = menu_item.cost

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






def duplicate_menu(request, menu_id):
    """
    Duplicate a menu along with its categories and menu items. Keeps secondary menus secondary. 
    """
    original_menu = get_object_or_404(Menu, id=menu_id)

    with transaction.atomic():
        # Duplicate the menu
        duplicated_menu = Menu.objects.create(
            name=f"{original_menu.name} (Copy)",
            is_active=False,  # Default to inactive for the duplicate
            is_secondary=original_menu.is_secondary
        )

        # Duplicate categories and their menu items
        for category in original_menu.categories.all():
            duplicated_category = MenuCategory.objects.create(
                name=category.name,
                menu=duplicated_menu,
                order=category.order,
                is_active=category.is_active,
            )

            for item in category.items.all():
                MenuItem.objects.create(
                    name=item.name,
                    category=duplicated_category,
                    description=item.description,
                    cost=item.cost,
                    order=item.order,
                    is_active=item.is_active,
                    is_secondary=item.is_secondary,
                )

    messages.success(request, f"Menu '{original_menu.name}' duplicated successfully!")
    return redirect('menu_list')




def order_menu(request, menu_slug):
    menu = get_object_or_404(Menu, slug=menu_slug)
    categories = menu.categories.prefetch_related(
        models.Prefetch('items', queryset=MenuItem.objects.order_by('order'))
    )
    error_messages = []  # Collect error messages for invalid updates

    if request.method == 'POST':

        menu_name = request.POST.get('menu-name')
        if menu_name and menu_name.strip() != menu.name:
            try:
                menu.name = menu_name.strip()
                menu.slug = None  # Reset slug so it gets regenerated in the save method
                menu.full_clean()  # Validate the new name
                menu.save()
                messages.success(request, "Menu name updated successfully!")
            except Exception as e:
                error_messages.append(f"Error updating menu name: {e}")

        # Handle secondary toggle
        is_secondary = request.POST.get('is_secondary') == 'on'
        if menu.is_secondary != is_secondary:
            menu.is_secondary = is_secondary
            menu.is_active = True if is_secondary else menu.is_active  # Ensure secondary menus are always active
            menu.save()
            messages.success(
                request, 
                f"Menu '{menu.name}' is now {'Secondary' if is_secondary else 'Primary'}."
            )

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