"""
API views for Offers and OfferDetails.
"""

from django.db.models import Min
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework import generics, filters, permissions
from rest_framework.permissions import IsAuthenticated

from offers_app.models import Offer, OfferDetail
from offers_app.api.serializers import (
    OfferDetailSerializer,
    OfferDetailFullSerializer,
    OfferCreateSerializer,
    OfferPublicSerializer,
)
from offers_app.api.permissions import IsBusinessUser, IsOwner
from offers_app.api.filters import OfferFilter


class OfferListCreateAPIView(generics.ListCreateAPIView):
    """
    Offers collection endpoint.

    * **GET** – public listing; supports filter, search, ordering  
    * **POST** – create new offer; requires *business* authentication
    """

    queryset = (
        Offer.objects.all()
        .annotate(min_price_annotated=Min("details__price"))
        .select_related("user")
    )
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_class = OfferFilter
    search_fields = ["title", "description"]
    ordering_fields = ["updated_at", "min_price_annotated"]
    ordering = ["-updated_at"]

    def get_permissions(self):
        """Return the permission set that applies to the current HTTP method."""
        if self.request.method == "POST":
            return [IsAuthenticated(), IsBusinessUser()]
        return [permissions.AllowAny()]

    def get_serializer_class(self):
        """Return write‑ or read‑serializer depending on the HTTP method."""
        return OfferCreateSerializer if self.request.method == "POST" else OfferPublicSerializer

    def perform_create(self, serializer):
        """
        Persist the new offer.

        The OfferCreateSerializer already assigns ``user`` from the request
        context, so we simply call ``save()`` without extra arguments to
        avoid passing ``user`` twice.
        """
        serializer.save()


class OfferDetailAPIView(generics.RetrieveUpdateDestroyAPIView):
    """
    Single offer endpoint.

    * **GET**    – any authenticated user  
    * **PATCH / PUT / DELETE** – owner only  
    * DELETE returns *204 No Content* on success
    """

    queryset = Offer.objects.all().select_related("user")
    serializer_class = OfferDetailSerializer

    def get_permissions(self):
        """Apply owner check for write actions."""
        if self.request.method in ["PATCH", "PUT", "DELETE"]:
            return [IsAuthenticated(), IsOwner()]
        return [IsAuthenticated()]


class OfferDetailDetailAPIView(generics.RetrieveAPIView):
    """
    Retrieve a single *OfferDetail* (nested line of an offer).
    """

    queryset = OfferDetail.objects.all()
    serializer_class = OfferDetailFullSerializer
    permission_classes = [IsAuthenticated]
