from django.db import models

from settings.utils import use_imperial_units

from simple_history.models import HistoricalRecords

from decimal import Decimal

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
        ('oz', 'ounce'),
        ('fl_oz', 'fluid ounce'),
        ('pcs', 'piece'),
        ('in', 'inch'),
    ]


    name = models.CharField(max_length=255)
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
        
    @property
    def converted_quantity(self):
        """Converts quantity to a higher unit if it meets or exceeds the threshold for conversion."""
        
        # Conversion factors for metric and imperial units
        metric_conversion_factors = {
            'g': Decimal('1000'),       # 1000 grams = 1 kg
            'ml': Decimal('1000'),      # 1000 milliliters = 1 liter
            'cm': Decimal('100'),       # 100 cm = 1 m
            'pce': Decimal('1'),        # No conversion for pieces
        }
        
        imperial_conversion_factors = {
            'oz': Decimal('16'),        # 16 ounces = 1 pound
            'fl_oz': Decimal('128'),    # 128 fluid ounces = 1 gallon
            'in': Decimal('12'),        # 12 inches = 1 foot
            'pcs': Decimal('1'),        # No conversion for pieces
        }

        # Choose the appropriate conversion factors based on the unit type
        if self.unit_type in metric_conversion_factors:
            conversion_factor = metric_conversion_factors[self.unit_type]
            higher_unit = {'g': 'kg', 'ml': 'L', 'cm': 'm'}.get(self.unit_type, self.unit_type)
        elif self.unit_type in imperial_conversion_factors:
            conversion_factor = imperial_conversion_factors[self.unit_type]
            higher_unit = {'oz': 'lb', 'fl_oz': 'gal', 'in': 'ft'}.get(self.unit_type, self.unit_type)
        else:
            # Default if no conversion applies
            conversion_factor = Decimal('1')
            higher_unit = self.unit_type

        # Calculate the base quantity in terms of the unit and multiplier
        base_qty = Decimal(self.quantity) * Decimal(self.unit_multiplier)

        # Only convert if quantity meets or exceeds the conversion factor
        if base_qty < conversion_factor:
            # Return quantity in original unit
            return f"{base_qty}{self.unit_type}"

        # Convert quantity to higher unit if the threshold is met
        converted_qty = base_qty / conversion_factor
        return f"{converted_qty}{higher_unit}"
    

