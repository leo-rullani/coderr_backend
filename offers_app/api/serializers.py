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

class OfferDetailSerializer(serializers.ModelSerializer):
    """
    Serializes details for an offer, only id and url.
    """
    class Meta:
        model = OfferDetail
        fields = ['id', 'url']

class OfferSerializer(serializers.ModelSerializer):
    """
    Serializes offer information for the offer list endpoint.
    """
    details = OfferDetailSerializer(many=True, read_only=True)
    user_details = UserDetailsSerializer(
        source='user', read_only=True
    )

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