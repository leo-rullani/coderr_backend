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
    ViewSet for CRUD operations on *Review* objects.

    * **GET** (list / retrieve) – any authenticated user  
    * **POST** – only *customers* may create a review  
    * **PATCH / DELETE** – only the review *author* (see permission)

    The filter backend allows queries such as:

        /api/reviews/?business_user=2
        /api/reviews/?reviewer=1
    """

    queryset = Review.objects.all()
    serializer_class = ReviewSerializer
    permission_classes = [IsAuthenticated, IsReviewerOrReadOnly]

    filter_backends = [DjangoFilterBackend, OrderingFilter]
    filterset_fields = {"business_user": ["exact"], "reviewer": ["exact"]}
    ordering_fields = ["updated_at", "rating"]
    ordering = ["-updated_at"]

    def perform_create(self, serializer):
        """
        Attach the current user as *reviewer*.

        Only **customer** accounts are allowed to create reviews.
        A user counts as customer if *either*

        * `CustomUser.role == "customer"` **or**
        * legacy flag `user.userprofile.is_customer == True`
        """
        user = self.request.user
        is_customer_role = getattr(user, "role", None) == "customer"
        is_customer_profile = (
            hasattr(user, "userprofile")
            and getattr(user.userprofile, "is_customer", False)
        )

        if not (is_customer_role or is_customer_profile):
            raise PermissionDenied("Only customers can create reviews.")

        serializer.save(reviewer=user)