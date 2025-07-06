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
    OfferListSerializer,       
)
from offers_app.api.permissions import IsBusinessUser, IsOwner
from offers_app.api.filters import OfferFilter


class OfferListCreateAPIView(generics.ListCreateAPIView):
    """
    * GET  – public list (filter, search, ordering)  
    * POST – create offer (business user)
    """

    queryset = (
        Offer.objects.all()
        .annotate(min_price_annotated=Min("details__price"))
        .select_related("user")
        .distinct()
    )
    filter_backends = [
        DjangoFilterBackend,
        filters.SearchFilter,
        filters.OrderingFilter,
    ]
    search_fields = [
        "title",
        "description",
        "details__title",
        "details__features",
        "details__offer_type",
        "user__username",
    ]
    filterset_class = OfferFilter
    ordering_fields = ["updated_at", "min_price_annotated"]
    ordering = ["-updated_at"]

    def get_permissions(self):
        if self.request.method == "POST":
            return [IsAuthenticated(), IsBusinessUser()]
        return [permissions.AllowAny()]

    def get_serializer_class(self):
        return OfferCreateSerializer if self.request.method == "POST" else OfferListSerializer  # 🆕

    def perform_create(self, serializer):
        serializer.save()


class OfferDetailAPIView(generics.RetrieveUpdateDestroyAPIView):
    queryset = Offer.objects.all().select_related("user")
    serializer_class = OfferDetailSerializer

    def get_permissions(self):
        if self.request.method in ["PATCH", "PUT", "DELETE"]:
            return [IsAuthenticated(), IsOwner()]
        return [IsAuthenticated()]


class OfferDetailDetailAPIView(generics.RetrieveAPIView):
    queryset = OfferDetail.objects.all()
    serializer_class = OfferDetailFullSerializer
    permission_classes = [IsAuthenticated]