from django.db import models
from django.contrib.auth.models import User
from django.conf import settings

class Order(models.Model):
    customer_name = models.CharField(max_length=255, default="Unknown")  # Customer name
    taken_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,  # Dynamically reference the custom user model
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        default=None,
    )
    order_date = models.DateTimeField(auto_now_add=True)  # Auto timestamp
    total_cost = models.DecimalField(max_digits=10, decimal_places=2)
    total_revenue = models.DecimalField(max_digits=10, decimal_places=2)
    total_profit = models.DecimalField(max_digits=10, decimal_places=2)

    def __str__(self):
        return f"Order {self.id} by {self.customer_name}"