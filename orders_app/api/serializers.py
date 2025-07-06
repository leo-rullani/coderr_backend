"""
Serializers for the Orders API.
"""

from rest_framework import serializers
from rest_framework.exceptions import NotFound, ValidationError, PermissionDenied  # ← neu

from orders_app.models import Order
from offers_app.models import OfferDetail


class StrictFloatField(serializers.FloatField):
    """
    Renders *price* as **int** if no fractional component is present.
    """

    def to_representation(self, value):
        value = float(value) if value is not None else None
        return int(value) if value is not None and value.is_integer() else value

class OrderSerializer(serializers.ModelSerializer):
    """
    Read‑only representation of an `Order`.

    * `customer_user` / `business_user` are delivered as plain integer IDs.
    * `price` is serialised via `StrictFloatField`.
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
    Create a new **Order** based on an existing **OfferDetail**.

    Accepts both `offer_detail_id` (snake_case) and `offerDetailId`
    (camelCase) for tolerance.
    """

    offer_detail_id = serializers.IntegerField(required=False, write_only=True)
    offerDetailId = serializers.IntegerField(required=False, write_only=True)

    def validate(self, attrs):
        """
        1. Extract the ID from either field.
        2. Ensure the OfferDetail exists.
        3. Ensure the requesting user has role **customer**.
        """
        raw_id = attrs.get("offer_detail_id") or attrs.get("offerDetailId")
        if raw_id is None:
            raise ValidationError({"offer_detail_id": "This field is required."})

        # normalise key
        attrs["offer_detail_id"] = raw_id
        attrs.pop("offerDetailId", None)

        try:
            self._detail = OfferDetail.objects.select_related("offer").get(id=raw_id)
        except OfferDetail.DoesNotExist:
            raise NotFound("OfferDetail not found.")

        user = self.context["request"].user
        if getattr(user, "role", None) != "customer":
            # ← neu: 403 statt 400
            raise PermissionDenied("Only customers can create orders.")

        return attrs

    def create(self, validated_data):
        """
        Build the Order from the validated OfferDetail.
        """
        user = self.context["request"].user
        detail = self._detail            # cached during validate()
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
    Allows the *business user* to update **only** the `status` field.
    """

    class Meta:
        model = Order
        fields = ["status"]

    def validate_status(self, value):
        allowed = {"in_progress", "completed", "cancelled"}
        if value not in allowed:
            raise ValidationError(f"Status must be one of {sorted(allowed)}.")
        return value