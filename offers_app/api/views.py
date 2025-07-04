from rest_framework import generics, filters, permissions
from rest_framework.permissions import IsAuthenticated
from django_filters.rest_framework import DjangoFilterBackend
from django.db.models import Min
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
        """
        Check if the user is authenticated and has the 'business' role.

        Args:
            request: The HTTP request instance.
            view: The view instance.

        Returns:
            bool: True if the user is authenticated and role is 'business', else False.
        """
        return request.user.is_authenticated and getattr(request.user, "role", None) == "business"


class OfferListCreateAPIView(generics.ListCreateAPIView):
    """
    API endpoint for listing offers (GET) and creating new offers (POST).

    GET requests:
        - Publicly accessible.
        - Supports filtering, search, and ordering.
        - Annotates offers with the minimum price from related details.

    POST requests:
        - Requires authenticated user with 'business' role.
        - Creates a new offer with nested details.
    """

    queryset = Offer.objects.all().annotate(min_price_annotated=Min('details__price')).select_related('user')
    filter_backends = [
        DjangoFilterBackend,
        filters.SearchFilter,
        filters.OrderingFilter,
    ]
    filterset_class = OfferFilter
    search_fields = ['title', 'description']
    ordering_fields = ['updated_at', 'min_price_annotated']
    ordering = ['-updated_at']

    def get_permissions(self):
        """
        Return permission classes depending on the request method.

        Returns:
            list: List of permission instances.
        """
        if self.request.method == "POST":
            return [IsAuthenticated(), IsBusinessUser()]
        return [permissions.AllowAny()]

    def get_serializer_class(self):
        """
        Return serializer class depending on the request method.

        Returns:
            Serializer class.
        """
        if self.request.method == "POST":
            return OfferCreateSerializer
        return OfferListSerializer

    def perform_create(self, serializer):
        """
        Save the new offer, associating it with the current user.

        Args:
            serializer: The serializer instance with validated data.
        """
        serializer.save()


class OfferDetailAPIView(generics.RetrieveUpdateDestroyAPIView):
    """
    API endpoint for retrieving, updating, or deleting a single offer by id.

    Permissions:
        - PATCH/PUT/DELETE: Only the offer owner.
        - GET: Any authenticated user.

    Responses:
        - DELETE returns HTTP 204 No Content on success.
    """

    queryset = Offer.objects.all().select_related('user')
    serializer_class = OfferDetailSerializer

    def get_permissions(self):
        """
        Return permission classes depending on the request method.

        Returns:
            list: List of permission instances.
        """
        if self.request.method in ["PATCH", "PUT", "DELETE"]:
            return [IsAuthenticated(), IsOwner()]
        return [IsAuthenticated()]


class OfferDetailDetailAPIView(generics.RetrieveAPIView):
    """
    API endpoint for retrieving a single offer detail by id.

    Returns all fields required for nested 'details' in offer response.
    """

    queryset = OfferDetail.objects.all()
    serializer_class = OfferDetailFullSerializer
    permission_classes = [IsAuthenticated]