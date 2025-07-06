"""
Offer & OfferDetail API endpoints.

Endpoints
---------
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
    * **GET**  – public list with pagination, filters, search & ordering  
    * **POST** – create a new offer; only authenticated **business** users
    """

    queryset = (
        Offer.objects.all()
        .annotate(min_price_annotated=Min("details__price"))
        .select_related("user")
        .distinct()  # prevents duplicates when joining for search
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

    # the front‑end requests ?ordering=min_price / -min_price
    ordering_fields = ["updated_at", "min_price_annotated", "min_price"]
    ordering = ["-updated_at"]

    @staticmethod
    def _translated_ordering(ordering_param: str) -> str:
        """
        Translate the alias *min_price* → *min_price_annotated*,
        keeping a potential '-' prefix.
        """
        if ordering_param.lstrip("-") == "min_price":
            sign = "-" if ordering_param.startswith("-") else ""
            return f"{sign}min_price_annotated"
        return ordering_param

    def get_permissions(self):
        if self.request.method == "POST":
            return [IsAuthenticated(), IsBusinessUser()]
        return [permissions.AllowAny()]

    def get_serializer_class(self):
        return OfferCreateSerializer if self.request.method == "POST" else OfferListSerializer

    def get_queryset(self):
        qs = super().get_queryset()
        ordering_param = self.request.query_params.get("ordering")
        if ordering_param:
            qs = qs.order_by(self._translated_ordering(ordering_param))
        return qs

    def perform_create(self, serializer):
        serializer.save()  # user is injected by the serializer context

class OfferDetailAPIView(generics.RetrieveUpdateDestroyAPIView):
    """
    Retrieve, partially update or delete a single **Offer**.

    * GET    – allowed for any authenticated user  
    * PATCH  – owner only  
    * DELETE – owner only (returns **204 No Content**)
    """
    queryset = Offer.objects.all().select_related("user")
    serializer_class = OfferDetailSerializer

    def get_permissions(self):
        if self.request.method in {"PATCH", "PUT", "DELETE"}:
            return [IsAuthenticated(), IsOwner()]
        return [IsAuthenticated()]

class OfferDetailDetailAPIView(generics.RetrieveAPIView):
    """Retrieve a single *OfferDetail* (line item) – authentication required."""
    queryset = OfferDetail.objects.all()
    serializer_class = OfferDetailFullSerializer
    permission_classes = [IsAuthenticated]