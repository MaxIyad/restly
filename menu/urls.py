# menu/urls.py:
from django.urls import path
from . import views


urlpatterns = [
    path('', views.menu_list, name='menu_list'),
    path('<str:menu_name>/', views.menu_detail, name='menu_detail'),
    path('<str:menu_name>/<str:category_name>/', views.category_detail, name='category_detail'),
    path('<str:menu_name>/<str:category_name>/<str:menu_item_name>/', views.menu_item_detail, name='menu_item_detail'),
    path('<str:menu_name>/<str:category_name>/<str:menu_item_name>/simulate_order', views.simulate_order, name='simulate_order'),
]
