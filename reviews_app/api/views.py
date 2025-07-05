from rest_framework.viewsets import ModelViewSet
from rest_framework.permissions import IsAuthenticated
from rest_framework.exceptions import PermissionDenied
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework.filters import OrderingFilter
from reviews_app.models import Review
from .serializers import ReviewSerializer
from .permissions import IsReviewerOrReadOnly

class ReviewViewSet(ModelViewSet):
    """
    ViewSet for listing, retrieving, creating, updating, and deleting reviews.
    Only the reviewer can update or delete their review.
    Only authenticated users with a customer profile can create reviews.
    """
    queryset = Review.objects.all()
    serializer_class = ReviewSerializer
    permission_classes = [IsAuthenticated, IsReviewerOrReadOnly]
    filter_backends = [DjangoFilterBackend, OrderingFilter]
    filterset_fields = {
        "business_user": ["exact"],
        "reviewer": ["exact"],
    }
    ordering_fields = ["updated_at", "rating"]
    ordering = ["-updated_at"]

    def perform_create(self, serializer):
        user = self.request.user
        # Check if user has customer profile to allow review creation
        if not hasattr(user, "userprofile") or not getattr(user.userprofile, "is_customer", False):
            raise PermissionDenied("Only customers can create reviews.")
        serializer.save(reviewer=user)