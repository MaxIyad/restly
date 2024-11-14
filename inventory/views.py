from django.shortcuts import render
from .models import Ingredient, Category

def ingredient_list(request):
    # Get all categories and associated ingredients
    categories = Category.objects.prefetch_related('ingredient_set').all()

    context = {
        'categories': categories,
    }
    return render(request, 'inventory/ingredient_list.html', context)
