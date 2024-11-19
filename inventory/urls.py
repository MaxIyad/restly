from django.urls import path
from . import views

urlpatterns = [
    path('', views.ingredient_list, name='inventory'),
    path('row_add/', views.row_add, name="row_add"),
    path('category_add/', views.category_add, name="category_add"),
    path('take-inventory/', views.take_inventory, name='take_inventory'),
    path('order/', views.order_inventory, name='order_inventory'),
    path('print/', views.print_inventory, name='print_inventory'),
]
