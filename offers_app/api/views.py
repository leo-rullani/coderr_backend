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
    * **GET**   – öffentliche Liste (Filter, Suche, Ordering)  
    * **POST**  – neues Angebot (nur Business‑User)
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

    # Front‑End möchte ?ordering=min_price / -min_price → Alias zulassen
    ordering_fields = ["updated_at", "min_price_annotated", "min_price"]
    ordering = ["-updated_at"]

    # ------------------------------------------------------------------ #
    #  helpers                                                           #
    # ------------------------------------------------------------------ #
    def _translated_ordering(self, ordering_param: str) -> str:
        """
        mappt 'min_price'  → 'min_price_annotated'
        (behält +/- Präfix bei)
        """
        if ordering_param.lstrip("-") == "min_price":
            prefix = "-" if ordering_param.startswith("-") else ""
            return f"{prefix}min_price_annotated"
        return ordering_param

    # ------------------------------------------------------------------ #
    #  permissions / serializers                                         #
    # ------------------------------------------------------------------ #
    def get_permissions(self):
        if self.request.method == "POST":
            return [IsAuthenticated(), IsBusinessUser()]
        return [permissions.AllowAny()]

    def get_serializer_class(self):
        if self.request.method == "POST":
            return OfferCreateSerializer
        return OfferListSerializer

    # ------------------------------------------------------------------ #
    #  queryset override  (ordering‑Alias)                               #
    # ------------------------------------------------------------------ #
    def get_queryset(self):
        qs = super().get_queryset()
        ordering_param = self.request.query_params.get("ordering")
        if ordering_param:
            qs = qs.order_by(self._translated_ordering(ordering_param))
        return qs

    def perform_create(self, serializer):
        serializer.save()


class OfferDetailAPIView(generics.RetrieveUpdateDestroyAPIView):
    """
    Einzelnes Angebot (GET, PATCH, DELETE).
    PATCH / DELETE nur für den Besitzer.
    """
    queryset = Offer.objects.all().select_related("user")
    serializer_class = OfferDetailSerializer

    def get_permissions(self):
        if self.request.method in ["PATCH", "PUT", "DELETE"]:
            return [IsAuthenticated(), IsOwner()]
        return [IsAuthenticated()]


class OfferDetailDetailAPIView(generics.RetrieveAPIView):
    """Einzelnes *OfferDetail* abrufen (z. B. für Modal im Front‑End)."""
    queryset = OfferDetail.objects.all()
    serializer_class = OfferDetailFullSerializer
    permission_classes = [IsAuthenticated]