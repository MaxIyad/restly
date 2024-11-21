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

    ingredient = None

    if request.method == "POST":
        if "add_ingredient" in request.POST:
            ingredient_name = request.POST.get("ingredient_name")
            ingredient = Ingredient.objects.filter(name=ingredient_name).first()

            recipe_ingredient_form = RecipeIngredientForm(request.POST)

            if recipe_ingredient_form.is_valid():
                # Create the RecipeIngredient object
                recipe_ingredient = recipe_ingredient_form.save(commit=False)

                if ingredient:
                    recipe_ingredient.ingredient = ingredient
                    recipe_ingredient.menu_item = menu_item  # Associate the menu item
                    recipe_ingredient.save()  # Save to the database
                    messages.success(
                        request,
                        f"Ingredient '{recipe_ingredient.ingredient.name}' added to '{menu_item.name}' "
                        f"from category '{recipe_ingredient.category.name}'."
                    )
                    return redirect('menu_item_detail', menu_name=menu_name, category_name=category_name, menu_item_name=menu_item_name)
                else:
                    messages.error(request, "Selected ingredient does not exist.")
        elif "remove_ingredient" in request.POST:
            ingredient_id = request.POST.get("ingredient_id")
            recipe_ingredient = get_object_or_404(RecipeIngredient, id=ingredient_id, menu_item=menu_item)
            recipe_ingredient.delete()
            messages.success(request, f"Ingredient '{recipe_ingredient.ingredient.name}' removed from '{menu_item.name}'.")
            return redirect('menu_item_detail', menu_name=menu_name, category_name=category_name, menu_item_name=menu_item_name)
    else:
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
    errors = []

    # Deduct ingredient quantities only from the specified category
    for recipe_ingredient in recipe_ingredients:
        ingredient = recipe_ingredient.ingredient
        category_to_deplete = recipe_ingredient.category

        if category_to_deplete is None:
            errors.append(f"Category for {ingredient.name} is not specified!")
            continue

        # Filter ingredient in the specified category
        ingredient_in_category = Ingredient.objects.filter(
            id=ingredient.id, category=category_to_deplete
        ).first()

        if not ingredient_in_category:
            errors.append(f"{ingredient.name} does not exist in the {category_to_deplete.name} category!")
            continue

        if ingredient_in_category.quantity >= recipe_ingredient.quantity:
            ingredient_in_category.quantity -= recipe_ingredient.quantity
            ingredient_in_category.save()
        else:
            errors.append(
                f"Not enough {ingredient.name} in category {category_to_deplete.name} to fulfill the order!"
            )

    if errors:
        messages.error(request, " ".join(errors))
    else:
        messages.success(request, f"Order for '{menu_item.name}' simulated successfully!")

    return redirect('menu_detail', menu_name=menu_name)