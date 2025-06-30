from rest_framework import serializers
from rest_framework.exceptions import NotFound
from orders_app.models import Order
from offers_app.models import OfferDetail

class OrderSerializer(serializers.ModelSerializer):
    """
    Serializes all fields of an Order for listing and detail endpoints.
    """
    class Meta:
        model = Order
        fields = [
            "id",
            "customer_user",
            "business_user",
            "title",
            "revisions",
            "delivery_time_in_days",
            "price",
            "features",
            "offer_type",
            "status",
            "created_at",
            "updated_at",
        ]

class OrderCreateSerializer(serializers.Serializer):
    """
    Serializer for creating a new order based on an OfferDetail.

    Fields:
        offer_detail_id (int): The ID of the OfferDetail used to create the order.

    Raises:
        NotFound: If the given OfferDetail ID does not exist (404).
        ValidationError: If user is not customer or if other validation fails (400).
    """
    offer_detail_id = serializers.IntegerField()

    def validate_offer_detail_id(self, value):
        """
        Validates that the OfferDetail with the given ID exists.

        Args:
            value (int): The ID of the OfferDetail.

        Returns:
            int: The validated OfferDetail ID.

        Raises:
            NotFound: If the OfferDetail does not exist (404).
        """
        try:
            offer_detail = OfferDetail.objects.get(id=value)
        except OfferDetail.DoesNotExist:
            raise NotFound("OfferDetail not found.")  # <-- Gibt 404 zurück!
        return value
    
    def create(self, validated_data):
        """
        Creates a new order using the given OfferDetail.

        Args:
            validated_data (dict): The validated data from the request.

        Returns:
            Order: The newly created order instance.

        Raises:
            ValidationError: If the user is not a customer (400).
        """
        request = self.context['request']
        user = request.user

        # Nur Kunden dürfen Bestellungen erstellen!
        if getattr(user, "role", None) != "customer":
            raise serializers.ValidationError("Only customers can create orders.")

        offer_detail = OfferDetail.objects.get(id=validated_data["offer_detail_id"])
        offer = offer_detail.offer

        return Order.objects.create(
            customer_user=user,
            business_user=offer.user,
            title=offer_detail.title,
            revisions=offer_detail.revisions,
            delivery_time_in_days=offer_detail.delivery_time_in_days,
            price=offer_detail.price,
            features=offer_detail.features,
            offer_type=offer_detail.offer_type,
            status="in_progress",
        )