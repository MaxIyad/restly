from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import get_user_model, login, logout, authenticate, update_session_auth_hash, get_backends
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.utils.timezone import make_aware
from .forms import SignupForm, LoginForm
from django.urls import reverse
from .models import CustomAccessLog, Customer
from django.core.exceptions import SuspiciousOperation
from django.contrib.auth.hashers import check_password, make_password
from datetime import datetime, timedelta
from django.core.paginator import Paginator
from axes.models import AccessLog
from django.http import HttpResponse
import csv


CustomUser = get_user_model()

def signup_view(request):
    if request.method == "POST":
        form = SignupForm(request.POST)
        if form.is_valid():
            user = CustomUser(
                username=form.cleaned_data["username"],
                email=form.cleaned_data["email"],
                pin=form.cleaned_data["pin"],  # Save the PIN
            )
            user.set_password(form.cleaned_data["password"])  # Hash the password
            user.save()
            # Explicitly set the backend for login to avoid ambiguity
            backend = get_backends()[0]
            user.backend = f"{backend.__module__}.{backend.__class__.__name__}"
            login(request, user, backend=user.backend)
            messages.success(request, "Account created successfully.")
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
    if request.method == "POST":
        form = LoginForm(request.POST)
        if form.is_valid():
            username = form.cleaned_data["username"]
            password = form.cleaned_data.get("password", "")
            ip_address = get_client_ip(request)
            path_info = request.path
            user_agent = request.META.get('HTTP_USER_AGENT', 'Unknown')

            user = authenticate(request, username=username, password=password)
            ip_address = get_client_ip(request)

            if not user:
                # Log reason into AccessLog
                CustomAccessLog.objects.create(
                    custom_username=username,
                    custom_ip_address=ip_address,
                    custom_attempt_time=datetime.now(),
                    reason="Invalid username or password",
                    custom_path_info=path_info,
                    custom_user_agent=user_agent,
                    success=False,
                )
                messages.error(request, "Invalid username or password.")
                return render(request, "accounts/login.html", {"form": form})

            # Login successful
            login(request, user)
            CustomAccessLog.objects.create(
                custom_username=username,
                custom_ip_address=ip_address,
                custom_attempt_time=datetime.now(),
                reason="Login successful",
                custom_path_info=path_info,
                custom_user_agent=user_agent,
                success=False,
            )
            messages.success(request, "Login successful!")
            return redirect("profile")
    else:
        form = LoginForm()

    return render(request, "accounts/login.html", {"form": form})



