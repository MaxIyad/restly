import csv
from django.db.models import Sum, F, FloatField, ExpressionWrapper
from menu.models import MenuItem, RecipeIngredient
from decimal import Decimal, InvalidOperation
from collections import defaultdict
from django.shortcuts import render
from django.http import HttpResponse
from django.db.models import Sum, F, FloatField, ExpressionWrapper
from django.db import transaction
from menu.models import MenuItem, RecipeIngredient
from inventory.models import Ingredient, Category
from settings.models import Settings









def estimate_view(request):
    # Fetch active menu items
    active_menu_items = MenuItem.objects.filter(
        category__menu__is_active=True, is_active=True
    ).select_related('category', 'category__menu')
    settings_instance = Settings.objects.first()

    context = {
        "ingredients_by_category": {},
        "menu_items_data": [],
        "revenue_goal": None,
        "profit_goal": None,
        "total_cost": None,
        "profitability": None,
        "profitability_percentage": None,
        "success": None,
        "error": None,
        "goal_explanation": "",
        "settings": settings_instance,
    }

    recipe_data = (
        RecipeIngredient.objects.filter(menu_item__in=active_menu_items)
        .values("ingredient_id", "ingredient__name", "ingredient__unit_type")
        .annotate(
            total_quantity=Sum(F("quantity")),
            avg_revenue_per_unit=ExpressionWrapper(
                Sum(F("menu_item__cost") * F("quantity")) / Sum(F("quantity")),
                output_field=FloatField(),
            )
        )
    )

    categories = Category.objects.prefetch_related('ingredient_set')
    grouped_ingredients = {category.name: [] for category in categories}

    if request.method == "POST":
        mode = request.POST.get("mode", "").strip()

        if mode == "revenue_to_ingredients":
            try:
                # Parse input
                revenue_goal_input = request.POST.get("revenue_goal", "").strip()
                profit_goal_input = request.POST.get("profit_goal", "").strip()

                revenue_goal = Decimal(revenue_goal_input) if revenue_goal_input else None
                profit_goal = Decimal(profit_goal_input) if profit_goal_input else None

                if revenue_goal is None and profit_goal is None:
                    raise InvalidOperation("Both revenue and profit goals are missing.")

                total_cost = Decimal(0)
                max_iterations = 10
                iteration = 0

                while iteration < max_iterations:
                    iteration += 1



                    if profit_goal is not None:
                        revenue_goal = profit_goal + total_cost

                    new_total_cost = Decimal(0)

                    for category in categories:
                        grouped_ingredients[category.name] = []

                        for ingredient in category.ingredient_set.all():
                            matching_data = next(
                                (data for data in recipe_data if data["ingredient_id"] == ingredient.id), None
                            )

                            if matching_data:
                                avg_revenue_per_unit = Decimal(
                                    matching_data["avg_revenue_per_unit"] or 0
                                )
                                unit_cost = Decimal(ingredient.unit_cost or 0)
                                current_quantity = Decimal(ingredient.quantity or 0)

                                quantity_needed = (
                                    revenue_goal / avg_revenue_per_unit
                                    if avg_revenue_per_unit > 0 and revenue_goal
                                    else Decimal(0)
                                )
                                sufficient = current_quantity >= quantity_needed
                                total_cost_for_ingredient = quantity_needed * unit_cost

                                grouped_ingredients[category.name].append({
                                    "name": ingredient.name,
                                    "unit_type": ingredient.unit_type,
                                    "quantity_needed": quantity_needed,
                                    "current_quantity": current_quantity,
                                    "unit_cost": unit_cost,
                                    "total_cost": total_cost_for_ingredient,
                                    "sufficient": sufficient,
                                })

                                new_total_cost += total_cost_for_ingredient

                    if abs(new_total_cost - total_cost) < Decimal("0.01"):
                        break
                    total_cost = new_total_cost

                # Goal explanation
                currency_symbol = settings_instance.get_currency_type_display()
                profit = revenue_goal - total_cost

                if profit_goal is not None:
                    context["goal_explanation"] = (
                        f"To achieve <span class='highlight-montery-goal-text'>{currency_symbol}{profit_goal:.2f}</span> in profit, "
                        f"you’ll spend {currency_symbol}{total_cost:.2f} on costs, "
                        f"resulting in {currency_symbol}{revenue_goal:.2f} as revenue."
                    )
                else:
                    context["goal_explanation"] = (
                        f"To generate {currency_symbol}{revenue_goal:.2f} in revenue, "
                        f"you’ll spend {currency_symbol}{total_cost:.2f} on costs, "
                        f"leaving {currency_symbol}{profit:.2f} in profit."
                    )

                # Calculate menu item data
                menu_items_data = []
                for item in active_menu_items:
                    # Total ingredient cost for the menu item
                    total_ingredient_cost = sum(
                        Decimal(ri.quantity) * Decimal(ri.ingredient.unit_cost or 0)
                        for ri in item.recipe_ingredients.select_related("ingredient")
                    )
                    price = item.cost or Decimal("0")
                    margin_currency = price - total_ingredient_cost
                    margin_percentage = (margin_currency / total_ingredient_cost * 100) if total_ingredient_cost > 0 else 0

                    # If margin is zero or negative, skip calculation (otherwise, 404)
                    if margin_currency <= 0:
                        continue

                    units_needed = (profit_goal / margin_currency) if profit_goal else (revenue_goal / price)

                    revenue_acquired = price * round(units_needed, 2)
                    profit_acquired = margin_currency * round(units_needed,2)

                    menu_items_data.append({
                        "name": item.name,
                        "cost": total_ingredient_cost,
                        "margin": f"{margin_currency:.2f} ({margin_percentage:.2f}%)",
                        "price": price,
                        "units_needed": units_needed,
                        "revenue_acquired": revenue_acquired,
                        "profit_acquired": profit_acquired,
                    })


                # Update context
                context.update({
                    "revenue_goal": revenue_goal,
                    "profit_goal": profit_goal,
                    "total_cost": total_cost,
                    "profitability": profit,
                    "profitability_percentage": (
                        (profit / revenue_goal * 100) if revenue_goal and revenue_goal > 0 else Decimal(0)
                    ),
                    "ingredients_by_category": grouped_ingredients,
                    "menu_items_data": menu_items_data,
                })

            except (InvalidOperation, Exception) as e:
                context["error"] = f"Error in calculation: {e}"

    return render(request, "reports/estimate.html", context)












