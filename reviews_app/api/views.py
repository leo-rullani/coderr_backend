from rest_framework.viewsets import ModelViewSet
from rest_framework.permissions import IsAuthenticated
from rest_framework.exceptions import PermissionDenied
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework.filters import OrderingFilter
from reviews_app.models import Review
from .serializers import ReviewSerializer

class ReviewViewSet(ModelViewSet):
    """
    List, retrieve, and create reviews.
    Allows filtering by business_user and reviewer,
    and ordering by updated_at or rating.
    Only authenticated users with a customer profile may create reviews.
    """
    queryset = Review.objects.all()
    serializer_class = ReviewSerializer
    permission_classes = [IsAuthenticated]
    filter_backends = [DjangoFilterBackend, OrderingFilter]
    filterset_fields = {
        "business_user": ["exact"],
        "reviewer": ["exact"],
    }
    ordering_fields = ["updated_at", "rating"]
    ordering = ["-updated_at"]

    def perform_create(self, serializer):
        user = self.request.user
        # Korrekte Prüfung auf Kundenprofil:
        if not hasattr(user, "userprofile") or not user.userprofile.is_customer:
            raise PermissionDenied("Nur Kunden dürfen Bewertungen abgeben.")
        serializer.save(reviewer=user)