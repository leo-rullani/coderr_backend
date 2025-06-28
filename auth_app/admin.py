from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from .models import CustomUser

@admin.register(CustomUser)
class CustomUserAdmin(UserAdmin):
    """
    Custom admin panel for the CustomUser model.
    Displays username, email, role and user status in the admin list view.
    """
    model = CustomUser
    list_display = ("username", "email", "role", "is_active", "is_staff")
    fieldsets = UserAdmin.fieldsets + (
        ("Role Info", {"fields": ("role",)}),
    )