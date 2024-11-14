from django.shortcuts import render, redirect
from .models import Settings
from .forms import SettingsForm

def settings_view(request):
    # Retrieve the single settings instance or create it if it doesn't exist
    settings_instance, created = Settings.objects.get_or_create(id=1)
    
    if request.method == 'POST':
        form = SettingsForm(request.POST, instance=settings_instance)
        if form.is_valid():
            form.save()  # Save all settings at once
            return redirect('')  # Redirect after saving to prevent re-submitting
    else:
        form = SettingsForm(instance=settings_instance)  # Populate form with current settings
    
    return render(request, 'settings/settings.html', {'form': form})