from django.contrib.auth.models import AbstractBaseUser, BaseUserManager, PermissionsMixin
from django.db import models
from django.utils.timezone import now
from settings.models import Settings






class Customer(models.Model):
    name = models.CharField(max_length=255, default="Unknown", verbose_name="Customer Name")
    phone = models.CharField(max_length=15, null=True, blank=True, verbose_name="Phone Number")
    email = models.EmailField(null=True, blank=True, verbose_name="Email Address")
    address = models.TextField(null=True, blank=True, verbose_name="Address")
    allergens = models.TextField(null=True, blank=True, verbose_name="Allergens")
    notes = models.TextField(null=True, blank=True, verbose_name="Notes")

    def __str__(self):
        return self.name







# ---------------------------------------------------------------------------------------------------------------------------- #
class CustomUserManager(BaseUserManager):
    def create_user(self, username, pin, **extra_fields):
        if not username:
            raise ValueError("The Username field is required.")
        if not pin:
            raise ValueError("The PIN field is required.")
        user = self.model(username=username, **extra_fields)
        user.set_password(pin)  # Use set_password to hash the PIN
        user.save(using=self._db)
        return user

    def create_superuser(self, username, pin, **extra_fields):
        extra_fields.setdefault("is_staff", True)
        extra_fields.setdefault("is_superuser", True)

        if extra_fields.get("is_staff") is not True:
            raise ValueError("Superuser must have is_staff=True.")
        if extra_fields.get("is_superuser") is not True:
            raise ValueError("Superuser must have is_superuser=True.")

        return self.create_user(username, pin, **extra_fields)

class CustomUser(AbstractBaseUser, PermissionsMixin):
    username = models.CharField(max_length=150, unique=True)
    
    pin = models.CharField(max_length=4)  # PIN field
    is_active = models.BooleanField(default=True)
    is_staff = models.BooleanField(default=False)
    allowed_urls = models.JSONField(default=list, blank=True) 
    full_name = models.CharField(max_length=255, null=True, blank=True, verbose_name="Full Name")
    nick_name = models.CharField(max_length=100, null=True, blank=True, verbose_name="Nick Name")
    hourly_wage = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True, verbose_name="Hourly Wage")
    staff_meal_limit = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True, verbose_name="Staff Meal Limit")
    address = models.TextField(null=True, blank=True, verbose_name="Address")
    phone_number = models.CharField(max_length=15, null=True, blank=True, verbose_name="Phone Number")
    join_date = models.DateField(default=now, verbose_name="Join Date")
    role = models.CharField(max_length=50, choices=[("Staff", "Staff"), ("Manager", "Manager"), ("Admin", "Admin")], default="Staff")
    email = models.EmailField(unique=True, null=True, blank=True)

    objects = CustomUserManager()

    USERNAME_FIELD = "username"
    REQUIRED_FIELDS = []  

    def get_currency_symbol(self):
        settings_instance = Settings.objects.first()
        return settings_instance.get_currency_type_display() if settings_instance else "$"

    def __str__(self):
        return self.username



class LoginAttempt(models.Model):
    username = models.CharField(max_length=150)
    ip_address = models.GenericIPAddressField()
    timestamp = models.DateTimeField(auto_now_add=True)
    success = models.BooleanField()
    reason = models.CharField(max_length=255, blank=True, null=True)

    def __str__(self):
        status = "Success" if self.success else "Failed"
        return f"{self.timestamp} - {self.username} ({status}): {self.reason}"