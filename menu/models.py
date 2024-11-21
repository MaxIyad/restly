from django.db import models
from inventory.models import Ingredient, Category




class Menu(models.Model):
    name = models.CharField(max_length=255, unique=True)
    is_active = models.BooleanField(default=False)

    def save(self, *args, **kwargs):
        if self.is_active:
            Menu.objects.filter(is_active=True).update(is_active=False)
        super().save(*args, **kwargs)

    def __str__(self):
        return self.name




class MenuCategory(models.Model):
    name = models.CharField(max_length=255)
    menu = models.ForeignKey(Menu, on_delete=models.CASCADE, related_name="categories")

    class Meta:
        unique_together = ('name', 'menu')

    def __str__(self):
        return self.name





class MenuItem(models.Model):
    name = models.CharField(max_length=255)
    category = models.ForeignKey(MenuCategory, on_delete=models.CASCADE, related_name="items")
    description = models.TextField(blank=True, null=True)

    def __str__(self):
        return self.name


class RecipeIngredient(models.Model):
    menu_item = models.ForeignKey(MenuItem, related_name="recipe_ingredients", on_delete=models.CASCADE)
    ingredient = models.ForeignKey(Ingredient, on_delete=models.CASCADE)
    quantity = models.FloatField(help_text="Quantity of the ingredient used in the recipe")
    category = models.ForeignKey(Category, on_delete=models.CASCADE, null=True, blank=True, help_text="Category to deplete from")

    def __str__(self):
        return f"{self.ingredient.name} ({self.quantity}) for {self.menu_item.name}"
