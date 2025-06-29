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
    url = serializers.SerializerMethodField()

    class Meta:
        model = OfferDetail
        fields = ['id', 'url']

    def get_url(self, obj):
        # Gibt die absolute URL für das OfferDetail zurück
        return f"/offerdetails/{obj.id}/"

class OfferDetailFullSerializer(serializers.ModelSerializer):
    """
    Serializes all required fields for offer details (detail endpoint).
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