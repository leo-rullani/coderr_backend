from django.contrib import admin
from .models import Order

@admin.register(Order)
class OrderAdmin(admin.ModelAdmin):
    """
    Admin interface for Order model.
    Shows all main fields, enables search, filter, and ordering.
    """
    list_display = (
        "id",
        "title",
        "customer_user",
        "business_user",
        "price",
        "offer_type",
        "status",
        "created_at",
    )
    search_fields = ("title", "customer_user__username", "business_user__username")
    list_filter = ("status", "created_at", "offer_type")
    date_hierarchy = "created_at"