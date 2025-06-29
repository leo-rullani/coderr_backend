from django.db import models
from auth_app.models import CustomUser

class UserProfile(models.Model):
    """
    Extended profile model for both customers and business users.
    """
    user = models.OneToOneField(CustomUser, on_delete=models.CASCADE)
    file = models.ImageField(upload_to='profile_pics/', null=True, blank=True)
    uploaded_at = models.DateTimeField(auto_now_add=True, null=True, blank=True) 
    first_name = models.CharField(max_length=50, blank=True, default="")
    last_name = models.CharField(max_length=50, blank=True, default="")
    location = models.CharField(max_length=100, blank=True, default="")
    tel = models.CharField(max_length=30, blank=True, default="")
    description = models.TextField(blank=True, default="")
    working_hours = models.CharField(max_length=100, blank=True, default="")
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.user.username} Profile"