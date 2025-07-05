from rest_framework import serializers
from rest_framework.exceptions import NotFound
from orders_app.models import Order
from offers_app.models import OfferDetail

class OrderSerializer(serializers.ModelSerializer):
    """
    Serializer for Order model.
    Ensures that user fields return only integer IDs.
    Price is rendered as int if it is a whole number.
    """
    customer_user = serializers.PrimaryKeyRelatedField(read_only=True)
    business_user = serializers.PrimaryKeyRelatedField(read_only=True)
    price = serializers.FloatField()

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

    def to_representation(self, instance):
        """
        Ensures price is rendered as int if it is a whole number.
        """
        data = super().to_representation(instance)
        if data.get("price") is not None:
            try:
                float_price = float(data["price"])
                if float_price.is_integer():
                    data["price"] = int(float_price)
                else:
                    data["price"] = float_price
            except Exception:
                pass
        return data

class OrderCreateSerializer(serializers.Serializer):
    """
    Serializer for creating a new Order based on OfferDetail.
    Expects { "offer_detail_id": int }.
    Only users with the 'customer' role can create orders.
    """
    offer_detail_id = serializers.IntegerField()

    def validate_offer_detail_id(self, value):
        """
        Validates that the referenced OfferDetail exists.
        """
        try:
            OfferDetail.objects.get(id=value)
        except OfferDetail.DoesNotExist:
            raise NotFound("OfferDetail not found.")
        return value

    def create(self, validated_data):
        """
        Creates an Order based on the given OfferDetail.
        """
        request = self.context['request']
        user = request.user

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

class OrderStatusUpdateSerializer(serializers.ModelSerializer):
    """
    Serializer for updating only the status of an order via PATCH.
    Allows only 'in_progress', 'completed', or 'cancelled' as status.
    """
    class Meta:
        model = Order
        fields = ["status"]

    def validate_status(self, value):
        """
        Validates that the status is one of the allowed values.
        """
        allowed = ["in_progress", "completed", "cancelled"]
        if value not in allowed:
            raise serializers.ValidationError(f"Status must be one of {allowed}.")
        return value