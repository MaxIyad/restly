from django.shortcuts import render, redirect, get_object_or_404
from .models import Ingredient, CartItem
from .forms import AddToCartForm, PaymentForm
from menu.models import MenuItem, MenuItemVariation
from django.core.serializers.json import DjangoJSONEncoder
from django.http import JsonResponse

def pos_view(request):
    cart = get_cart(request)
    menu_items = MenuItem.objects.filter(is_active=True).prefetch_related('variations')

    if request.method == 'POST':
        form = AddToCartForm(request.POST)
        if form.is_valid():
            menu_item_id = form.cleaned_data['menu_item_id']
            variation_id = form.cleaned_data.get('variation_id')
            quantity = form.cleaned_data['quantity']

            # Fetch menu item and optionally the variation
            menu_item = MenuItem.objects.get(id=menu_item_id)
            variation = MenuItemVariation.objects.filter(id=variation_id).first() if variation_id else None
            price = variation.price if variation else menu_item.cost

            # Add to cart
            cart.append({
                'menu_item_id': menu_item.id,
                'variation_id': variation.id if variation else None,
                'quantity': quantity,
                'price': float(price),
            })
            request.session['cart'] = cart  # Save back to session
            return redirect('pos')

    # Serialize menu items and their variations
    menu_item_data = serialize_menu_items(menu_items)

    # Pass data to the template
    context = {
        'menu_items': menu_items,
        'cart': cart,
        'form': AddToCartForm(),
        'menu_item_data': menu_item_data,  # Add serialized data for JS usage
    }
    return render(request, 'pos/pos.html', context)


def get_cart(request):
    cart = request.session.get('cart', [])
    if not isinstance(cart, list):
        cart = []
        request.session['cart'] = cart
    return cart


def checkout_view(request):
    cart = request.session.get('cart', [])
    if not cart:
        return redirect('pos')

    if request.method == 'POST':
        payment_form = PaymentForm(request.POST)
        if payment_form.is_valid():
            sale = payment_form.save()
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

                # Deduct ingredients from inventory
                recipe_ingredients = variation.variation_recipe_ingredients.all() if variation else menu_item.menu_item_recipe_ingredients.all()
                for recipe_ingredient in recipe_ingredients:
                    ingredient = recipe_ingredient.ingredient
                    ingredient.quantity -= recipe_ingredient.quantity * item['quantity']
                    ingredient.save()

            request.session['cart'] = []  # Clear cart
            return redirect('pos')

    total_amount = sum(item['price'] * item['quantity'] for item in cart)
    context = {
        'cart': cart,
        'total_amount': total_amount,
        'payment_form': PaymentForm(initial={'total_amount': total_amount}),
    }
    return render(request, 'pos/checkout.html', context)


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
