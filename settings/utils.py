from .models import Settings
from django.core.exceptions import AppRegistryNotReady


def use_imperial_units():
    try:
        settings = Settings.objects.first()
        return settings.use_imperial_units if settings else False
    except AppRegistryNotReady:
        # Fallback during migrations or setup when tables may not be ready
        return False
