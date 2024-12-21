from django.db import models
from menu.models import MenuItem, MenuItemVariation
from inventory.models import Ingredient
import uuid



    
class Sale(models.Model):
    timestamp = models.DateTimeField(auto_now_add=True)
    total_amount = models.DecimalField(max_digits=10, decimal_places=2)
    payment_method = models.CharField(
        max_length=50, 
        choices=[('cash', 'Cash'), ('card', 'Card'), ('digital', 'Digital'), ('sumup', 'SumUp Terminal')]
    )
    change_given = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    sumup_transaction_id = models.CharField(max_length=100, null=True, blank=True)


class CartItem(models.Model):
    sale = models.ForeignKey(Sale, on_delete=models.CASCADE, related_name="cart_items", null=True, blank=True)
    menu_item = models.ForeignKey(MenuItem, on_delete=models.CASCADE, null=True, blank=True)
    variation = models.ForeignKey(MenuItemVariation, on_delete=models.CASCADE, null=True, blank=True)
    quantity = models.PositiveIntegerField(default=1)
    price = models.DecimalField(max_digits=10, decimal_places=2)

    def subtotal(self):
        return self.quantity * self.price