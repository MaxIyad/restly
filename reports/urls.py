from django.urls import path
from . import views

urlpatterns = [
    path("estimate/", views.estimate_view, name="estimate_report"),
    path("reports/sales/", views.sales_view, name="sales_report"),
    path("orders/", views.order_history_view, name="order_history"),
]
