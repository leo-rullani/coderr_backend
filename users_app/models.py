"""
Extended profile model shared by customer‑ and business‑accounts.
"""

from django.db import models
from auth_app.models import CustomUser


class UserProfile(models.Model):
    """Single row per user, created on demand."""
    user = models.OneToOneField(CustomUser, on_delete=models.CASCADE)
    is_customer = models.BooleanField(default=False)

    file = models.ImageField(upload_to="profile_pics/", null=True, blank=True)
    uploaded_at = models.DateTimeField(auto_now_add=True, null=True, blank=True)

    first_name = models.CharField(max_length=50, blank=True, default="")
    last_name = models.CharField(max_length=50, blank=True, default="")
    location = models.CharField(max_length=100, blank=True, default="")
    tel = models.CharField(max_length=30, blank=True, default="")
    description = models.TextField(blank=True, default="")
    working_hours = models.CharField(max_length=100, blank=True, default="")

    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self) -> str:  # pragma: no cover
        return f"{self.user.username} Profile"