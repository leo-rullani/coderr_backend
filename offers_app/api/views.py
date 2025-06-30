from rest_framework import generics, filters, permissions
from rest_framework.permissions import IsAuthenticated
from django_filters.rest_framework import DjangoFilterBackend
from offers_app.models import Offer, OfferDetail
from offers_app.api.serializers import (
    OfferListSerializer,
    OfferDetailSerializer,
    OfferCreateSerializer,        
    OfferDetailFullSerializer,
    OfferPublicSerializer,
)
from offers_app.api.permissions import IsOwner
from offers_app.api.filters import OfferFilter

class IsBusinessUser(permissions.BasePermission):
    """
    Allows access only to users with role 'business'.
    """
    def has_permission(self, request, view):
        return request.user.is_authenticated and getattr(request.user, "role", None) == "business"

class OfferListCreateAPIView(generics.ListCreateAPIView):
    """
    API endpoint for listing offers (GET) and creating new offers (POST).
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
        serializer.save()

class OfferDetailAPIView(generics.RetrieveUpdateDestroyAPIView):
    """
    API endpoint for retrieving, updating, or deleting a single offer by id.
    PATCH/PUT and DELETE are only allowed by the owner.
    DELETE returns 204 No Content on success.
    """
    queryset = Offer.objects.all().select_related('user')
    serializer_class = OfferDetailSerializer
    permission_classes = [IsAuthenticated, IsOwner]

class OfferDetailDetailAPIView(generics.RetrieveAPIView):
    """
    API endpoint for retrieving a single offer detail by id.
    Returns all fields needed for nested 'details' in offer response.
    """
    queryset = OfferDetail.objects.all()
    serializer_class = OfferDetailFullSerializer
    permission_classes = [IsAuthenticated]