from rest_framework import serializers
from offers_app.models import Offer, OfferDetail
from django.contrib.auth import get_user_model

User = get_user_model()

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
        """
        Returns the absolute URL for the offer detail object.
        """
        return f"/offerdetails/{obj.id}/"

class OfferDetailFullSerializer(serializers.ModelSerializer):
    """
    Serializes all required fields for offer details (used in offer detail endpoint and creation).
    """
    class Meta:
        model = OfferDetail
        fields = [
            'id',
            'title',
            'revisions',
            'delivery_time_in_days',
            'price',
            'features',
            'offer_type',
            'url',
        ]

class OfferListSerializer(serializers.ModelSerializer):
    """
    Serializes offers for the list endpoint.
    Includes only id and url for offer details.
    """
    details = OfferDetailShortSerializer(many=True, read_only=True)
    user_details = UserDetailsSerializer(source='user', read_only=True)

    class Meta:
        model = Offer
        fields = [
            'id',
            'user',
            'title',
            'image',
            'description',
            'created_at',
            'updated_at',
            'details',
            'min_price',
            'min_delivery_time',
            'user_details',
        ]

class OfferDetailSerializer(serializers.ModelSerializer):
    """
    Serializes a single offer for the detail endpoint.
    Includes all required fields for offer details.
    """
    details = OfferDetailFullSerializer(many=True, read_only=True)
    user_details = UserDetailsSerializer(source='user', read_only=True)

    class Meta:
        model = Offer
        fields = [
            'id',
            'user',
            'title',
            'image',
            'description',
            'created_at',
            'updated_at',
            'details',
            'min_price',
            'min_delivery_time',
            'user_details',
        ]

class OfferDetailCreateSerializer(serializers.ModelSerializer):
    """
    Serializer for creating offer details in nested POST requests.
    """
    class Meta:
        model = OfferDetail
        exclude = ['offer', 'id', 'url']  # id/url set automatically, offer via parent

class OfferCreateSerializer(serializers.ModelSerializer):
    """
    Serializer for creating offers with nested offer details.
    Enforces at least 3 details per offer.
    """
    details = OfferDetailCreateSerializer(many=True)

    class Meta:
        model = Offer
        fields = [
            'id',
            'title',
            'image',
            'description',
            'details',
        ]

    def validate_details(self, value):
        """
        Ensures that at least 3 offer details are provided.
        """
        if len(value) < 3:
            raise serializers.ValidationError(
                "At least 3 offer details are required."
            )
        return value

    def create(self, validated_data):
        """
        Creates an offer with nested offer details.
        """
        details_data = validated_data.pop('details')
        user = self.context['request'].user
        offer = Offer.objects.create(user=user, **validated_data)
        for detail_data in details_data:
            OfferDetail.objects.create(offer=offer, **detail_data)
        return offer