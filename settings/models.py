from django.db import models
from django.core.exceptions import AppRegistryNotReady


class Settings(models.Model):
    use_imperial_units = models.BooleanField(default=False)
    currency_type = models.CharField(
        max_length=3,
        choices=[
            ('USD', '$'), 
            ('EUR', '€'), 
            ('GBP', '£'),
        ],
        default='EUR'
    )

    def __str__(self):
        return "Global Settings"
