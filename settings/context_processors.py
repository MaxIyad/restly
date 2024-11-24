from .models import Settings

def global_settings(request):
    settings_instance = Settings.objects.first()
    return {
        'settings': settings_instance,
    }
