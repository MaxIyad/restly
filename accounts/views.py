from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import get_user_model, login, logout, authenticate, update_session_auth_hash, get_backends
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from .forms import SignupForm, LoginForm
from django.urls import reverse
from .models import LoginAttempt, Customer
from django.core.exceptions import SuspiciousOperation
from django.contrib.auth.hashers import check_password, make_password



CustomUser = get_user_model()

def signup_view(request):
    if request.method == "POST":
        form = SignupForm(request.POST)
        if form.is_valid():
            user = CustomUser(username=form.cleaned_data["username"])
            user.set_password(form.cleaned_data["pin"])
            user.save()
            messages.success(request, "Account created successfully. You are now logged in.")
            login(request, user)
            return redirect("profile")
    else:
        form = SignupForm()

    return render(request, "accounts/signup.html", {"form": form})




def get_client_ip(request):
    x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
    if x_forwarded_for:
        ip = x_forwarded_for.split(',')[0]
    else:
        ip = request.META.get('REMOTE_ADDR')
    return ip


#### Login ####
def login_view(request):
    ip_address = get_client_ip(request)

    if request.method == "POST":
        form = LoginForm(request.POST)
        if form.is_valid():
            username = form.cleaned_data["username"]
            pin = form.cleaned_data["pin"]

            # Check if the user exists
            try:
                user = CustomUser.objects.get(username=username)
            except CustomUser.DoesNotExist:
                # Log failed attempt due to invalid username
                LoginAttempt.objects.create(
                    username=username,
                    ip_address=ip_address,
                    success=False,
                    reason="Invalid username"
                )
                messages.error(request, "Invalid username.")
                return render(request, "accounts/login.html", {"form": form})

            # Check if the PIN matches
            if not check_password(pin, user.password):
                # Log failed attempt due to incorrect PIN
                LoginAttempt.objects.create(
                    username=username,
                    ip_address=ip_address,
                    success=False,
                    reason="Incorrect PIN"
                )
                messages.error(request, "Incorrect PIN.")
                return render(request, "accounts/login.html", {"form": form})

            # If all checks pass, log the user in
            # Set the backend explicitly
            backend = get_backends()[0]  # Use the first configured backend
            user.backend = f"{backend.__module__}.{backend.__class__.__name__}"

            login(request, user)
            LoginAttempt.objects.create(
                username=username,
                ip_address=ip_address,
                success=True,
                reason="Login successful"
            )
            messages.success(request, "Login successful!")
            return redirect("profile")
    else:
        form = LoginForm()

    return render(request, "accounts/login.html", {"form": form})


#### Logout ####

def logout_view(request):
    logout(request)
    messages.success(request, "You have been logged out.")
    return redirect("login")





@login_required
def profile_view(request):
    user = request.user 

    # Check if the user is a superuser
    all_users = CustomUser.objects.all() if user.is_superuser else None

    if request.method == "POST":
        current_pin = request.POST.get("current_pin")
        new_pin = request.POST.get("new_pin")
        confirm_new_pin = request.POST.get("confirm_new_pin")

        if not user.check_password(current_pin):
            messages.error(request, "The current PIN is incorrect.")
        elif new_pin != confirm_new_pin:
            messages.error(request, "The new PINs do not match.")
        elif len(new_pin) != 4 or not new_pin.isdigit():
            messages.error(request, "The new PIN must be exactly 4 digits.")
        else:
            user.set_password(new_pin)  
            user.save()
            update_session_auth_hash(request, user)  
            messages.success(request, "Your PIN has been successfully updated.")
            return redirect("profile") 

    context = {
        "user": user,
        "all_users": all_users,  # Pass all users to the context for superusers
    }
    return render(request, "accounts/profile.html", context)





########################################################################################################################################################
########################################################################################################################################################
########################################################################################################################################################




