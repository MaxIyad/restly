from django.urls import path
from . import views

urlpatterns = [
    path("estimate/", views.estimate_view, name="report"),
]
