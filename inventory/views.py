from django.shortcuts import render
from .models import Ingredient

def ingredient_list(request):
    ingredients = Ingredient.objects.all()

    context = {
        'ingredients': ingredients,
    }
    return render(request, 'inventory/ingredient_list.html', context)
