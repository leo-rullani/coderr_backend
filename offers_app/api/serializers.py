from rest_framework import serializers
from offers_app.models import Offer, OfferDetail
from django.contrib.auth import get_user_model

User = get_user_model()


# --------------------------------------------------------------------------- #
# helpers
# --------------------------------------------------------------------------- #
def clean_detail_data(detail):
    """Remove non‑model keys before creating an OfferDetail."""
    forbidden_keys = ["user", "url"]
    return {k: v for k, v in detail.items() if k not in forbidden_keys}


# --------------------------------------------------------------------------- #
# small reusable serializers
# --------------------------------------------------------------------------- #
class UserDetailsSerializer(serializers.ModelSerializer):
    """Basic user info for offer listing."""
    class Meta:
        model = User
        fields = ["first_name", "last_name", "username"]


class OfferDetailShortSerializer(serializers.ModelSerializer):
    """Only id + URL for the offer list view."""
    url = serializers.SerializerMethodField()

    class Meta:
        model = OfferDetail
        fields = ["id", "url"]

    def get_url(self, obj):
        return f"/offerdetails/{obj.id}/"


class OfferDetailFullSerializer(serializers.ModelSerializer):
    """
    Full detail for POST and detail view.
    Return price as ``int`` when there are no decimals.
    """
    price = serializers.SerializerMethodField()

    class Meta:
        model = OfferDetail
        fields = [
            "id",
            "title",
            "revisions",
            "delivery_time_in_days",
            "price",
            "features",
            "offer_type",
        ]

    def get_price(self, obj):
        if obj.price is None:
            return None
        return int(obj.price) if obj.price % 1 == 0 else float(obj.price)


class OfferDetailWriteSerializer(serializers.ModelSerializer):
    """Write‑serializer for nested details (validation only)."""

    class Meta:
        model = OfferDetail
        exclude = ["offer", "id"]

    def validate(self, data):
        required = [
            "title",
            "revisions",
            "delivery_time_in_days",
            "price",
            "features",
            "offer_type",
        ]
        missing = [f for f in required if data.get(f) in [None, ""]]
        if missing:
            raise serializers.ValidationError(f"Missing fields: {', '.join(missing)}")
        return data


class StrictCharField(serializers.CharField):
    """CharField that accepts only real strings."""

    def to_internal_value(self, data):
        if not isinstance(data, str):
            raise serializers.ValidationError("Must be a string.")
        return super().to_internal_value(data)


# --------------------------------------------------------------------------- #
# create / update serializers
# --------------------------------------------------------------------------- #
class OfferCreateSerializer(serializers.ModelSerializer):
    """
    Create serializer for an Offer with ≥ 3 details.
    Response returns full details incl. ID.
    """
    details = OfferDetailWriteSerializer(many=True, write_only=True)

    class Meta:
        model = Offer
        fields = ["id", "title", "image", "description", "details"]

    def validate_details(self, value):
        if len(value) < 3:
            raise serializers.ValidationError("At least 3 offer details are required.")
        return value

    def create(self, validated_data):
        details_data = validated_data.pop("details")
        offer = Offer.objects.create(
            user=self.context["request"].user, **validated_data
        )

        # collect aggregates while creating details
        prices, delivery_times = [], []
        for d in details_data:
            od = OfferDetail.objects.create(offer=offer, **clean_detail_data(d))
            prices.append(od.price)
            delivery_times.append(od.delivery_time_in_days)

        # --- aggregate update ------------------------------------------------
        offer.min_price = min(prices) if prices else None
        offer.min_delivery_time = min(delivery_times) if delivery_times else None
        offer.save(update_fields=["min_price", "min_delivery_time"])
        # --------------------------------------------------------------------

        return offer

    # representation incl. IDs
    def to_representation(self, instance):
        rep = super().to_representation(instance)
        rep["details"] = OfferDetailFullSerializer(
            instance.details.all(), many=True
        ).data
        return rep


class OfferDetailSerializer(serializers.ModelSerializer):
    """
    Detail serializer for a full Offer (incl. nested PATCH logic).
    """
    title = StrictCharField()
    details = OfferDetailWriteSerializer(many=True)
    user_details = UserDetailsSerializer(source="user", read_only=True)
    min_price_annotated = serializers.FloatField(source="min_price", read_only=True)

    class Meta:
        model = Offer
        fields = [
            "id",
            "user",
            "title",
            "image",
            "description",
            "created_at",
            "updated_at",
            "details",
            "min_price_annotated",
            "min_delivery_time",
            "user_details",
        ]

    def update(self, instance, validated_data):
        """Partial‑update the offer and its nested details."""
        details_data = validated_data.pop("details", None)

        # update scalar fields
        for attr, value in validated_data.items():
            setattr(instance, attr, value)
        instance.save()

        # update / create details
        if details_data is not None:
            existing = {d.id: d for d in instance.details.all()}
            for detail in details_data:
                detail_id = detail.get("id")
                if detail_id and detail_id in existing:
                    obj = existing[detail_id]
                    for key, val in detail.items():
                        if key != "id":
                            setattr(obj, key, val)
                    obj.save()
                elif not detail_id:
                    OfferDetail.objects.create(
                        offer=instance, **clean_detail_data(detail)
                    )

        # --- aggregate update ------------------------------------------------
        values = instance.details.values_list("price", "delivery_time_in_days")
        prices, times = zip(*values) if values else ([], [])
        instance.min_price = min(prices) if prices else None
        instance.min_delivery_time = min(times) if times else None
        instance.save(update_fields=["min_price", "min_delivery_time"])
        # --------------------------------------------------------------------

        return instance

class OfferListSerializer(serializers.ModelSerializer):
    """Offer list endpoint including min price & delivery aggregates."""
    details = serializers.SerializerMethodField()
    user_details = UserDetailsSerializer(source="user", read_only=True)
    min_price_annotated = serializers.FloatField(read_only=True)

    class Meta:
        model = Offer
        fields = [
            "id",
            "user",
            "title",
            "image",
            "description",
            "created_at",
            "updated_at",
            "details",
            "min_price_annotated",
            "min_delivery_time",
            "user_details",
        ]

    def get_details(self, obj):
        valid_details = obj.details.filter(id__isnull=False)
        return OfferDetailShortSerializer(valid_details, many=True).data


class OfferDetailPublicSerializer(serializers.ModelSerializer):
    """Public view of a single OfferDetail."""
    price = serializers.SerializerMethodField()

    class Meta:
        model = OfferDetail
        fields = [
            "id",
            "title",
            "revisions",
            "delivery_time_in_days",
            "price",
            "features",
            "offer_type",
        ]

    def get_price(self, obj):
        if obj.price is None:
            return None
        return int(obj.price) if obj.price % 1 == 0 else float(obj.price)


class OfferPublicSerializer(serializers.ModelSerializer):
    """Public list serializer for offers (only valid details)."""
    details = OfferDetailPublicSerializer(many=True, read_only=True)

    class Meta:
        model = Offer
        fields = ["id", "title", "image", "description", "details"]