@login_required
def manage_permissions_view(request, user_id):
    if not request.user.is_superuser:
        return redirect("access_denied")  # Redirect if not superuser

    user = get_object_or_404(CustomUser, id=user_id)

    if request.method == "POST":
        if "update_permissions" in request.POST:
            allowed_urls = request.POST.getlist("allowed_urls") 
            denied_urls = request.POST.getlist("denied_urls")   
            user.allowed_urls = allowed_urls
            user.save()
            messages.success(request, f"Permissions updated for {user.username}.")

        elif "activate_account" in request.POST:
            user.is_active = True
            user.save()
            messages.success(request, f"Account for {user.username} has been activated.")

        elif "deactivate_account" in request.POST:
            user.is_active = False
            user.save()
            messages.success(request, f"Account for {user.username} has been deactivated.")

        elif "delete_account" in request.POST:
            username = user.username
            user.delete()
            messages.success(request, f"Account for {username} has been deleted.")
            return redirect("profile")  # Redirect after deletion
        
        elif "update_details" in request.POST:
            user.full_name = request.POST.get("full_name")
            user.nick_name = request.POST.get("nick_name")
            user.hourly_wage = request.POST.get("hourly_wage")
            user.staff_meal_limit = request.POST.get("staff_meal_limit")
            user.address = request.POST.get("address")
            user.phone_number = request.POST.get("phone_number")
            user.role = request.POST.get("role")
            user.email = request.POST.get("email")
            user.save()
            messages.success(request, f"Details updated for {user.username}.")

        elif "update_pin" in request.POST:
            new_pin = request.POST.get("new_pin")
            confirm_new_pin = request.POST.get("confirm_new_pin")

            if new_pin != confirm_new_pin:
                messages.error(request, "The new PINs do not match.")
            elif len(new_pin) != 4 or not new_pin.isdigit():
                messages.error(request, "The new PIN must be exactly 4 digits.")
            else:
                user.password = make_password(new_pin)  # Hash the new PIN
                user.save()
                messages.success(request, f"PIN for {user.username} has been updated.")

        return redirect("manage_permissions", user_id=user_id)

    # Define a list of all available URLs
    available_urls = [
        "/reports/orders/",
        "/accounts/profile/",
        "/menu/",
        "/reports/sales/",
    ]

    context = {
        "user": user,
        "available_urls": available_urls,
        "allowed_urls": user.allowed_urls,
    }
    return render(request, "accounts/manage_permissions.html", context)







def access_denied_view(request):
    return render(request, "accounts/access_denied.html")



from django.contrib.admin.views.decorators import staff_member_required

@staff_member_required
def login_attempts_view(request):
    attempts = LoginAttempt.objects.all().order_by("-timestamp")
    return render(request, "accounts/login_attempts.html", {"attempts": attempts})







########################################################################################################################################################
########################################################################################################################################################
########################################################################################################################################################






def customer_list(request):
    customers = Customer.objects.all()
    return render(request, "customers/customer_list.html", {"customers": customers})

def customer_detail(request, customer_id):
    customer = get_object_or_404(Customer, id=customer_id)
    return render(request, "customers/customer_detail.html", {"customer": customer})

def customer_create(request):
    if request.method == "POST":
        name = request.POST.get("name")
        phone = request.POST.get("phone")
        email = request.POST.get("email")
        address = request.POST.get("address")
        allergens = request.POST.get("allergens")
        notes = request.POST.get("notes")

        if not name:
            messages.error(request, "Customer name is required.")
        else:
            customer = Customer.objects.create(
                name=name,
                phone=phone,
                email=email,
                address=address,
                allergens=allergens,
                notes=notes,
            )
            messages.success(request, "Customer created successfully.")
            return redirect("customer_list")

    return render(request, "customers/customer_create.html")

def customer_edit(request, customer_id):
    customer = get_object_or_404(Customer, id=customer_id)
    if request.method == "POST":
        customer.name = request.POST.get("name", customer.name)
        customer.phone = request.POST.get("phone", customer.phone)
        customer.email = request.POST.get("email", customer.email)
        customer.address = request.POST.get("address", customer.address)
        customer.allergens = request.POST.get("allergens", customer.allergens)
        customer.notes = request.POST.get("notes", customer.notes)
        customer.save()
        messages.success(request, "Customer updated successfully.")
        return redirect("customer_detail", customer_id=customer.id)

    return render(request, "customers/customer_edit.html", {"customer": customer})


def customer_delete(request, customer_id):
    customer = get_object_or_404(Customer, id=customer_id)
    if request.method == "POST":
        customer.delete()
        messages.success(request, "Customer deleted successfully.")
        return redirect("customer_list")
    return render(request, "customers/customer_delete.html", {"customer": customer})
