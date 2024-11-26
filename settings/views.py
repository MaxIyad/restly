from django.shortcuts import render, redirect
from .models import Settings
from .forms import SettingsForm

def settings_view(request):
    settings_instance, created = Settings.objects.get_or_create(id=1)
    
    if request.method == 'POST':
        form = SettingsForm(request.POST, instance=settings_instance)
        if form.is_valid():
            form.save()
            return redirect('/')  # Redirect after saving
    else:
        form = SettingsForm(instance=settings_instance)
    
    return render(request, 'settings/settings.html', {
        'form': form,
        'settings': settings_instance
    })