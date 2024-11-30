# menu/urls.py:
from django.urls import path
from . import views
from .views import duplicate_menu

urlpatterns = [
    path('', views.menu_list, name='menu_list'),
    path('<int:menu_id>/duplicate/', duplicate_menu, name='duplicate_menu'),
    path('<str:menu_slug>/', views.menu_detail, name='menu_detail'),
    path('<str:menu_slug>/order', views.order_menu, name='order_menu'),
    path('<str:menu_slug>/<str:category_slug>/<str:menu_item_slug>/', views.menu_item_detail, name='menu_item_detail'),
    path('<str:menu_slug>/<str:category_slug>/<str:menu_item_slug>/simulate_order/', views.simulate_order, name='simulate_order'),
]