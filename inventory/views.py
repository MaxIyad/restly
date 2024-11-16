from django.shortcuts import render, redirect
from .models import Ingredient, Category
from settings.models import Settings 
from .forms import IngredientForm, CategoryForm

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

def row_add(request):
    if request.method == 'POST':
        form = IngredientForm(request.POST)
        if form.is_valid():
            form.save()
            return redirect('ingredient_list')
    else:
        form = IngredientForm()

    return render(request, 'inventory/row_add.html', {'form': form})

def category_add(request):
    if request.method == 'POST':
        form = CategoryForm(request.POST)
        if form.is_valid():
            form.save()
            return redirect('inventory')  # Redirect to the inventory list
    else:
        form = CategoryForm()

    return render(request, 'inventory/category_add.html', {'form': form})