from rest_framework.viewsets import ModelViewSet
from rest_framework.permissions import IsAuthenticated
from rest_framework.exceptions import PermissionDenied
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework.filters import OrderingFilter
from reviews_app.models import Review
from .serializers import ReviewSerializer
from .permissions import IsReviewerOrReadOnly  # NEU!

class ReviewViewSet(ModelViewSet):
    """
    List, retrieve, create, update and delete reviews.
    Only the reviewer can update or delete his review.
    Only authenticated users with a customer profile may create reviews.
    """
    queryset = Review.objects.all()
    serializer_class = ReviewSerializer
    permission_classes = [IsAuthenticated, IsReviewerOrReadOnly]  # NEU!
    filter_backends = [DjangoFilterBackend, OrderingFilter]
    filterset_fields = {
        "business_user": ["exact"],
        "reviewer": ["exact"],
    }
    ordering_fields = ["updated_at", "rating"]
    ordering = ["-updated_at"]

    def perform_create(self, serializer):
        user = self.request.user
        # Kunden-Check: nur Kunden dürfen erstellen
        if not hasattr(user, "userprofile") or not user.userprofile.is_customer:
            raise PermissionDenied("Nur Kunden dürfen Bewertungen abgeben.")
        serializer.save(reviewer=user)