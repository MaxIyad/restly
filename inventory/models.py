# inventory/models.py:

from django.db import models
from simple_history.models import HistoricalRecords
from decimal import Decimal, ROUND_HALF_UP
from django.core.exceptions import ValidationError
from django.utils.text import slugify

# Category model for ingredient filtering
class Category(models.Model):
    name = models.CharField(max_length=100, unique=True, default="global")
    slug = models.SlugField(max_length=100, unique=True, blank=True)
    order = models.PositiveIntegerField(default=1)

    class Meta:
        ordering = ['order'] 
        
    def save(self, *args, **kwargs):

        if self.pk:
            old_name = Category.objects.filter(pk=self.pk).values('name').first()
            if old_name and old_name['name'] != self.name:
                self.slug = None  # Reset slug to regenerate it


        if not self.slug:  # Generate slug only if it doesn't exist
            base_slug = slugify(self.name)
            slug = base_slug
            counter = 1
            while Category.objects.filter(slug=slug).exclude(id=self.id).exists():
                slug = f"{base_slug}-{counter}"
                counter += 1
            self.slug = slug
        super().save(*args, **kwargs)


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
        ('in', 'inch'),
    ]

    name = models.CharField(max_length=255)
    slug = models.SlugField(max_length=255, unique=True, blank=True)
    quantity = models.FloatField()  # Quantity in stock
    threshold = models.FloatField(default=0)  # Minimum threshold for inventory
    category = models.ForeignKey('Category', on_delete=models.CASCADE)
    unit_type = models.CharField(max_length=10, choices=UNIT_TYPES)
    unit_multiplier = models.FloatField()  # Multiplier for unit type
    unit_cost = models.FloatField()  # Cost per unit
    estimated_usage = models.FloatField(null=True, blank=True)  # Optional, estimated usage per day
    total_cost = models.DecimalField(max_digits=12, decimal_places=6, editable=False)
    history = HistoricalRecords()
    order = models.PositiveIntegerField(default=1)
    change_source = models.CharField(max_length=50, blank=True, null=True)

    class Meta:
        ordering = ['order']
        unique_together = ('name', 'category')

    def save(self, *args, **kwargs):
        # Calculate the total cost for current quantity
        self.name = self.name.lower()

        if self.pk:
            old_name = Ingredient.objects.filter(pk=self.pk).values('name').first()
            if old_name and old_name['name'] != self.name:
                self.slug = None  # Reset slug to regenerate it
                
        if not self.slug:  # Generate slug only if it doesn't exist
            base_slug = slugify(self.name)
            slug = base_slug
            counter = 1
            while Ingredient.objects.filter(slug=slug).exclude(id=self.id).exists():
                slug = f"{base_slug}-{counter}"
                counter += 1
            self.slug = slug
        self.total_cost = self.quantity * self.unit_cost
        super().save(*args, **kwargs)

    def clean(self):
    # Check for duplicate names in the same category
        if Ingredient.objects.filter(name__iexact=self.name, category=self.category).exclude(id=self.id).exists():
            raise ValidationError(f"The name '{self.name}' is already in use in the category '{self.category.name}'.")

    def __str__(self):
        return self.name.title()

    @property
    def converted_quantity(self):
        """Converts quantity to a higher unit if it meets or exceeds the threshold for conversion."""
        return self._convert_unit(self.quantity)

    @property
    def converted_threshold(self):
        """Converts threshold to a higher unit if it meets or exceeds the threshold for conversion."""
        return self._convert_unit(self.threshold)
        

    @property
    def is_below_threshold(self):
        """Checks if the quantity is below the threshold."""
        return self.quantity < self.threshold

    def _convert_unit(self, value):
        """Utility method to convert a value (quantity or threshold) based on the unit type."""
        metric_conversion_factors = {
            'g': Decimal('1000'),       # 1000 grams = 1 kg
            'ml': Decimal('1000'),      # 1000 milliliters = 1 liter
            'cm': Decimal('100'),       # 100 cm = 1 m
        }

        imperial_conversion_factors = {
            'oz': Decimal('16'),        # 16 ounces = 1 pound
            'fl_oz': Decimal('128'),    # 128 fluid ounces = 1 gallon
            'in': Decimal('12'),        # 12 inches = 1 foot
        }

        if self.unit_type in metric_conversion_factors:
            conversion_factor = metric_conversion_factors[self.unit_type]
            higher_unit = {'g': 'kg', 'ml': 'L', 'cm': 'm'}.get(self.unit_type, self.unit_type)
        elif self.unit_type in imperial_conversion_factors:
            conversion_factor = imperial_conversion_factors[self.unit_type]
            higher_unit = {'oz': 'lb', 'fl_oz': 'gal', 'in': 'ft'}.get(self.unit_type, self.unit_type)
        else:
            conversion_factor = Decimal('1')
            higher_unit = self.unit_type

        base_qty = Decimal(value) * Decimal(self.unit_multiplier)

        if base_qty < conversion_factor:
            return f"{base_qty.quantize(Decimal('.01'), rounding=ROUND_HALF_UP)}{self.unit_type}"

        converted_qty = base_qty / conversion_factor
        return f"{converted_qty.quantize(Decimal('.01'), rounding=ROUND_HALF_UP)}{higher_unit}"
