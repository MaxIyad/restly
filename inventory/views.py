from django.shortcuts import render
from .models import Ingredient, Category
from settings.models import Settings 

def ingredient_list(request):
    # Get all categories and associated ingredients
    categories = Category.objects.prefetch_related('ingredient_set').all()
    # Retrieve the settings instance, or use a default if it doesn't exist
    settings_instance = Settings.objects.first()

    context = {
        'categories': categories,
        'settings': settings_instance,
    }
    return render(request, 'inventory/ingredient_list.html', context)

