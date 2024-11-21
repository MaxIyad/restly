# menu/views.py:
from django.shortcuts import render, get_object_or_404, redirect
from django.http import JsonResponse
from .models import Menu, MenuItem, RecipeIngredient
from inventory.models import Ingredient
from .forms import MenuForm, MenuCategoryForm, MenuCategory, RecipeIngredientForm, MenuItemForm
from django.contrib import messages


from django.http import JsonResponse
from inventory.models import Category





def menu_list(request):
    menus = Menu.objects.all()

    if request.method == "POST":
        # Check for activation changes
        menu_id = request.POST.get('menu_id')
        if menu_id:
            menu = Menu.objects.get(id=menu_id)
            menu.is_active = not menu.is_active  # Toggle active state
            menu.save()
            messages.success(request, f"Menu '{menu.name}' is now active!")
            return redirect('menu_list')

        # Handle new menu creation
        form = MenuForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, "Menu added successfully!")
            return redirect('menu_list')
    else:
        form = MenuForm()

    return render(request, 'menu/menu_list.html', {'menus': menus, 'form': form})


def menu_detail(request, menu_name):
    menu = get_object_or_404(Menu, name=menu_name)
    categories = menu.categories.prefetch_related("items")

    if request.method == "POST":
        if "add_category" in request.POST:
            # Add a new category
            category_form = MenuCategoryForm(request.POST)
            if category_form.is_valid():
                category = category_form.save(commit=False)
                category.menu = menu
                category.save()
                messages.success(request, f"Category '{category.name}' added to menu '{menu.name}'.")
                return redirect('menu_detail', menu_name=menu_name)

        elif "add_menu_item" in request.POST:
            # Add a new menu item to a category
            category_id = request.POST.get("category_id")
            category = get_object_or_404(MenuCategory, id=category_id, menu=menu)
            item_form = MenuItemForm(request.POST)
            if item_form.is_valid():
                menu_item = item_form.save(commit=False)
                menu_item.category = category
                menu_item.save()
                messages.success(request, f"Menu item '{menu_item.name}' added to category '{category.name}'.")
                return redirect('menu_detail', menu_name=menu_name)

    else:
        category_form = MenuCategoryForm()
        item_form = MenuItemForm()

    context = {
        'menu': menu,
        'categories': categories,
        'category_form': category_form,
        'item_form': item_form,
    }
    return render(request, 'menu/menu_detail.html', context)





def category_detail(request, menu_name, category_name):
    menu = get_object_or_404(Menu, name=menu_name)
    category = get_object_or_404(MenuCategory, name=category_name, menu=menu)
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
                return redirect('category_detail', menu_name=menu_name, category_name=category_name)

    else:
        menu_item_form = MenuItemForm()

    context = {
        'menu': menu,
        'category': category,
        'menu_items': menu_items,
        'menu_item_form': menu_item_form,
    }
    return render(request, 'menu/category_detail.html', context)


######################################################################################################








def menu_item_detail(request, menu_name, category_name, menu_item_name):
    menu = get_object_or_404(Menu, name=menu_name)
    category = get_object_or_404(MenuCategory, name=category_name, menu=menu)
    menu_item = get_object_or_404(MenuItem, name=menu_item_name, category=category)
    recipe_ingredients = menu_item.recipe_ingredients.all()

    if request.method == "POST":
        if "add_ingredient" in request.POST:
            # Get ingredient name and category ID from the form
            ingredient_name = request.POST.get("ingredient_name")
            category_id = request.POST.get("category")
            quantity = request.POST.get("quantity")

            # Validate the input
            if not ingredient_name:
                messages.error(request, "Please select an ingredient to add.")
                return redirect('menu_item_detail', menu_name=menu_name, category_name=category_name, menu_item_name=menu_item_name)
            
            if not category_id:
                messages.error(request, "Please select a category for the ingredient.")
                return redirect('menu_item_detail', menu_name=menu_name, category_name=category_name, menu_item_name=menu_item_name)

            if not quantity:
                messages.error(request, "Please specify the quantity.")
                return redirect('menu_item_detail', menu_name=menu_name, category_name=category_name, menu_item_name=menu_item_name)

            # Fetch the ingredient and category objects
            ingredient = Ingredient.objects.filter(name=ingredient_name).first()
            category = Category.objects.filter(id=category_id).first()

            if not ingredient:
                messages.error(request, "The selected ingredient does not exist.")
                return redirect('menu_item_detail', menu_name=menu_name, category_name=category_name, menu_item_name=menu_item_name)

            # Create and save the RecipeIngredient
            RecipeIngredient.objects.create(
                menu_item=menu_item,
                ingredient=ingredient,
                category=category,
                quantity=quantity
            )

            messages.success(
                request,
                f"Ingredient '{ingredient.name}' added to '{menu_item.name}' from category '{category.name if category else 'N/A'}'."
            )
            return redirect('menu_item_detail', menu_name=menu_name, category_name=category_name, menu_item_name=menu_item_name)

        elif "remove_ingredient" in request.POST:
            ingredient_id = request.POST.get("ingredient_id")
            recipe_ingredient = get_object_or_404(RecipeIngredient, id=ingredient_id, menu_item=menu_item)
            recipe_ingredient.delete()
            messages.success(request, f"Ingredient '{recipe_ingredient.ingredient.name}' removed from '{menu_item.name}'.")
            return redirect('menu_item_detail', menu_name=menu_name, category_name=category_name, menu_item_name=menu_item_name)

    recipe_ingredient_form = RecipeIngredientForm()

    context = {
        'menu': menu,
        'category': category,
        'menu_item': menu_item,
        'recipe_ingredients': recipe_ingredients,
        'recipe_ingredient_form': recipe_ingredient_form,
    }
    return render(request, 'menu/menu_item_detail.html', context)







def get_categories_for_ingredient(request):
    ingredient_name = request.GET.get('ingredient_name')
    if not ingredient_name:
        return JsonResponse({'error': 'No ingredient name provided'}, status=400)

    try:
        # Fetch all ingredients with the same name
        ingredients = Ingredient.objects.filter(name__iexact=ingredient_name)
        categories = Category.objects.filter(ingredient__in=ingredients).distinct()
        categories_data = [{'id': category.id, 'name': category.name} for category in categories]
        return JsonResponse({'categories': categories_data})
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)










def simulate_order(request, menu_name, category_name, menu_item_name):
    menu = get_object_or_404(Menu, name=menu_name)
    category = get_object_or_404(MenuCategory, name=category_name, menu=menu)
    menu_item = get_object_or_404(MenuItem, name=menu_item_name, category=category)
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

    return redirect('menu_detail', menu_name=menu_name)
