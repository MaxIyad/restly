from django.db import models
from inventory.models import Ingredient

class Sale(models.Model):
    timestamp = models.DateTimeField(auto_now_add=True)
    total_amount = models.DecimalField(max_digits=10, decimal_places=2)
    payment_method = models.CharField(
        max_length=50, 
        choices=[('cash', 'Cash'), ('card', 'Card'), ('digital', 'Digital')]
    )
    change_given = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)

class Cart(models.Model):
    sale = models.ForeignKey(Sale, on_delete=models.CASCADE, related_name='orders')
    ingredient = models.ForeignKey(Ingredient, on_delete=models.CASCADE)
    quantity = models.FloatField()
    price = models.DecimalField(max_digits=10, decimal_places=2)

    def subtotal(self):
        return self.quantity * self.price