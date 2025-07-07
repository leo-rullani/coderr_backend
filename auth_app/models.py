from django.contrib.auth.models import AbstractUser, BaseUserManager
from django.db import models
from django.utils.translation import gettext_lazy as _


class CustomUserManager(BaseUserManager):
    """User‑Manager, der sowohl normale User als auch Super‑User erstellt."""

    use_in_migrations = True  # erleichtert zukünftige Migrationen

    def create_user(self, username, email=None, password=None, **extra):
        if not username:
            raise ValueError("The username is required")
        email = self.normalize_email(email)
        extra.setdefault("role", CustomUser.Roles.CUSTOMER)  # Fallback
        user = self.model(username=username, email=email, **extra)
        user.set_password(password)
        user.save(using=self._db)
        return user

    def create_superuser(self, username, email=None, password=None, **extra):
        # Ohne diese Defaults scheitert `createsuperuser`
        extra.setdefault("role", CustomUser.Roles.BUSINESS)
        extra.setdefault("is_staff", True)
        extra.setdefault("is_superuser", True)

        if extra.get("is_staff") is not True:
            raise ValueError("Superuser must have is_staff=True.")
        if extra.get("is_superuser") is not True:
            raise ValueError("Superuser must have is_superuser=True.")

        return self.create_user(username, email, password, **extra)


class CustomUser(AbstractUser):
    """Erweitertes User‑Modell mit Rollenfeld."""

    class Roles(models.TextChoices):
        CUSTOMER = "customer", _("Customer")
        BUSINESS = "business", _("Business")

    role = models.CharField(
        max_length=20,
        choices=Roles.choices,
        default=Roles.CUSTOMER,
    )

    # Unser eigener Manager
    objects = CustomUserManager()

    def __str__(self):
        return f"{self.username} ({self.role})"