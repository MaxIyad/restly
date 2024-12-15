from django.urls import path
from . import views

urlpatterns = [
    path('', views.pos_view, name='pos'),
    path('checkout/', views.checkout_view, name='checkout'),
    
]
