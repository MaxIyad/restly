from django.shortcuts import render, redirect
from inventory.models import Ingredient
from menu.models import MenuItem, RecipeIngredient
from decimal import Decimal, InvalidOperation
from django.db import transaction


def estimate_view(request):
    context = {}

    # Fetch active menu items
    active_menu_items = MenuItem.objects.filter(category__menu__is_active=True).select_related(
        'category', 'category__menu'
    )

    # Prepare initial ingredient data
    ingredients = Ingredient.objects.all()
    required_ingredients = {}
    for recipe in RecipeIngredient.objects.filter(menu_item__in=active_menu_items).select_related('ingredient', 'category'):
        ingredient = recipe.ingredient
        if ingredient.id not in required_ingredients:
            required_ingredients[ingredient.id] = {
                "name": ingredient.name,
                "unit_type": ingredient.unit_type,
                "categories": set(),
                "total_quantity": Decimal("0"),
                "average_revenue_per_unit": Decimal("0"),
            }
        required_ingredients[ingredient.id]["total_quantity"] += Decimal(recipe.quantity)
        required_ingredients[ingredient.id]["categories"].add(recipe.category.name if recipe.category else "Uncategorized")

    # Calculate average revenue per unit for each ingredient
    for ingredient_data in required_ingredients.values():
        ingredient_revenue = Decimal("0")
        ingredient_quantity = Decimal("0")
        ingredient = Ingredient.objects.get(name=ingredient_data["name"])
        for recipe in RecipeIngredient.objects.filter(ingredient=ingredient, menu_item__in=active_menu_items):
            if recipe.menu_item.cost:
                ingredient_revenue += Decimal(recipe.menu_item.cost) * Decimal(recipe.quantity)
                ingredient_quantity += Decimal(recipe.quantity)
        if ingredient_quantity > 0:
            ingredient_data["average_revenue_per_unit"] = ingredient_revenue / ingredient_quantity
        ingredient_data["categories"] = ", ".join(ingredient_data["categories"])

    context["required_ingredients"] = required_ingredients.values()

    if request.method == "POST":
        mode = request.POST.get("mode")  # "revenue_to_ingredients" or "edit_inventory"

        if mode == "revenue_to_ingredients":
            try:
                revenue_goal = Decimal(request.POST.get("revenue_goal", "0"))
                ingredient_totals = {}
                for ingredient in Ingredient.objects.all():
                    ingredient_revenue = Decimal("0")
                    ingredient_quantity = Decimal("0")
                    for recipe in RecipeIngredient.objects.filter(ingredient=ingredient, menu_item__in=active_menu_items):
                        if recipe.menu_item.cost:
                            ingredient_revenue += Decimal(recipe.menu_item.cost) * Decimal(recipe.quantity)
                            ingredient_quantity += Decimal(recipe.quantity)
                    if ingredient_quantity > 0:
                        avg_revenue_per_unit = ingredient_revenue / ingredient_quantity
                        ingredient_totals[ingredient.name] = {
                            "quantity": revenue_goal / avg_revenue_per_unit,
                            "unit_type": ingredient.unit_type,
                        }
                context["ingredients_required"] = ingredient_totals
                context["revenue_goal"] = revenue_goal
            except (InvalidOperation, Exception) as e:
                context["error"] = f"Error in calculation: {e}"

        elif mode == "edit_inventory":
            # Update inventory based on user inputs
            try:
                with transaction.atomic():
                    for ingredient in ingredients:
                        new_quantity = request.POST.get(f"quantity_{ingredient.id}", None)
                        if new_quantity is not None:
                            ingredient.quantity = Decimal(new_quantity)
                            ingredient.save()
                    context["success"] = "Inventory updated successfully."
            except (InvalidOperation, Exception) as e:
                context["error"] = f"Error updating inventory: {e}"

        elif mode == "reset_inventory":
            # Reset inventory to original state (example placeholder functionality)
            for ingredient in ingredients:
                ingredient.refresh_from_db()
            context["success"] = "Inventory reset successfully."

    return render(request, "reports/estimate.html", context)
