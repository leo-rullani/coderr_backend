from rest_framework import generics, filters, permissions, serializers
from rest_framework.permissions import IsAuthenticated
from django_filters.rest_framework import DjangoFilterBackend
from offers_app.models import Offer, OfferDetail
from offers_app.api.serializers import (
    OfferListSerializer,
    OfferDetailSerializer,
    OfferDetailCreateSerializer,  # Wichtig: Importiere diesen Serializer!
)
from offers_app.api.filters import OfferFilter

class IsBusinessUser(permissions.BasePermission):
    """
    Allows access only to users with role 'business'.
    """
    def has_permission(self, request, view):
        return request.user.is_authenticated and getattr(request.user, "role", None) == "business"

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
        extra_kwargs = {
            'user': {'read_only': True},
        }

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
        validated_data.pop('user', None)  # Remove user if present (safety)
        user = self.context['request'].user
        offer = Offer.objects.create(user=user, **validated_data)
        for detail_data in details_data:
            OfferDetail.objects.create(offer=offer, **detail_data)
        return offer

class OfferListCreateAPIView(generics.ListCreateAPIView):
    """
    API endpoint for listing offers (GET) and creating new offers (POST).
    - GET: Public, paginated list with only id and url in details.
    - POST: Only authenticated business users can create offers with at least 3 details.
    """
    queryset = Offer.objects.all().select_related('user')
    filter_backends = [
        DjangoFilterBackend,
        filters.SearchFilter,
        filters.OrderingFilter,
    ]
    filterset_class = OfferFilter
    search_fields = ['title', 'description']
    ordering_fields = ['updated_at', 'min_price']
    ordering = ['-updated_at']

    def get_permissions(self):
        """
        Sets permissions for GET (public) and POST (business only).
        """
        if self.request.method == "POST":
            return [IsAuthenticated(), IsBusinessUser()]
        return [permissions.AllowAny()]

    def get_serializer_class(self):
        """
        Chooses serializer based on request method.
        """
        if self.request.method == "POST":
            return OfferCreateSerializer
        return OfferListSerializer

    def perform_create(self, serializer):
        """
        Sets the current user as the creator for the new offer.
        """
        serializer.save(user=self.request.user)

class OfferDetailAPIView(generics.RetrieveAPIView):
    """
    API endpoint that returns a single offer by id,
    with all nested detail fields, as required by the API doc.
    """
    queryset = Offer.objects.all().select_related('user')
    serializer_class = OfferDetailSerializer
    permission_classes = [permissions.AllowAny]