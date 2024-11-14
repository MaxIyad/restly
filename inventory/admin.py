from django.contrib import admin
from inventory.models import Category, Ingredient
from settings.models import Settings

# Register your models here.
admin.site.register(Category)
admin.site.register(Ingredient)
admin.site.register(Settings)
