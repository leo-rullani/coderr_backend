"""
Serializers for Offers & OfferDetails.

Covered use‑cases
-----------------
* OfferCreateSerializer             – POST  /api/offers/        (≥ 3 detail tiers)
* OfferDetailSerializer             – GET / PATCH single offer  (business dashboard)
* OfferListSerializer               – GET  /api/offers/         (public list, cards)
* OfferPublicSerializer             – GET  /api/offers/?creator_id=… (reduced list)
* OfferDetailPublicSerializer       – GET  /api/offerdetails/<id>/   (public)

Helper classes
--------------
* StrictCharField   – only real strings are accepted (no ints / lists)
* StrictFloatField  – renders whole numbers as ``int`` instead of ``float``
"""

from django.contrib.auth import get_user_model
from rest_framework import serializers

from offers_app.models import Offer, OfferDetail

User = get_user_model()

def clean_detail_data(detail: dict) -> dict:
    """Remove non‑model keys before creating an OfferDetail instance."""
    forbidden = {"user", "url"}
    return {k: v for k, v in detail.items() if k not in forbidden}


class StrictCharField(serializers.CharField):
    """CharField that **only** accepts strings (no numbers, lists, …)."""

    def to_internal_value(self, data):
        if not isinstance(data, str):
            raise serializers.ValidationError("Must be a string.")
        return super().to_internal_value(data)


class StrictFloatField(serializers.FloatField):
    """
    On output, return *int* if the value is a whole number.
    This exactly matches the examples in the API spec.
    """

    def to_representation(self, value):
        if value is None:
            return None
        return int(value) if float(value).is_integer() else float(value)
class UserDetailsSerializer(serializers.ModelSerializer):
    """Tiny subset of user data for offer list cards."""

    class Meta:
        model = User
        fields = ["first_name", "last_name", "username"]
class OfferDetailShortSerializer(serializers.ModelSerializer):
    """Only *id* + *URL* for list‑views."""
    url = serializers.SerializerMethodField()

    class Meta:
        model = OfferDetail
        fields = ["id", "url"]

    def get_url(self, obj):
        return f"/offerdetails/{obj.id}/"


class OfferDetailFullSerializer(serializers.ModelSerializer):
    """Complete detail representation incl. clean price field."""
    price = StrictFloatField()

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


class OfferDetailWriteSerializer(serializers.ModelSerializer):
    """Write‑serializer for nested validation (POST / PATCH)."""

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
            raise serializers.ValidationError(
                f"Missing fields: {', '.join(missing)}"
            )
        return data

class OfferCreateSerializer(serializers.ModelSerializer):
    """Serializer for creating an offer with **≥ 3** detail tiers."""
    details = OfferDetailWriteSerializer(many=True, write_only=True)

    class Meta:
        model = Offer
        fields = ["id", "title", "image", "description", "details"]

    def validate_details(self, value):
        if len(value) < 3:
            raise serializers.ValidationError(
                "At least 3 offer details are required."
            )
        return value

    def create(self, validated_data):
        details_data = validated_data.pop("details")
        offer = Offer.objects.create(
            user=self.context["request"].user, **validated_data
        )

        prices, delivery_times = [], []
        for detail in details_data:
            od = OfferDetail.objects.create(
                offer=offer, **clean_detail_data(detail)
            )
            prices.append(od.price)
            delivery_times.append(od.delivery_time_in_days)

        offer.min_price = min(prices)
        offer.min_delivery_time = min(delivery_times)
        offer.save(update_fields=["min_price", "min_delivery_time"])
        return offer

    def to_representation(self, instance):
        rep = super().to_representation(instance)
        rep["details"] = OfferDetailFullSerializer(
            instance.details.all(), many=True
        ).data
        rep["min_price"] = StrictFloatField().to_representation(instance.min_price)
        rep["min_delivery_time"] = instance.min_delivery_time
        return rep
class OfferDetailSerializer(serializers.ModelSerializer):
    """Full offer incl. nested PATCH logic (business owner view)."""

    title = StrictCharField()
    details = OfferDetailWriteSerializer(many=True)
    user_details = UserDetailsSerializer(source="user", read_only=True)
    min_price = StrictFloatField(read_only=True)

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
            "min_price",
            "min_delivery_time",
            "user_details",
        ]

    def update(self, instance, validated_data):
        details_data = validated_data.pop("details", None)

        # scalar fields
        for attr, val in validated_data.items():
            setattr(instance, attr, val)
        instance.save()

        # create / update details
        if details_data is not None:
            existing = {d.id: d for d in instance.details.all()}
            for detail in details_data:
                detail_id = detail.get("id")
                if detail_id and detail_id in existing:
                    obj = existing[detail_id]
                    for k, v in detail.items():
                        if k != "id":
                            setattr(obj, k, v)
                    obj.save()
                else:
                    OfferDetail.objects.create(
                        offer=instance, **clean_detail_data(detail)
                    )

        # recalc aggregates
        qs = instance.details.values_list("price", "delivery_time_in_days")
        if qs:
            prices, dts = zip(*qs)
            instance.min_price = min(prices)
            instance.min_delivery_time = min(dts)
            instance.save(update_fields=["min_price", "min_delivery_time"])

        return instance

    def to_representation(self, instance):
        rep = super().to_representation(instance)
        rep["details"] = OfferDetailFullSerializer(
            instance.details.all(), many=True
        ).data
        rep["min_price"] = StrictFloatField().to_representation(instance.min_price)
        return rep
class OfferListSerializer(serializers.ModelSerializer):
    """List endpoint used by the card grid in the front‑end."""
    details = serializers.SerializerMethodField()
    user_details = UserDetailsSerializer(source="user", read_only=True)
    min_price = StrictFloatField(read_only=True)
    createdAt = serializers.DateTimeField(source="created_at", read_only=True)
    updatedAt = serializers.DateTimeField(source="updated_at", read_only=True)

    class Meta:
        model = Offer
        fields = [
            "id",
            "user",
            "title",
            "image",
            "description",
            "created_at",     # original snake_case
            "updated_at",
            "createdAt",      # camelCase alias
            "updatedAt",
            "details",
            "min_price",
            "min_delivery_time",
            "user_details",
        ]

    def get_details(self, obj):
        return OfferDetailShortSerializer(
            obj.details.filter(id__isnull=False), many=True
        ).data

class OfferDetailPublicSerializer(serializers.ModelSerializer):
    price = StrictFloatField()

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


class OfferPublicSerializer(serializers.ModelSerializer):
    """Reduced list serializer for search views."""
    details = OfferDetailPublicSerializer(many=True, read_only=True)
    min_price = StrictFloatField(read_only=True)

    class Meta:
        model = Offer
        fields = [
            "id",
            "title",
            "image",
            "description",
            "min_price",
            "min_delivery_time",
            "details",
        ]