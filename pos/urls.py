from django.urls import path
from . import views

urlpatterns = [
    path('', views.pos_view, name='pos'),
    path('checkout/', views.checkout_view, name='checkout'),
    path('clear_cart/', views.clear_cart_view, name='clear_cart'),
    
]
