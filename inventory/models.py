from django.db import models
from django.utils import timezone
from settings.models import Settings

# Category model for ingredient filtering
class Category(models.Model):
    name = models.CharField(max_length=100, unique=True, default="global")

    def __str__(self):
        return self.name

# Ingredient model
class Ingredient(models.Model):
    
    
    UNIT_TYPES = [
        ('g', 'gram'),
        ('ml', 'milliliter'),
        ('pce', 'piece'),
        ('cm', 'centimeter'),
    ]



    name = models.CharField(max_length=255, unique=True)
    quantity = models.FloatField()  # Quantity in stock
    category = models.ForeignKey(Category, on_delete=models.CASCADE)
    unit_type = models.CharField(max_length=10, choices=UNIT_TYPES)
    unit_multiplier = models.FloatField()  # Multiplier for unit type
    unit_cost = models.DecimalField(max_digits=10, decimal_places=2)  # Cost per unit
    threshold = models.FloatField()  # Minimum threshold for inventory
    estimated_usage = models.FloatField(null=True, blank=True)  # Optional, estimated usage per day
    total_cost = models.DecimalField(max_digits=12, decimal_places=2, editable=False)

    def save(self, *args, **kwargs):
        # Calculate the total cost for current quantity
        self.total_cost = self.quantity * self.unit_cost
        super().save(*args, **kwargs)

    def __str__(self):
        return self.name

    def is_below_threshold(self):
        return self.quantity < self.threshold


# InventoryLog model for tracking changes
class InventoryLog(models.Model):
    SOURCE_TYPES = [
        ('order', 'Order'),
        ('manual', 'Manual Adjustment'),
        ('delivery', 'Delivery'),
        ('inventory', 'Inventory')
    ]

    ingredient = models.ForeignKey(Ingredient, on_delete=models.CASCADE)
    quantity_change = models.FloatField()  # Positive or negative change
    source = models.CharField(max_length=20, choices=SOURCE_TYPES)
    timestamp = models.DateTimeField(default=timezone.now)

    def __str__(self):
        return f"{self.ingredient.name} | {self.source} | {self.quantity_change} | {self.timestamp}"

    class Meta:
        ordering = ['-timestamp']

    @staticmethod
    def log_change(ingredient, quantity_change, source):
        # Method to create a log entry and adjust the ingredient's quantity
        ingredient.quantity += quantity_change
        ingredient.save()
        InventoryLog.objects.create(ingredient=ingredient, quantity_change=quantity_change, source=source)
