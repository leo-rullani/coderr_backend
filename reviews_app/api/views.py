from rest_framework.viewsets import ReadOnlyModelViewSet
from rest_framework.permissions import IsAuthenticated
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework.filters import OrderingFilter
from reviews_app.models import Review
from .serializers import ReviewSerializer

class ReviewViewSet(ReadOnlyModelViewSet):
    """
    List and retrieve reviews.
    Allows filtering by business_user and reviewer,
    and ordering by updated_at or rating.
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