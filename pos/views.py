from django.shortcuts import render

from django.shortcuts import render, redirect, get_object_or_404
from .models import Ingredient, Sale, Cart
from .forms import AddToCartForm, PaymentForm

def pos_view(request):
    # Cart stored in session
    cart = request.session.get('cart', {})

    if request.method == 'POST':
        form = AddToCartForm(request.POST)
        if form.is_valid():
            ingredient_id = form.cleaned_data['ingredient_id']
            quantity = form.cleaned_data['quantity']
            cart[ingredient_id] = cart.get(ingredient_id, 0) + quantity
            request.session['cart'] = cart
            return redirect('pos')

    ingredients = Ingredient.objects.filter(visible=True)
    context = {
        'ingredients': ingredients,
        'cart': cart,
        'form': AddToCartForm(),
    }
    return render(request, 'pos/pos.html', context)

def checkout_view(request):
    cart = request.session.get('cart', {})
    if not cart:
        return redirect('pos')

    if request.method == 'POST':
        payment_form = PaymentForm(request.POST)
        if payment_form.is_valid():
            sale = payment_form.save()
            for ingredient_id, quantity in cart.items():
                ingredient = get_object_or_404(Ingredient, id=ingredient_id)
                price = ingredient.unit_cost
                Cart.objects.create(
                    sale=sale,
                    ingredient=ingredient,
                    quantity=quantity,
                    price=price
                )
                # Deduct inventory
                ingredient.quantity -= quantity
                ingredient.save()
            request.session['cart'] = {}  # Clear cart
            return redirect('pos')

    total_amount = sum(
        get_object_or_404(Ingredient, id=id).unit_cost * quantity
        for id, quantity in cart.items()
    )
    context = {
        'cart': cart,
        'total_amount': total_amount,
        'payment_form': PaymentForm(initial={'total_amount': total_amount}),
    }
    return render(request, 'pos/checkout.html', context)