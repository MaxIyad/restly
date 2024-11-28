from django.urls import path, include
from .views import login_view, logout_view, profile_view, signup_view, manage_permissions_view, access_denied_view, login_attempts_view, create_user_view
from . import views

urlpatterns = [

    path("login/", login_view, name="login"),
    path("logout/", logout_view, name="logout"),
    path("profile/", profile_view, name="profile"),
    path("signup/", signup_view, name="signup"),
    path("manage-permissions/<int:user_id>/", manage_permissions_view, name="manage_permissions"),
    path("access_denied/", access_denied_view, name="access_denied"),
    path("login-attempts/", login_attempts_view, name="login_attempts"),
    path("create-user/", create_user_view, name="create_user"),


    ####

    path("customers/", views.customer_list, name="customer_list"),
    path("customers/<int:customer_id>/", views.customer_detail, name="customer_detail"),
    path("customers/create/", views.customer_create, name="customer_create"),
    path("customers/<int:customer_id>/edit/", views.customer_edit, name="customer_edit"),
    path("customers/<int:customer_id>/delete/", views.customer_delete, name="customer_delete"),
]
