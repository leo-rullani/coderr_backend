"""
Serializers for the Orders API.
"""

from rest_framework import serializers
from rest_framework.exceptions import NotFound, ValidationError

from orders_app.models import Order
from offers_app.models import OfferDetail

class StrictFloatField(serializers.FloatField):
    """
    Ensures that prices are rendered as *int* if they have no
    fractional component – this exactly matches the API‑spec JSON examples.
    """

    def to_representation(self, value):
        value = float(value) if value is not None else None
        return int(value) if value is not None and value.is_integer() else value

class OrderSerializer(serializers.ModelSerializer):
    """
    Read‑only serializer for `Order` objects.

    * `customer_user` / `business_user` are returned as plain integer IDs
      (no nested user objects).
    * `price` is sent as *int* if it is a whole number.
    """

    customer_user = serializers.PrimaryKeyRelatedField(read_only=True)
    business_user = serializers.PrimaryKeyRelatedField(read_only=True)
    price = StrictFloatField()

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
    Write‑serializer for creating a new **Order** from an **OfferDetail**.

    The official field is ``offer_detail_id``.  To stay tolerant with
    potential camelCase payloads (e.g. *offerDetailId*), we accept **both**
    spellings and normalise internally.
    """

    offer_detail_id = serializers.IntegerField(required=False, write_only=True)
    offerDetailId = serializers.IntegerField(required=False, write_only=True)

    def validate(self, attrs):
        """
        1. Accept either ``offer_detail_id`` or ``offerDetailId``.
        2. Ensure that the referenced OfferDetail actually exists.
        3. Ensure that the requesting user has role **customer**.
        """
        raw_id = attrs.get("offer_detail_id") or attrs.get("offerDetailId")
        if raw_id is None:
            raise ValidationError({"offer_detail_id": "This field is required."})

        # normalise key name for downstream code
        attrs["offer_detail_id"] = raw_id
        attrs.pop("offerDetailId", None)

        try:
            self._detail = OfferDetail.objects.select_related("offer").get(id=raw_id)
        except OfferDetail.DoesNotExist:
            raise NotFound("OfferDetail not found.")

        user = self.context["request"].user
        if getattr(user, "role", None) != "customer":
            raise ValidationError("Only customers can create orders.")

        return attrs

    def create(self, validated_data):
        """
        Instantiate a new *Order* based on the validated OfferDetail.
        """
        user = self.context["request"].user
        detail = self._detail            # cached in *validate()*
        offer = detail.offer

        return Order.objects.create(
            customer_user=user,
            business_user=offer.user,
            title=detail.title,
            revisions=detail.revisions,
            delivery_time_in_days=detail.delivery_time_in_days,
            price=detail.price,
            features=detail.features,
            offer_type=detail.offer_type,
            status="in_progress",
        )
class OrderStatusUpdateSerializer(serializers.ModelSerializer):
    """
    Allows business users to update **only** the ``status`` field.
    """

    class Meta:
        model = Order
        fields = ["status"]

    def validate_status(self, value):
        allowed = {"in_progress", "completed", "cancelled"}
        if value not in allowed:
            raise ValidationError(f"Status must be one of {sorted(allowed)}.")
        return value