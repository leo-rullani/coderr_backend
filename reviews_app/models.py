from django.db import models
from django.contrib.auth import get_user_model

User = get_user_model()

class Review(models.Model):
    """
    Model for reviews. Each review links a reviewer (user) to a business_user (user).
    """
    business_user = models.ForeignKey(
        User, 
        on_delete=models.CASCADE, 
        related_name="business_reviews",
        help_text="The business (user) that is being reviewed."
    )
    reviewer = models.ForeignKey(
        User, 
        on_delete=models.CASCADE, 
        related_name="user_reviews",
        help_text="The user who created the review."
    )
    rating = models.PositiveSmallIntegerField()
    description = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["-updated_at"]

    def __str__(self):
        return f"Review {self.id} by {self.reviewer} for {self.business_user} ({self.rating})"