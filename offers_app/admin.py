from django.contrib import admin
from .models import Offer, OfferDetail

@admin.register(Offer)
class OfferAdmin(admin.ModelAdmin):
    """
    Admin interface for Offer model.
    Displays main fields, enables search and filtering.
    """
    list_display = ("id", "title", "user", "min_price", "created_at")
    search_fields = ("title", "user__username")
    list_filter = ("created_at",)
    date_hierarchy = "created_at"

@admin.register(OfferDetail)
class OfferDetailAdmin(admin.ModelAdmin):
    """
    Admin interface for OfferDetail model.
    Shows core fields, allows search and filtering by offer type.
    """
    list_display = ("id", "offer", "title", "price", "offer_type")
    search_fields = ("title", "offer__title", "offer_type")
    list_filter = ("offer_type",)