###########################################################################################################################################################
###########################################################################################################################################################
###########################################################################################################################################################


def sales_view(request):
    # Aggregate sales data from active menus
    active_menus = Menu.objects.filter(is_active=True)

    # Menu-level sales data
    menu_sales = []
    for menu in active_menus:
        menu_items = MenuItem.objects.filter(category__menu=menu)
        total_revenue = menu_items.aggregate(total_revenue=Sum(F('cost')))['total_revenue'] or Decimal("0")
        menu_sales.append({
            "menu": menu.name,
            "total_revenue": total_revenue,
            "items_sold": menu_items.count()
        })

    # Category-level sales data
    category_sales = []
    for category in MenuCategory.objects.filter(menu__in=active_menus):
        items = MenuItem.objects.filter(category=category)
        total_revenue = items.aggregate(total_revenue=Sum(F('cost')))['total_revenue'] or Decimal("0")
        category_sales.append({
            "category": category.name,
            "menu": category.menu.name,
            "total_revenue": total_revenue,
            "items_sold": items.count()
        })

    # Item-level sales data
    item_sales = []
    for item in MenuItem.objects.filter(category__menu__in=active_menus):
        item_revenue = item.cost or Decimal("0")
        item_sales.append({
            "item": item.name,
            "category": item.category.name,
            "menu": item.category.menu.name,
            "revenue": item_revenue
        })

    # Ingredient-level sales data
    ingredient_sales = {}
    for recipe in RecipeIngredient.objects.filter(menu_item__category__menu__in=active_menus).select_related('ingredient'):
        ingredient = recipe.ingredient
        if ingredient.id not in ingredient_sales:
            ingredient_sales[ingredient.id] = {
                "name": ingredient.name,
                "categories": set(),
                "revenue": Decimal("0")
            }
        ingredient_sales[ingredient.id]["categories"].add(recipe.category.name if recipe.category else "Uncategorized")
        if recipe.menu_item.cost:
            ingredient_sales[ingredient.id]["revenue"] += Decimal(recipe.menu_item.cost) * Decimal(recipe.quantity)

    # Convert ingredient categories to comma-separated strings
    for ingredient_data in ingredient_sales.values():
        ingredient_data["categories"] = ", ".join(ingredient_data["categories"])

    context = {
        "menu_sales": menu_sales,
        "category_sales": category_sales,
        "item_sales": item_sales,
        "ingredient_sales": ingredient_sales.values(),
    }

    return render(request, "reports/sales.html", context)