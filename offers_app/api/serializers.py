from rest_framework import serializers
from offers_app.models import Offer, OfferDetail
from django.contrib.auth import get_user_model

User = get_user_model()

def clean_detail_data(detail):
    """
    Removes all non-model fields before creating OfferDetail.
    """
    forbidden_keys = ['user', 'url']
    return {k: v for k, v in detail.items() if k not in forbidden_keys}

class UserDetailsSerializer(serializers.ModelSerializer):
    """
    Serializes basic user information for offer listing.
    """
    class Meta:
        model = User
        fields = ['first_name', 'last_name', 'username']

class OfferDetailShortSerializer(serializers.ModelSerializer):
    """
    Serializes id and url for offer details (used in offer list endpoint).
    """
    url = serializers.SerializerMethodField()

    class Meta:
        model = OfferDetail
        fields = ['id', 'url']

    def get_url(self, obj):
        return f"/offerdetails/{obj.id}/"
    
class OfferDetailFullSerializer(serializers.ModelSerializer):
    """
    Serializes all required fields for offer details (used in offer detail endpoint and creation).
    """
    price = serializers.FloatField()

    class Meta:
        model = OfferDetail
        fields = [
            'id', 'title', 'revisions', 'delivery_time_in_days', 'price',
            'features', 'offer_type',
        ]

    def get_url(self, obj):
        request = self.context.get('request')
        relative_url = obj.get_absolute_url()
        if request is not None:
            return request.build_absolute_uri(relative_url)
        return relative_url

class OfferDetailWriteSerializer(serializers.ModelSerializer):
    """
    Serializer for writing/updating offer details.
    Ensures all required fields are present.
    """
    class Meta:
        model = OfferDetail
        exclude = ['offer', 'id']

    def validate(self, data):
        required = ['title', 'revisions', 'delivery_time_in_days', 'price', 'features', 'offer_type']
        missing = [f for f in required if data.get(f) in [None, ""]]
        if missing:
            raise serializers.ValidationError(f"Missing fields: {', '.join(missing)}")
        return data

class StrictCharField(serializers.CharField):
    """
    CharField that only allows strings.
    """
    def to_internal_value(self, data):
        if not isinstance(data, str):
            raise serializers.ValidationError("Must be a string.")
        return super().to_internal_value(data)

class OfferCreateSerializer(serializers.ModelSerializer):
    """
    Serializer for creating offers with nested offer details.
    Enforces at least 3 details per offer (POST only).
    """
    details = OfferDetailWriteSerializer(many=True)

    class Meta:
        model = Offer
        fields = ['id', 'title', 'image', 'description', 'details']

    def validate_details(self, value):
        if len(value) < 3:
            raise serializers.ValidationError("At least 3 offer details are required.")
        return value

    def create(self, validated_data):
        details_data = validated_data.pop('details')
        user = self.context['request'].user
        offer = Offer.objects.create(user=user, **validated_data)
        for detail_data in details_data:
            OfferDetail.objects.create(offer=offer, **clean_detail_data(detail_data))
        return offer

class OfferDetailSerializer(serializers.ModelSerializer):
    """
    Serializes a single offer for the detail endpoint.
    PATCH/PUT nested details with validation.
    """
    title = StrictCharField()
    details = OfferDetailWriteSerializer(many=True)
    user_details = UserDetailsSerializer(source='user', read_only=True)
    min_price_annotated = serializers.FloatField(source='min_price', read_only=True)

    class Meta:
        model = Offer
        fields = [
            'id', 'user', 'title', 'image', 'description', 'created_at',
            'updated_at', 'details', 'min_price_annotated', 'min_delivery_time', 'user_details',
        ]

    def update(self, instance, validated_data):
        """
        Updates offer and its details (nested, PATCH logic).
        Only specified fields are updated (PATCH logic).
        """
        details_data = validated_data.pop('details', None)
        for attr, value in validated_data.items():
            setattr(instance, attr, value)
        instance.save()
        if details_data is not None:
            existing = {d.id: d for d in instance.details.all()}
            for detail in details_data:
                detail_id = detail.get('id')
                if detail_id and detail_id in existing:
                    d = existing[detail_id]
                    for key, val in detail.items():
                        if key != 'id':
                            setattr(d, key, val)
                    d.save()
                elif not detail_id:
                    OfferDetail.objects.create(offer=instance, **clean_detail_data(detail))
        return instance

class OfferListSerializer(serializers.ModelSerializer):
    """
    Serializes offers for the list endpoint.
    Includes only id and url for offer details.
    Only returns details with valid IDs.
    """
    details = serializers.SerializerMethodField()
    user_details = UserDetailsSerializer(source='user', read_only=True)
    min_price_annotated = serializers.FloatField(read_only=True)

    class Meta:
        model = Offer
        fields = [
            'id', 'user', 'title', 'image', 'description', 'created_at',
            'updated_at', 'details', 'min_price_annotated', 'min_delivery_time', 'user_details',
        ]

    def get_details(self, obj):
        valid_details = obj.details.filter(id__isnull=False)
        return OfferDetailShortSerializer(valid_details, many=True).data


class OfferDetailPublicSerializer(serializers.ModelSerializer):
    """
    Serializes all fields for offer details for public view.
    """
    price = serializers.FloatField()

    class Meta:
        model = OfferDetail
        fields = [
            'id', 'title', 'revisions', 'delivery_time_in_days', 'price',
            'features', 'offer_type',
        ]

class OfferPublicSerializer(serializers.ModelSerializer):
    """
    Serializes offers for public listing, including only valid offer details.
    """
    details = OfferDetailPublicSerializer(many=True, read_only=True)

    class Meta:
        model = Offer
        fields = [
            'id', 'title', 'image', 'description', 'details',
        ]