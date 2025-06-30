from django.db import models
from django.conf import settings

class Order(models.Model):
    """
    Model for storing orders between a customer and a business user.
    """
    STATUS_CHOICES = [
        ("in_progress", "In Progress"),
        ("completed", "Completed"),
        ("cancelled", "Cancelled"),
    ]

    customer_user = models.ForeignKey(
        settings.AUTH_USER_MODEL, related_name="customer_orders",
        on_delete=models.CASCADE
    )
    business_user = models.ForeignKey(
        settings.AUTH_USER_MODEL, related_name="business_orders",
        on_delete=models.CASCADE
    )
    title = models.CharField(max_length=200)
    revisions = models.PositiveIntegerField(default=0)
    delivery_time_in_days = models.PositiveIntegerField(default=0)
    price = models.DecimalField(max_digits=10, decimal_places=2)
    features = models.JSONField(default=list)
    offer_type = models.CharField(max_length=50)
    status = models.CharField(
        max_length=20, choices=STATUS_CHOICES, default="in_progress"
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"Order {self.id}: {self.title} ({self.customer_user} → {self.business_user})"
