import csv
from django.db.models import Sum, F, FloatField, ExpressionWrapper
from menu.models import MenuItem, RecipeIngredient, Menu
from decimal import Decimal, InvalidOperation
from collections import defaultdict
from django.shortcuts import render
from django.http import HttpResponse
from django.db.models import Sum, F, FloatField, ExpressionWrapper
from django.db import transaction
from menu.models import MenuItem, RecipeIngredient
from inventory.models import Ingredient, Category
from settings.models import Settings
from .models import Order





def estimate_view(request):

    active_menu_items = MenuItem.objects.filter(
        category__menu__is_active=True, is_active=True
    ).select_related('category', 'category__menu')
    settings_instance = Settings.objects.first()

    context = {
        "ingredients_by_category": {},
        "revenue_goal": None,
        "profit_goal": None,
        "total_cost": None,
        "profitability": None,
        "profitability_percentage": None,
        "success": None,
        "error": None,
        "ingredient_distribution": [],
        "profitability_data": {},
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
        mode = request.POST.get("mode")

        if mode == "revenue_to_ingredients":
            try:
                # Validate input
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

<<<<<<< HEAD
<<<<<<< HEAD


                    if profit_goal is not None:
=======
                    if profit_goal is not None and revenue_goal is None:
                        # Revenue goal is derived from profit goal
>>>>>>> 7c333c8714fcdb16de4e0922cff771b8754a8493
=======
                    if profit_goal is not None:
>>>>>>> 13c3635acfc796b8e2d883388f6aa35f5dc8fe0d
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

                if revenue_goal is not None:
                    profit = revenue_goal - total_cost

                    # Fetch currency type from settings
                    currency_symbol = settings_instance.get_currency_type_display()

<<<<<<< HEAD
                # Calculate menu item data
                menu_items_data = []
                for item in active_menu_items:
                    # Total ingredient cost for the menu item
                    total_ingredient_cost = sum(
                        Decimal(ri.quantity) * Decimal(ri.ingredient.unit_cost or 0)
                        for ri in item.recipe_ingredients.select_related("ingredient")
                    )
                    price = item.cost or Decimal("0")
                    if price <= total_ingredient_cost:
                        continue  # Skip items with non-profitable pricing

                    margin_currency = price - total_ingredient_cost
                    margin_percentage = (margin_currency / total_ingredient_cost * 100) if total_ingredient_cost > 0 else 0
<<<<<<< HEAD

                    # If margin is zero or negative, skip calculation (otherwise, 404)
                    if margin_currency <= 0:
                        continue

                    units_needed = (profit_goal / margin_currency) if profit_goal else (revenue_goal / price)

                    revenue_acquired = price * round(units_needed, 2)
                    profit_acquired = margin_currency * round(units_needed,2)
=======
                    
                    # Calculate units needed
                    if revenue_goal and price > 0:
                        units_needed = (revenue_goal / price).quantize(Decimal("1"), rounding="ROUND_UP")
                    elif profit_goal and margin_currency > 0:
                        units_needed = (profit_goal / margin_currency).quantize(Decimal("1"), rounding="ROUND_UP")
=======
                    if profit_goal is not None:
                        context["goal_explanation"] = (
                            f"To achieve <span class='highlight-montery-goal-text'>{currency_symbol}{profit_goal:.2f}</span> in profit, "
                            f"{currency_symbol}{total_cost:.2f} will be spent on costs, "
                            f"resulting in {currency_symbol}{revenue_goal:.2f} as revenue."
                        )
>>>>>>> 13c3635acfc796b8e2d883388f6aa35f5dc8fe0d
                    else:
                        context["goal_explanation"] = (
                            f"To generate {currency_symbol}{revenue_goal:.2f} in revenue, "
                            f"{currency_symbol}{total_cost:.2f} will be spent on costs, "
                            f"leaving {currency_symbol}{profit:.2f} in profit."
                            )

<<<<<<< HEAD
                    total_revenue = price * units_needed
                    profit = total_revenue - (total_ingredient_cost * units_needed)
>>>>>>> 7c333c8714fcdb16de4e0922cff771b8754a8493

                    menu_items_data.append({
                        "name": item.name,
                        "cost": total_ingredient_cost,
                        "margin": margin_currency,
                        "price": price,
                        "units_needed": units_needed,
<<<<<<< HEAD
                        "revenue_acquired": revenue_acquired,
                        "profit_acquired": profit_acquired,
                        "margin_display": f"{margin_currency:.2f} ({margin_percentage:.2f}%)",
=======
                        "total_revenue": total_revenue,
                        "profit": profit,
>>>>>>> 7c333c8714fcdb16de4e0922cff771b8754a8493
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
=======
                context["revenue_goal"] = revenue_goal
                context["profit_goal"] = profit_goal
                context["total_cost"] = total_cost
                context["profitability"] = revenue_goal - total_cost if revenue_goal else None
                context["profitability_percentage"] = (
                    (context["profitability"] / revenue_goal * 100)
                    if revenue_goal and revenue_goal > 0
                    else Decimal(0)
                )
                context["profitability_data"] = {
                    "revenue_goal": float(revenue_goal or 0),
                    "total_cost": float(total_cost),
                    "profitability": float(context["profitability"] or 0),
                }
>>>>>>> 13c3635acfc796b8e2d883388f6aa35f5dc8fe0d

            except (InvalidOperation, Exception) as e:
                context["error"] = f"Error in calculation: {e}"

    context["ingredients_by_category"] = grouped_ingredients

    return render(request, "reports/estimate.html", context)



# Left off: the caluclations for message and the three lines under the goal entry feild are fucked.





###########################################################################################################################################################
###########################################################################################################################################################
###########################################################################################################################################################

from reports.models import Order

def order_history_view(request):
    orders = Order.objects.all().order_by('-order_date')  
    context = {
        "orders": orders,
    }

    return render(request, "reports/order_history.html", context)









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


###########################################################################################################################################################
###########################################################################################################################################################
###########################################################################################################################################################


def customer_list(request):
    customers = Customer.objects.all()
    return render(request, "customers/customer_list.html", {"customers": customers})

def customer_detail(request, customer_id):
    customer = get_object_or_404(Customer, id=customer_id)
    return render(request, "customers/customer_detail.html", {"customer": customer})

def customer_create(request):
    if request.method == "POST":
        name = request.POST.get("name")
        phone = request.POST.get("phone")
        email = request.POST.get("email")
        address = request.POST.get("address")
        allergens = request.POST.get("allergens")
        notes = request.POST.get("notes")

        if not name:
            messages.error(request, "Customer name is required.")
        else:
            customer = Customer.objects.create(
                name=name,
                phone=phone,
                email=email,
                address=address,
                allergens=allergens,
                notes=notes,
            )
            messages.success(request, "Customer created successfully.")
            return redirect("customer_list")

    return render(request, "customers/customer_create.html")

def customer_edit(request, customer_id):
    customer = get_object_or_404(Customer, id=customer_id)
    if request.method == "POST":
        customer.name = request.POST.get("name", customer.name)
        customer.phone = request.POST.get("phone", customer.phone)
        customer.email = request.POST.get("email", customer.email)
        customer.address = request.POST.get("address", customer.address)
        customer.allergens = request.POST.get("allergens", customer.allergens)
        customer.notes = request.POST.get("notes", customer.notes)
        customer.save()
        messages.success(request, "Customer updated successfully.")
        return redirect("customer_detail", customer_id=customer.id)

    return render(request, "customers/customer_edit.html", {"customer": customer})

def customer_delete(request, customer_id):
    customer = get_object_or_404(Customer, id=customer_id)
    if request.method == "POST":
        customer.delete()
        messages.success(request, "Customer deleted successfully.")
        return redirect("customer_list")
    return render(request, "customers/customer_delete.html", {"customer": customer})
