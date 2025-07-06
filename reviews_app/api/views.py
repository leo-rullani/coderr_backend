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
    CRUD endpoint for **Review** objects.
    """

    queryset = Review.objects.all()
    serializer_class = ReviewSerializer
    permission_classes = [IsAuthenticated, IsReviewerOrReadOnly]
    pagination_class = None
    filter_backends  = [DjangoFilterBackend, OrderingFilter]
    filterset_fields = {"business_user": ["exact"], "reviewer": ["exact"]}
    ordering_fields  = ["updated_at", "rating"]
    ordering         = ["-updated_at"]
    def get_queryset(self):
        """
        Extend default queryset to honour the alias parameters
        `business_user_id` and `reviewer_id`, which are used by
        the automated test‑suite.
        """
        qs = super().get_queryset()

        b_id = self.request.query_params.get("business_user_id")
        if b_id is not None:
            qs = qs.filter(business_user_id=b_id)

        r_id = self.request.query_params.get("reviewer_id")
        if r_id is not None:
            qs = qs.filter(reviewer_id=r_id)

        return qs

    def perform_create(self, serializer):
        """
        Attach current user as *reviewer*.

        A user counts as *customer* if

        * `CustomUser.role == "customer"` **or**
        * legacy flag `user.userprofile.is_customer == True`
        """
        user = self.request.user
        is_customer_role    = getattr(user, "role", None) == "customer"
        is_customer_profile = (
            hasattr(user, "userprofile")
            and getattr(user.userprofile, "is_customer", False)
        )

        if not (is_customer_role or is_customer_profile):
            raise PermissionDenied("Only customers can create reviews.")

        serializer.save(reviewer=user)