from django.contrib import admin
from .models import UserProfile

@admin.register(UserProfile)
class UserProfileAdmin(admin.ModelAdmin):
    """
    Admin interface for UserProfile model.
    Shows main user profile fields, enables search and filtering.
    """
    list_display = (
        "id",
        "user",
        "first_name",
        "last_name",
        "location",
        "tel",
        "created_at",
    )
    search_fields = (
        "user__username",
        "first_name",
        "last_name",
        "location",
        "tel",
    )
    list_filter = ("created_at",)
    date_hierarchy = "created_at"