from django.db import models

from settings.utils import use_imperial_units

from simple_history.models import HistoricalRecords


# Category model for ingredient filtering
class Category(models.Model):
    name = models.CharField(max_length=100, unique=True, default="global")

    def __str__(self):
        return self.name

# Ingredient model
class Ingredient(models.Model):
    

    if use_imperial_units():
        UNIT_TYPES = [
            ('oz', 'ounce'),
            ('fl_oz', 'fluid ounce'),
            ('pcs', 'piece'),
            ('in', 'inch'),
        ]
    else:
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
    unit_cost = models.FloatField()  # Cost per unit
    threshold = models.FloatField()  # Minimum threshold for inventory
    estimated_usage = models.FloatField(null=True, blank=True)  # Optional, estimated usage per day
    total_cost = models.DecimalField(max_digits=12, decimal_places=2, editable=False)
    history = HistoricalRecords()


    def save(self, *args, **kwargs):
        # Calculate the total cost for current quantity
        self.total_cost = self.quantity * self.unit_cost
        super().save(*args, **kwargs)

    def __str__(self):
        return self.name

    def is_below_threshold(self):
        return self.quantity < self.threshold
