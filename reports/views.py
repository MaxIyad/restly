import csv
from decimal import Decimal, InvalidOperation
from collections import defaultdict
from django.shortcuts import render
from django.http import HttpResponse
from django.db.models import Sum, F, FloatField, ExpressionWrapper
from django.db import transaction
from menu.models import MenuItem, RecipeIngredient
from inventory.models import Ingredient
import csv
from decimal import Decimal, InvalidOperation
from collections import defaultdict
from django.shortcuts import render
from django.http import HttpResponse
from django.db.models import Sum, F, FloatField, ExpressionWrapper
from django.db import transaction
from menu.models import MenuItem, RecipeIngredient
from inventory.models import Ingredient




def estimate_view(request):
    # Fetch active menu items
    active_menu_items = MenuItem.objects.filter(
        category__menu__is_active=True, is_active=True
    ).select_related('category', 'category__menu')

    # Initialize context
    context = {
        "required_ingredients": [],
        "ingredients_required": {},
        "revenue_goal": None,
        "profit_goal": None,
        "total_cost": None,
        "profitability": None,
        "profitability_percentage": None,
        "success": None,
        "error": None,
        "ingredient_distribution": [],
        "profitability_data": {},
    }

    # Query RecipeIngredients to calculate required quantities and average revenue
    recipe_data = (
        RecipeIngredient.objects.filter(menu_item__in=active_menu_items)
        .values("ingredient_id", "ingredient__name", "ingredient__unit_type")
        .annotate(
            total_quantity=Sum(F("quantity")),
            avg_revenue_per_unit=ExpressionWrapper(
                Sum(F("menu_item__cost") * F("quantity")) / Sum(F("quantity")),
                output_field=FloatField()
            )
        )
        .order_by("ingredient__name")
    )

    # Add recipe data to context
    ingredient_quantities = defaultdict(Decimal)
    for data in recipe_data:
        total_quantity = Decimal(data["total_quantity"] or 0)
        ingredient_quantities[data["ingredient__name"]] += total_quantity
        context["required_ingredients"].append({
            "id": data["ingredient_id"],
            "name": data["ingredient__name"],
            "unit_type": data["ingredient__unit_type"],
            "total_quantity": total_quantity,
            "average_revenue_per_unit": Decimal(data["avg_revenue_per_unit"] or 0),
        })

    # Add ingredient distribution to context for charts
    context["ingredient_distribution"] = [
        {"name": k, "quantity": float(v)} for k, v in ingredient_quantities.items()
    ]

    # Handle form submissions
    if request.method == "POST":
        mode = request.POST.get("mode")  # "revenue_to_ingredients", "edit_inventory", "export_csv"

        if mode == "revenue_to_ingredients":
            try:
                # Validate and sanitize inputs
                revenue_goal_input = request.POST.get("revenue_goal", "").strip()
                profit_goal_input = request.POST.get("profit_goal", "").strip()

                # Convert inputs to Decimal, defaulting to 0 if invalid
                revenue_goal = Decimal(revenue_goal_input) if revenue_goal_input else None
                profit_goal = Decimal(profit_goal_input) if profit_goal_input else None

                ingredient_totals = {}
                total_cost = Decimal(0)

                # Adjust revenue goal based on profit goal if provided
                for ingredient_data in context["required_ingredients"]:
                    avg_revenue_per_unit = ingredient_data["average_revenue_per_unit"]
                    unit_cost = Decimal(Ingredient.objects.get(pk=ingredient_data["id"]).unit_cost)

                    if avg_revenue_per_unit > 0:
                        quantity_needed = Decimal(0)

                        if profit_goal is not None:
                            # Recalculate revenue goal dynamically to include profit goal
                            revenue_goal = profit_goal + total_cost

                        if revenue_goal is not None:
                            quantity_needed = revenue_goal / avg_revenue_per_unit

                        ingredient_totals[ingredient_data["name"]] = {
                            "quantity": quantity_needed,
                            "unit_type": ingredient_data["unit_type"],
                            "unit_cost": unit_cost,
                            "total_cost": quantity_needed * unit_cost,
                        }
                        total_cost += quantity_needed * unit_cost

                context["ingredients_required"] = ingredient_totals
                context["revenue_goal"] = revenue_goal
                context["profit_goal"] = profit_goal
                context["total_cost"] = total_cost
                context["profitability"] = profit_goal if profit_goal else (revenue_goal - total_cost if revenue_goal else None)
                context["profitability_percentage"] = (
                    (context["profitability"] / revenue_goal * 100) if revenue_goal and revenue_goal > 0 else Decimal(0)
                )
                context["profitability_data"] = {
                    "revenue_goal": float(revenue_goal or 0),
                    "total_cost": float(total_cost),
                    "profitability": float(context["profitability"] or 0),
                }
            except (InvalidOperation, Exception) as e:
                context["error"] = f"Error in calculation: {e}"

        elif mode == "edit_inventory":
            try:
                with transaction.atomic():
                    for ingredient_data in context["required_ingredients"]:
                        ingredient = Ingredient.objects.get(pk=ingredient_data["id"])
                        new_quantity = request.POST.get(f"quantity_{ingredient.id}")
                        if new_quantity is not None:
                            ingredient.quantity = float(new_quantity)  # Convert back to float
                            ingredient.save()
                context["success"] = "Inventory updated successfully."
            except (InvalidOperation, Exception) as e:
                context["error"] = f"Error updating inventory: {e}"

        elif mode == "export_csv":
            response = HttpResponse(content_type="text/csv")
            response["Content-Disposition"] = 'attachment; filename="ingredients_required.csv"'

            writer = csv.writer(response)
            writer.writerow(["Ingredient", "Quantity Needed", "Unit", "Unit Cost", "Total Cost"])
            for name, data in context["ingredients_required"].items():
                writer.writerow([name, f"{data['quantity']:.2f}", data["unit_type"], f"${data['unit_cost']:.2f}", f"${data['total_cost']:.2f}"])
            return response

    return render(request, "reports/estimate.html", context)








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