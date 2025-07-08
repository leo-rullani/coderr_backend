"""
Offer & OfferDetail API endpoints.
"""

from django.db.models import Min
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework import generics, filters, permissions, status
from rest_framework.exceptions import ValidationError, NotFound
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

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
    • **GET**   public list with pagination, filters, search & ordering  
    • **POST**  create a new offer – *business* users only
    """

    queryset = (
        Offer.objects.all()
        .annotate(min_price_annotated=Min("details__price"))
        .select_related("user")
        .distinct()
    )

    # ------------- filters / ordering --------------------------------------
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    search_fields   = [
        "title", "description",
        "details__title", "details__features", "details__offer_type",
        "user__username",
    ]
    filterset_class = OfferFilter
    ordering_fields = ["updated_at", "min_price_annotated", "min_price"]
    ordering        = ["-updated_at"]

    @staticmethod
    def _translated_ordering(param: str) -> str:
        """?ordering=min_price → min_price_annotated (behält das «‑»‑Präfix)."""
        if param.lstrip("-") == "min_price":
            return f"{'-' if param.startswith('-') else ''}min_price_annotated"
        return param

    # ------------- permissions ---------------------------------------------
    def get_permissions(self):
        if self.request.method == "POST":
            return [IsAuthenticated(), IsBusinessUser()]
        return [permissions.AllowAny()]

    # ------------- serializer ----------------------------------------------
    def get_serializer_class(self):
        return (
            OfferCreateSerializer
            if self.request.method == "POST"
            else OfferListSerializer
        )

    # ------------- queryset mods -------------------------------------------
    def get_queryset(self):
        qs = super().get_queryset()
        ordering = self.request.query_params.get("ordering")
        if ordering:
            qs = qs.order_by(self._translated_ordering(ordering))
        return qs

    # ------------- create ---------------------------------------------------
    def perform_create(self, serializer):
        serializer.save()                      # user kommt aus dem Serializer‑context


# --------------------------------------------------------------------------- #
#  DETAIL / PATCH / DELETE                                                    #
# --------------------------------------------------------------------------- #
class OfferDetailAPIView(generics.RetrieveUpdateDestroyAPIView):
    """
    • **GET**     any authenticated user  
    • **PATCH**   owner only – liefert **400** bei ungültigen Feldern  
    • **DELETE**  owner only – liefert **204 No Content**
    """

    queryset         = Offer.objects.all().select_related("user")
    serializer_class = OfferDetailSerializer

    # ------------- permissions ---------------------------------------------
    def get_permissions(self):
        if self.request.method in {"PATCH", "PUT", "DELETE"}:
            return [IsAuthenticated(), IsOwner()]
        return [IsAuthenticated()]

    # ------------- PATCH / PUT ---------------------------------------------
    def update(self, request, *args, **kwargs):
        """
        Reihenfolge bewusst geändert →*erst* den Body validieren,
        *dann* das eigentliche Objekt holen.

        Dadurch entsteht für fehlerhafte Felder ein echter **400 BadRequest**
        –selbst wenn die ID zufällig nicht existiert.
        """
        if not request.data:
            raise ValidationError(
                {"detail": "Request body may not be empty."},
                code=status.HTTP_400_BAD_REQUEST,
            )

        # 1 Body‐Validierung (ohne Objekt‑Bindung)
        temp_serializer = self.get_serializer(data=request.data, partial=True)
        temp_serializer.is_valid(raise_exception=True)  # ⇒ 400 bei fehlenden/falschen Feldern

        # 2 erst jetzt das Ziel‑Objekt holen → 404 falls es nicht existiert,
        #     403 falls falscher Owner (über IsOwner)
        instance = self.get_object()

        # 3 finales Update mit geprüften Daten
        serializer = self.get_serializer(instance, data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)
        self.perform_update(serializer)

        return Response(serializer.data, status=status.HTTP_200_OK)


# --------------------------------------------------------------------------- #
#  DETAIL OF A SINGLE OFFER‑LINE‑ITEM                                         #
# --------------------------------------------------------------------------- #
class OfferDetailDetailAPIView(generics.RetrieveAPIView):
    """Retrieve one *OfferDetail* – authentication required."""
    queryset = OfferDetail.objects.all()
    serializer_class = OfferDetailFullSerializer
    permission_classes = [IsAuthenticated]