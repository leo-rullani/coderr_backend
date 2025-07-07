"""
Offer & OfferDetail API endpoints.
"""

from django.db.models import Min
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework import generics, filters, permissions
from rest_framework.exceptions import ValidationError
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


# --------------------------------------------------------------------------- #
#  LIST + CREATE                                                              #
# --------------------------------------------------------------------------- #
class OfferListCreateAPIView(generics.ListCreateAPIView):
    """
    • **GET**    public list with pagination, filters, search & ordering  
    • **POST**   create a new offer – authenticated **business** users only
    """

    queryset = (
        Offer.objects.all()
        .annotate(min_price_annotated=Min("details__price"))
        .select_related("user")
        .distinct()
    )

    # -------------------- filters / ordering --------------------------------
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    search_fields   = [
        "title",
        "description",
        "details__title",
        "details__features",
        "details__offer_type",
        "user__username",
    ]
    filterset_class = OfferFilter
    ordering_fields = ["updated_at", "min_price_annotated", "min_price"]
    ordering        = ["-updated_at"]

    @staticmethod
    def _translated_ordering(param: str) -> str:
        """Translate ?ordering=min_price → min_price_annotated (behält «‑»‑Prefix)."""
        if param.lstrip("-") == "min_price":
            return f"{'-' if param.startswith('-') else ''}min_price_annotated"
        return param

    # -------------------- permissions ---------------------------------------
    def get_permissions(self):
        if self.request.method == "POST":
            return [IsAuthenticated(), IsBusinessUser()]
        return [permissions.AllowAny()]

    # -------------------- serializer choice ---------------------------------
    def get_serializer_class(self):
        return OfferCreateSerializer if self.request.method == "POST" else OfferListSerializer

    # -------------------- queryset mods -------------------------------------
    def get_queryset(self):
        qs = super().get_queryset()
        ordering = self.request.query_params.get("ordering")
        if ordering:
            qs = qs.order_by(self._translated_ordering(ordering))
        return qs

    # -------------------- create --------------------------------------------
    def perform_create(self, serializer):
        # der Serializer setzt `user` bereits selbst (via context)
        serializer.save()


# --------------------------------------------------------------------------- #
#  DETAIL / PATCH / DELETE                                                    #
# --------------------------------------------------------------------------- #
class OfferDetailAPIView(generics.RetrieveUpdateDestroyAPIView):
    """
    • **GET**      any authenticated user  
    • **PATCH**    owner only – liefert **400** bei ungültigem Body  
    • **DELETE**   owner only – liefert **204 No Content**
    """

    queryset         = Offer.objects.all().select_related("user")
    serializer_class = OfferDetailSerializer

    # -------------------- permissions ---------------------------------------
    def get_permissions(self):
        if self.request.method in {"PATCH", "PUT", "DELETE"}:
            return [IsAuthenticated(), IsOwner()]
        return [IsAuthenticated()]

    # -------------------- object fetch (→ 403 vor 404) ----------------------
    def get_object(self):
        obj = super().get_object()          # 404 falls nicht vorhanden
        self.check_object_permissions(self.request, obj)  # 403 falls falscher Owner
        return obj

    # -------------------- PATCH / PUT ---------------------------------------
    def update(self, request, *args, **kwargs):
        # leere Bodies sofort als 400 zurückweisen
        if not request.data:
            raise ValidationError({"detail": "Request body may not be empty."})

        # läuft die normale DRF‑Update‑Logik; trifft die Feld‑Validierung des
        # Serializers nicht zu, löst dies eine ValidationError (→ 400) aus
        return super().update(request, *args, **kwargs)


# --------------------------------------------------------------------------- #
#  DETAIL OF A SINGLE OFFER‑LINE‑ITEM                                         #
# --------------------------------------------------------------------------- #
class OfferDetailDetailAPIView(generics.RetrieveAPIView):
    """Retrieve one *OfferDetail* – authentication required."""
    queryset = OfferDetail.objects.all()
    serializer_class = OfferDetailFullSerializer
    permission_classes = [IsAuthenticated]