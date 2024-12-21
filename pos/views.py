from django.shortcuts import render, redirect, get_object_or_404
from .models import Ingredient, CartItem
from .forms import AddToCartForm, PaymentForm, CustomerForm
from menu.models import MenuItem, MenuItemVariation, MenuCategory, MenuItemSecondaryAssociation
from django.core.serializers.json import DjangoJSONEncoder
from django.http import JsonResponse
import requests
from django.conf import settings
from django.db.models import Prefetch

def pos_view(request):
    cart = get_cart(request)
    
    # Prefetch secondary associations for each menu item
    menu_items = MenuItem.objects.filter(is_active=True).prefetch_related(
        Prefetch(
            'secondary_associations',
            queryset=MenuItemSecondaryAssociation.objects.filter(is_active=True).select_related('secondary_item'),
            to_attr='active_secondary_associations'
        ),
        'variations'
    )
    
    categories = MenuCategory.objects.filter(
        is_active=True, 
        menu__is_secondary=False  # Exclude secondary menus
    ).prefetch_related(
        Prefetch('items', queryset=menu_items)
    )

    if request.method == 'POST':
        if 'menu_item_id' in request.POST:
            form = AddToCartForm(request.POST)
            if form.is_valid():
                menu_item_id = form.cleaned_data['menu_item_id']
                variation_id = form.cleaned_data.get('variation_id') or None
                quantity = form.cleaned_data['quantity']
                selected_sides = request.POST.get('selected_sides', '').split(',')

                # Fetch menu item and optionally the variation
                menu_item = MenuItem.objects.get(id=menu_item_id)
                variation = MenuItemVariation.objects.filter(id=variation_id).first() if variation_id else None
                price = variation.price if variation else menu_item.cost

                # Calculate the total price including sides
                total_price = price
                sides = []
                for side_id in selected_sides:
                    if side_id:
                        side_item = MenuItem.objects.get(id=side_id)
                        sides.append(side_item.name)
                        total_price += side_item.cost

                # Add to cart
                cart.append({
                    'menu_item_id': menu_item.id,
                    'variation_id': variation.id if variation else None,
                    'quantity': quantity,
                    'price': float(total_price),
                    'sides': sides,
                })
                request.session['cart'] = serialize_cart(cart)  # Save back to session
                return redirect('pos')
        else:
            customer_form = CustomerForm(request.POST)
            if customer_form.is_valid():
                customer_form.save()
                return redirect('pos')

    menu_item_data = serialize_menu_items(menu_items)
    context = {
        'cart': cart,
        'form': AddToCartForm(),
        'customer_form': CustomerForm(),
        'categories': categories,
        'menu_item_data': menu_item_data,  # Add serialized data for JS usage
    }
    return render(request, 'pos/pos.html', context)

def save_customer_info(request):
    if request.method == 'POST':
        customer_form = CustomerForm(request.POST)
        if customer_form.is_valid():
            customer_form.save()
            return redirect('pos')
    return redirect('pos')

def serialize_cart(cart):
    """Serialize the cart to store in the session."""
    serialized_cart = []
    for item in cart:
        serialized_cart.append({
            'menu_item_id': item['menu_item_id'],
            'variation_id': item['variation_id'],
            'quantity': item['quantity'],
            'price': item['price'],
            'sides': item.get('sides', []),
        })
    return serialized_cart

def get_cart(request):
    cart = request.session.get('cart', [])
    if not isinstance(cart, list):
        cart = []
        request.session['cart'] = cart
    return cart


SUMUP_API_URL = "https://api.sumup.com/v0.1/pos"


def checkout_view(request):
    cart = request.session.get('cart', [])
    if not cart:
        return redirect('pos')

    if request.method == 'POST':
        payment_form = PaymentForm(request.POST)
        if payment_form.is_valid():
            payment_method = payment_form.cleaned_data['payment_method']
            sale = payment_form.save(commit=False)
            total_amount = sum(item['price'] * item['quantity'] for item in cart)

            # Handle SumUp Payment
            if (payment_method == 'sumup'):
                sumup_response = send_to_sumup_terminal(total_amount)
                if sumup_response['success']:
                    sale.sumup_transaction_id = sumup_response['transaction_id']
                else:
                    # Handle SumUp error
                    print(request, "Failed to process payment on SumUp terminal.")
                    return redirect('checkout')

            # Finalize sale
            sale.total_amount = total_amount
            sale.save()

            for item in cart:
                menu_item = MenuItem.objects.get(id=item['menu_item_id'])
                variation = MenuItemVariation.objects.filter(id=item['variation_id']).first()
                CartItem.objects.create(
                    sale=sale,
                    menu_item=menu_item,
                    variation=variation,
                    quantity=item['quantity'],
                    price=item['price']
                )

                # Deduct inventory
                recipe_ingredients = variation.variation_recipe_ingredients.all() if variation else menu_item.menu_item_recipe_ingredients.all()
                for recipe_ingredient in recipe_ingredients:
                    ingredient = recipe_ingredient.ingredient
                    ingredient.quantity -= recipe_ingredient.quantity * item['quantity']
                    ingredient.save()

            # Clear cart and redirect to POS
            request.session['cart'] = []
            print(request, "Sale completed successfully!")
            return redirect('pos')

    total_amount = sum(item['price'] * item['quantity'] for item in cart)
    context = {
        'cart': cart,
        'total_amount': total_amount,
        'payment_form': PaymentForm(initial={'total_amount': total_amount}),
    }
    return render(request, 'pos/checkout.html', context)

def send_to_sumup_terminal(amount):
    """Send payment request to SumUp terminal."""
    try:
        # Example authentication (replace with actual token management)
        headers = {
            "Authorization": f"Bearer {settings.SUMUP_ACCESS_TOKEN}",
            "Content-Type": "application/json",
        }
        payload = {
            "amount": str(amount),
            "currency": "EUR",
            "checkout_reference": "Order12345",  # Replace with dynamic order reference later
        }
        response = requests.post(SUMUP_API_URL, json=payload, headers=headers)
        if response.status_code == 200:
            data = response.json()
            return {
                "success": True,
                "transaction_id": data.get("transaction_id"),
            }
        else:
            return {"success": False, "error": response.text}
    except Exception as e:
        return {"success": False, "error": str(e)}


def clear_cart_view(request):
    """Clears the cart stored in the session."""
    request.session['cart'] = []  # Reset the cart to an empty list
    return redirect('pos')  # Redirect to the POS page


def serialize_menu_items(menu_items):
    data = {}
    for item in menu_items:
        data[item.id] = [
            {
                'id': variation.id,
                'name': variation.name,
                'price': float(variation.price),
            } for variation in item.variations.all()
        ]
    return data
