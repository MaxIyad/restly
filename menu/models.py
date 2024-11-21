# menu/models.py
from django.db import models
from inventory.models import Ingredient, Category
from django.utils.text import slugify




class Menu(models.Model):
    name = models.CharField(max_length=255, unique=True)
    slug = models.SlugField(max_length=255, unique=True, blank=True)
    is_active = models.BooleanField(default=False)

    def save(self, *args, **kwargs):
        if not self.slug or Menu.objects.filter(name=self.name).exclude(id=self.id).exists():
            base_slug = slugify(self.name)
            slug = base_slug
            counter = 1
            while Menu.objects.filter(slug=slug).exclude(id=self.id).exists():
                slug = f"{base_slug}-{counter}"
                counter += 1
            self.slug = slug

        if self.is_active:
            Menu.objects.filter(is_active=True).update(is_active=False)

        super().save(*args, **kwargs)

    def __str__(self):
        return self.name




class MenuCategory(models.Model):
    name = models.CharField(max_length=255)
    slug = models.SlugField(max_length=255, unique=True, blank=True)
    menu = models.ForeignKey(Menu, on_delete=models.CASCADE, related_name="categories")

    class Meta:
        unique_together = ('name', 'menu')

    def save(self, *args, **kwargs):
        if not self.slug or MenuCategory.objects.filter(name=self.name, menu=self.menu).exclude(id=self.id).exists():
            base_slug = slugify(self.name)
            slug = f"{self.menu.slug}-{base_slug}"  # Include menu slug for uniqueness
            counter = 1
            while MenuCategory.objects.filter(slug=slug).exclude(id=self.id).exists():
                slug = f"{self.menu.slug}-{base_slug}-{counter}"
                counter += 1
            self.slug = slug


        super().save(*args, **kwargs)

    def __str__(self):
        return self.name





class MenuItem(models.Model):
    name = models.CharField(max_length=255)
    slug = models.SlugField(max_length=255, unique=True, blank=True)
    category = models.ForeignKey(MenuCategory, on_delete=models.CASCADE, related_name="items")
    description = models.TextField(blank=True, null=True)


    def save(self, *args, **kwargs):
        if not self.slug or MenuItem.objects.filter(name=self.name, category=self.category).exclude(id=self.id).exists():
            base_slug = slugify(self.name)
            slug = f"{self.category.slug}-{base_slug}"  # Include category slug for uniqueness
            counter = 1
            while MenuItem.objects.filter(slug=slug).exclude(id=self.id).exists():
                slug = f"{self.category.slug}-{base_slug}-{counter}"
                counter += 1
            self.slug = slug
        super().save(*args, **kwargs)

    def __str__(self):
        return self.name


class RecipeIngredient(models.Model):
    menu_item = models.ForeignKey(MenuItem, related_name="recipe_ingredients", on_delete=models.CASCADE)
    ingredient = models.ForeignKey(Ingredient, on_delete=models.CASCADE)
    quantity = models.FloatField(help_text="Quantity of the ingredient used in the recipe")
    category = models.ForeignKey(Category, on_delete=models.CASCADE, null=True, blank=True, help_text="Category to deplete from")

    def __str__(self):
        return f"{self.ingredient.name} ({self.quantity}) for {self.menu_item.name}"
