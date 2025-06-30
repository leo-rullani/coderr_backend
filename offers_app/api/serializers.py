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
    url = serializers.SerializerMethodField()

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

    def get_url(self, obj):
        """
        Returns the absolute URL for the offer detail object.
        """
        request = self.context.get('request')
        # Build absolute URL (http://127.0.0.1:8000/api/offerdetails/<id>/)
        relative_url = obj.get_absolute_url()
        if request is not None:
            return request.build_absolute_uri(relative_url)
        return relative_url

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

class OfferDetailWriteSerializer(serializers.ModelSerializer):
    """
    Serializer for writing/updating offer details.
    Ensures all required fields are present.
    """
    class Meta:
        model = OfferDetail
        exclude = ['offer', 'id', 'url']

    def validate(self, data):
        """
        Validates required fields for each offer detail.
        """
        required = ['title', 'revisions', 'delivery_time_in_days', 'price', 'features', 'offer_type']
        missing = [f for f in required if data.get(f) in [None, ""]]
        if missing:
            raise serializers.ValidationError(f"Missing fields: {', '.join(missing)}")
        return data

class OfferDetailWriteSerializer(serializers.ModelSerializer):
    """
    Serializer for writing/updating offer details.
    Ensures all required fields are present.
    """
    class Meta:
        model = OfferDetail
        exclude = ['offer', 'id', 'url']

    def validate(self, data):
        """
        Validates required fields for each offer detail.
        """
        required = ['title', 'revisions', 'delivery_time_in_days', 'price', 'features', 'offer_type']
        missing = [f for f in required if data.get(f) in [None, ""]]
        if missing:
            raise serializers.ValidationError(f"Missing fields: {', '.join(missing)}")
        return data

class OfferDetailSerializer(serializers.ModelSerializer):
    """
    Serializes a single offer for the detail endpoint.
    PATCH/PUT nested details with validation.
    """
    details = OfferDetailWriteSerializer(many=True)
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

    def validate_title(self, value):
        """
        Ensures that the title is a string and not a number.
        """
        if not isinstance(value, str):
            raise serializers.ValidationError("Title must be a string.")
        return value

    def update(self, instance, validated_data):
        """
        Updates offer and its details (nested, PATCH logic).
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
                    OfferDetail.objects.create(offer=instance, **detail)
        return instance

class OfferDetailCreateSerializer(serializers.ModelSerializer):
    """
    Serializer for creating offer details in nested POST requests.
    """
    class Meta:
        model = OfferDetail
        exclude = ['offer', 'id', 'url']  # id/url set automatically, offer via parent

class StrictCharField(serializers.CharField):
    def to_internal_value(self, data):
        if not isinstance(data, str):
            raise serializers.ValidationError("Must be a string.")
        return super().to_internal_value(data)

class OfferDetailSerializer(serializers.ModelSerializer):
    """
    Serializes a single offer for the detail endpoint.
    PATCH/PUT nested details with validation.
    """
    title = StrictCharField()
    details = OfferDetailWriteSerializer(many=True)
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
    
class OfferDetailPublicSerializer(serializers.ModelSerializer):
    price = serializers.FloatField()

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
        ]

class OfferPublicSerializer(serializers.ModelSerializer):
    details = OfferDetailPublicSerializer(many=True, read_only=True)

    class Meta:
        model = Offer
        fields = [
            'id',
            'title',
            'image',
            'description',
            'details',
        ]