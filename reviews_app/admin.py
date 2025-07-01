from django.contrib import admin
from .models import Review

@admin.register(Review)
class ReviewAdmin(admin.ModelAdmin):
    """
    Admin interface for Review model.
    Shows main fields, enables search and filtering.
    """
    list_display = (
        "id",
        "reviewer",
        "business_user",
        "rating",
        "created_at",
    )
    search_fields = ("reviewer__username", "business_user__username", "description")
    list_filter = ("rating", "created_at")
    date_hierarchy = "created_at"