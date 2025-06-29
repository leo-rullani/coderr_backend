from rest_framework import generics, filters, permissions
from django_filters.rest_framework import DjangoFilterBackend
from offers_app.models import Offer
from offers_app.api.serializers import OfferListSerializer, OfferDetailSerializer
from offers_app.api.filters import OfferFilter

class OfferListAPIView(generics.ListAPIView):
    """
    API endpoint that returns a paginated list of offers.
    Each offer contains a summary of its details (id, url only).
    """
    queryset = Offer.objects.all().select_related('user')
    serializer_class = OfferListSerializer
    filter_backends = [
        DjangoFilterBackend,
        filters.SearchFilter,
        filters.OrderingFilter,
    ]
    filterset_class = OfferFilter
    search_fields = ['title', 'description']
    ordering_fields = ['updated_at', 'min_price']
    ordering = ['-updated_at']
    permission_classes = [permissions.AllowAny]

class OfferDetailAPIView(generics.RetrieveAPIView):
    """
    API endpoint that returns a single offer by id,
    with all nested detail fields, as required by the API doc.
    """
    queryset = Offer.objects.all().select_related('user')
    serializer_class = OfferDetailSerializer
    permission_classes = [permissions.AllowAny]