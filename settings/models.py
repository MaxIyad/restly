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

    def __str__(self):
        return "Global Settings"
