"""
Serializers for Offer and OfferDetail objects.

Covered use‑cases
-----------------
* OfferCreateSerializer             – POST  /api/offers/        (≥ 3 detail tiers)
* OfferDetailSerializer             – GET / PATCH single offer  (business dashboard)
* OfferListSerializer               – GET  /api/offers/         (public list, cards)
* OfferPublicSerializer             – GET  /api/offers/?creator_id=… (reduced list)
* OfferDetailPublicSerializer       – GET  /api/offerdetails/<id>/   (public)

Utility
-------
* StrictCharField   – refuses non‑string input
* StrictFloatField  – renders whole numbers as ``int`` instead of ``float``
"""

from django.contrib.auth import get_user_model
from rest_framework import serializers

from offers_app.models import Offer, OfferDetail

User = get_user_model()


# --------------------------------------------------------------------------- #
#  helpers                                                                    #
# --------------------------------------------------------------------------- #
def clean_detail_data(detail: dict) -> dict:
    """Strip non‑model keys before persisting an OfferDetail."""
    forbidden = {"user", "url"}
    return {k: v for k, v in detail.items() if k not in forbidden}


class StrictCharField(serializers.CharField):
    """CharField that accepts **only** genuine strings."""

    def to_internal_value(self, data):
        if not isinstance(data, str):
            raise serializers.ValidationError("Must be a string.")
        return super().to_internal_value(data)


class StrictFloatField(serializers.FloatField):
    """
    Cast whole numbers to ``int`` so the JSON output matches the spec
    (e.g. *100* instead of *100.0*).
    """

    def to_representation(self, value):
        if value is None:
            return None
        return int(value) if float(value).is_integer() else float(value)


# --------------------------------------------------------------------------- #
#  nested user chip                                                           #
# --------------------------------------------------------------------------- #
class UserDetailsSerializer(serializers.ModelSerializer):
    """Minimal user info for offer list cards."""

    class Meta:
        model = User
        fields = ["first_name", "last_name", "username"]


# --------------------------------------------------------------------------- #
#  detail (read)                                                              #
# --------------------------------------------------------------------------- #
class OfferDetailShortSerializer(serializers.ModelSerializer):
    """Only *id* + hypermedia URL (list view)."""
    url = serializers.SerializerMethodField()

    class Meta:
        model = OfferDetail
        fields = ["id", "url"]

    def get_url(self, obj):
        return f"/offerdetails/{obj.id}/"


class OfferDetailFullSerializer(serializers.ModelSerializer):
    """Complete detail representation with clean price field."""
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


# --------------------------------------------------------------------------- #
#  detail (write)                                                             #
# --------------------------------------------------------------------------- #
# offers_app/api/serializers.py
class OfferDetailWriteSerializer(serializers.ModelSerializer):
    """Write serializer for nested detail input (POST / PATCH)."""

    id = serializers.IntegerField(required=False)      # ←  id zulassen

    class Meta:
        model   = OfferDetail
        exclude = ["offer"]                            # ←  id NICHT mehr ausschließen

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


# --------------------------------------------------------------------------- #
#  offer – CREATE                                                             #
# --------------------------------------------------------------------------- #
class OfferCreateSerializer(serializers.ModelSerializer):
    """Serializer for creating an offer with **≥ 3** detail tiers."""
    details = OfferDetailWriteSerializer(many=True, write_only=True)

    class Meta:
        model = Offer
        fields = ["id", "title", "image", "description", "details"]

    # ---------- validation --------------------------------------------------
    def validate_details(self, value):
        if len(value) < 3:
            raise serializers.ValidationError(
                "At least 3 offer details are required."
            )
        return value

    # ---------- persistence -------------------------------------------------
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

    # ---------- representation --------------------------------------------
    def to_representation(self, instance):
        rep = super().to_representation(instance)
        rep["details"] = OfferDetailFullSerializer(
            instance.details.all(), many=True
        ).data
        rep["min_price"] = StrictFloatField().to_representation(instance.min_price)
        rep["min_delivery_time"] = instance.min_delivery_time
        return rep


# --------------------------------------------------------------------------- #
#  offer – DETAIL / PATCH                                                     #
# --------------------------------------------------------------------------- #
class OfferDetailSerializer(serializers.ModelSerializer):
    """
    Full offer representation used for owner views (GET / PATCH / DELETE).

    * ``details`` accepts nested PATCH input:
        ─ update by `id`
        ─ update by unique `offer_type` (if no `id` supplied)
        ─ create new detail if neither id nor offer_type match an existing one
    * Aggregates (min_price / min_delivery_time) are re‑calculated automatically.
    """

    title       = StrictCharField()
    details     = OfferDetailWriteSerializer(many=True)
    user_details = UserDetailsSerializer(source="user", read_only=True)
    min_price   = StrictFloatField(read_only=True)

    class Meta:
        model  = Offer
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

    # ------------------------------------------------------------------ #
    #  PATCH                                                             #
    # ------------------------------------------------------------------ #
    def update(self, instance, validated_data):
        details_data = validated_data.pop("details", None)

        # ----- scalar fields -------------------------------------------
        for attr, value in validated_data.items():
            setattr(instance, attr, value)
        instance.save()

        # ----- nested details ------------------------------------------
        if details_data is not None:
            existing_by_id   = {d.id: d for d in instance.details.all()}
            existing_by_type = {d.offer_type: d for d in instance.details.all()}

            for detail in details_data:
                incoming_id = detail.get("id")

                # ❶ update by explicit ID
                if incoming_id and incoming_id in existing_by_id:
                    obj = existing_by_id[incoming_id]
                    for k, v in detail.items():
                        if k != "id":
                            setattr(obj, k, v)
                    obj.save()
                    continue

                # ❷ update by offer_type if no ID given
                match = existing_by_type.get(detail.get("offer_type"))
                if match:
                    for k, v in detail.items():
                        if k != "id":
                            setattr(match, k, v)
                    match.save()
                    continue

                # ❸ truly new detail
                OfferDetail.objects.create(
                    offer=instance, **clean_detail_data(detail)
                )

        # ----- aggregates ----------------------------------------------
        qs = instance.details.values_list("price", "delivery_time_in_days")
        if qs:
            prices, days = zip(*qs)
            instance.min_price         = min(prices)
            instance.min_delivery_time = min(days)
            instance.save(update_fields=["min_price", "min_delivery_time"])

        return instance

    # ------------------------------------------------------------------ #
    #  output                                                            #
    # ------------------------------------------------------------------ #
    def to_representation(self, instance):
        rep = super().to_representation(instance)
        rep["details"]   = OfferDetailFullSerializer(instance.details.all(), many=True).data
        rep["min_price"] = StrictFloatField().to_representation(instance.min_price)
        return rep


# --------------------------------------------------------------------------- #
#  offer – LIST (public grid)                                                 #
# --------------------------------------------------------------------------- #
class OfferListSerializer(serializers.ModelSerializer):
    """Card list view used in the public offer grid."""
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
            "created_at",     # snake_case
            "updated_at",
            "createdAt",      # camelCase aliases
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


# --------------------------------------------------------------------------- #
#  offer & detail – public read‑only                                          #
# --------------------------------------------------------------------------- #
class OfferDetailPublicSerializer(serializers.ModelSerializer):
    """Public representation of a single detail tier."""
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
    """Reduced list serializer used by public search endpoints."""
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