@login_required
def login_attempts_view(request):
    if not request.user.is_superuser:
        return redirect("access_denied")

    # Get filtering options from the request
    username = request.GET.get("username", "").strip()
    ip_address = request.GET.get("ip_address", "").strip()
    start_date = request.GET.get("start_date", "")
    end_date = request.GET.get("end_date", "")
    reason = request.GET.get("reason", "").strip()

    # Base queryset
    attempts = CustomAccessLog.objects.all()

    # Apply filters
    if username:
        attempts = attempts.filter(custom_username__icontains=username)
    if ip_address:
        attempts = attempts.filter(custom_ip_address__icontains=ip_address)
    if start_date:
        try:
            start_date_time = make_aware(datetime.strptime(start_date, "%Y-%m-%d"))
            attempts = attempts.filter(custom_attempt_time__gte=start_date_time)
        except ValueError:
            pass  # Handle invalid date format gracefully
    if end_date:
        try:
            # Add 23:59:59 to the end date
            end_date_time = make_aware(datetime.strptime(end_date, "%Y-%m-%d") + timedelta(days=1, seconds=-1))
            attempts = attempts.filter(custom_attempt_time__lte=end_date_time)
        except ValueError:
            pass  # Handle invalid date format gracefully
    if reason:
        attempts = attempts.filter(reason__icontains=reason)

    # Handle export functionality
    if "export" in request.GET:
        response = HttpResponse(content_type="text/csv")
        response["Content-Disposition"] = 'attachment; filename="login_attempts.csv"'
        writer = csv.writer(response)
        writer.writerow(["Attempt Time", "Username", "IP", "Reason", "Path", "User Agent"])
        for attempt in attempts:
            writer.writerow([
                attempt.custom_attempt_time,
                attempt.custom_username,
                attempt.custom_ip_address,
                attempt.reason,
                attempt.custom_path_info,
                attempt.custom_user_agent,
            ])
        return response

    # Paginate the results
    paginator = Paginator(attempts.order_by("-custom_attempt_time"), 10)
    page_number = request.GET.get("page")
    page_obj = paginator.get_page(page_number)

    return render(request, "accounts/login_attempts.html", {
        "page_obj": page_obj,
        "username": username,
        "ip_address": ip_address,
        "start_date": start_date,
        "end_date": end_date,
        "reason": reason,
    })

            



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
        elif len(new_pin) < 4 or not new_pin.isdigit():
            messages.error(request, "The new PIN must be between 4 and 20 digits.")
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
        return redirect("access_denied")
    
    user = get_object_or_404(CustomUser, id=user_id)

    if request.method == "POST":
        if "update_permissions" in request.POST:
            # Extract updated lists of allowed and denied URLs
            new_allowed_urls = set(request.POST.getlist("allowed_urls"))
            new_denied_urls = set(request.POST.getlist("denied_urls"))

            # Compute the effective changes
            current_allowed_urls = set(user.allowed_urls)
            current_denied_urls = set(user.denied_urls)

            # Finalize new states
            user.allowed_urls = list(new_allowed_urls)
            user.denied_urls = list(new_denied_urls - new_allowed_urls)  # Ensure no overlap
            user.save()

            messages.success(request, f"Permissions updated for {user.username}.")
        elif "toggle_restrictions" in request.POST:
            enforce_restrictions = "enforce_url_restrictions" in request.POST
            user.enforce_url_restrictions = enforce_restrictions
            user.save()
            state = "enabled" if enforce_restrictions else "disabled"
            messages.success(request, f"URL restrictions {state} for {user.username}.")

            return redirect("manage_permissions", user_id=user_id)
        
        elif "update_pin" in request.POST:
            new_pin = request.POST.get("new_pin")
            confirm_new_pin = request.POST.get("confirm_new_pin")

            if new_pin != confirm_new_pin:
                messages.error(request, "The new PINs do not match.")
            elif len(new_pin) < 4 or len(new_pin) > 20:
                messages.error(request, "The new PIN must be between 4 and 20 characters.")
            else:
                user.pin = new_pin # Hash the pin
                user.save()
                messages.success(request, f"PIN for {user.username} has been updated.")

        elif "reset_password" in request.POST:
            new_password = request.POST.get("new_password")
            confirm_password = request.POST.get("confirm_password")
            if new_password != confirm_password:
                messages.error(request, "Passwords do not match.")
            elif len(new_password) < 8:
                messages.error(request, "Password must be at least 8 characters.")
            else:
                user.set_password(new_password)
                user.save()
                messages.success(request, f"Password reset for {user.username}.")

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
            elif len(new_pin) < 4 or not new_pin.isdigit():
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
        "denied_urls": user.denied_urls,
    }
    return render(request, "accounts/manage_permissions.html", context)


@login_required
def create_user_view(request):
    if not request.user.is_superuser:
        return redirect("access_denied")

    if request.method == "POST":
        form = SignupForm(request.POST)
        if form.is_valid():
            # Extract form data
            username = form.cleaned_data["username"]
            email = form.cleaned_data["email"]
            password = form.cleaned_data["password"]
            pin = form.cleaned_data["pin"]
            is_superuser = request.POST.get("is_superuser", "off") == "on"

            # Create the user
            new_user = CustomUser.objects.create_user(
                username=username,
                email=email,
                pin=pin,
                password=password,
                is_staff=is_superuser,
                is_superuser=is_superuser,
            )
            messages.success(
                request,
                f"User '{new_user.username}' created successfully. {'Superuser privileges granted.' if is_superuser else ''}",
            )
            return redirect("profile")
    else:
        form = SignupForm()

    context = {"form": form}
    return render(request, "accounts/create_user.html", context)







def access_denied_view(request):
    return render(request, "accounts/access_denied.html")






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
