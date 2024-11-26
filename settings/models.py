# settings.models
from django.db import models

class Settings(models.Model):
    currency_type = models.CharField(
        max_length=3,
        choices=[
            ('USD', '$'), 
            ('EUR', '€'), 
            ('GBP', '£'),
        ],
        default='EUR'
    )
    theme = models.CharField(
        max_length=10,
        choices=[
            ('light', 'Light Theme'),
            ('dark', 'Dark Theme'),
        ],
        default='light'
    )

    def __str__(self):
        return "Global Settings"
