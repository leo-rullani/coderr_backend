from django.contrib.auth.models import AbstractUser
from django.db import models

class CustomUser(AbstractUser):
    """
    Custom user model extending Django's AbstractUser.
    Adds a 'role' field to distinguish between customer and business users.
    """

    class Roles(models.TextChoices):
        CUSTOMER = "customer", "Customer"
        BUSINESS = "business", "Business"

    role = models.CharField(
        max_length=20,
        choices=Roles.choices,
        default=Roles.CUSTOMER,
    )

    def __str__(self):
        """
        Returns a readable representation of the user with their role.
        Used in Django admin and debugging.
        """
        return f"{self.username} ({self.role})"