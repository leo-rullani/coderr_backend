from django.db import models
from django.contrib.auth import get_user_model

User = get_user_model()

class Offer(models.Model):
    """
    Model for storing offer data.
    """
    user = models.ForeignKey(
        User, on_delete=models.CASCADE, related_name="offers"
    )
    title = models.CharField(max_length=200)
    image = models.ImageField(
        upload_to="offer_images/", null=True, blank=True
    )
    description = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    min_price = models.DecimalField(
        max_digits=10, decimal_places=2
    )
    min_delivery_time = models.PositiveIntegerField()

    def __str__(self):
        """
        Returns string representation of the offer.
        """
        return f"{self.title} (by {self.user})"

class OfferDetail(models.Model):
    """
    Model for storing details related to an offer.
    """
    offer = models.ForeignKey(
        Offer, on_delete=models.CASCADE, related_name="details"
    )
    url = models.CharField(max_length=255)

    def __str__(self):
        """
        Returns string representation of the offer detail.
        """
        return f"Detail {self.id} for Offer {self.offer_id}"