'''from django.db import connection, OperationalError
from django.core.exceptions import AppRegistryNotReady
from .models import Settings

def use_imperial_units():
    try:
        # Ensure that the database is ready and migrations are not running
        if not connection.introspection.table_names():
            return False
        settings = Settings.objects.first()
        return settings.use_imperial_units if settings else False
    except (AppRegistryNotReady, OperationalError):
        # Return default value if the database isn't ready or Settings table is missing
        return False
'''

# settings/utils.py
from .models import Settings

def use_imperial_units():
    """Helper function to retrieve the imperial/metric preference."""
    settings = Settings.objects.first()
    return settings.use_imperial_units if settings else False
