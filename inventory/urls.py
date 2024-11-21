# inventory/urls.py:

from django.urls import path
from . import views

urlpatterns = [
    path('', views.ingredient_list, name='inventory'),
    path('row-add/', views.row_add, name="row_add"),
    path('category-add/', views.category_add, name="category_add"),
    path('take-inventory/', views.take_inventory, name='take_inventory'),
    path('order/', views.order_inventory, name='order_inventory'),
    path('print/', views.print_inventory, name='print_inventory'),
    path('delivery/', views.delivery_inventory, name='delivery_inventory'),
    path('history/', views.inventory_history, name='inventory_history'),
    path('export_inventory/<str:file_format>/', views.export_inventory, name='export_inventory'),
    path('export_history/<str:file_format>/', views.export_history, name='export_history'),
    path('<str:category_name>/<str:ingredient_name>/', views.ingredient_details, name='ingredient_details'),
]
