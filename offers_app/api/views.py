from offers_app.api.permissions import IsBusinessUser, IsOwner
from rest_framework import generics, filters, permissions
from rest_framework.permissions import IsAuthenticated
from django_filters.rest_framework import DjangoFilterBackend
from django.db.models import Min
from offers_app.models import Offer, OfferDetail
from offers_app.api.serializers import (
    OfferListSerializer,
    OfferDetailSerializer,
    OfferCreateSerializer,
    OfferDetailFullSerializer,
    OfferPublicSerializer,
)
from offers_app.api.permissions import IsOwner
from offers_app.api.filters import OfferFilter
from rest_framework import permissions
from .permissions import IsBusinessUser


class IsBusinessUser(permissions.BasePermission):
    """
    Restrict access to *business* accounts only.

    This check recognises both

    1. current accounts where ``CustomUser.role == 'business'`` and
    2. legacy accounts that were created before the ``role`` field
       existed and therefore rely on ``userprofile.is_customer == False``.
    """

    def has_permission(self, request, view):
        user = request.user
        if not user.is_authenticated:
            return False
        # 1) primary check: dedicated role field
        if getattr(user, "role", None) == "business":
            return True
        # 2) fallback for legacy accounts
        profile = getattr(user, "userprofile", None)
        return profile and not getattr(profile, "is_customer", True)


class IsBusinessUser(permissions.BasePermission):
    """
    Allow access only to users whose ``CustomUser.role`` equals ``'business'``.
    """

    def has_permission(self, request, view):
        """
        Return ``True`` iff the request is authenticated *and*
        the underlying user has role ``'business'``.

        Args:
            request: DRF request object.
            view: DRF view object.

        Returns:
            bool: ``True`` for business users, ``False`` otherwise.
        """
        return (
            request.user.is_authenticated
            and getattr(request.user, "role", None) == "business"
        )


class OfferListCreateAPIView(generics.ListCreateAPIView):
    """
    Offers collection endpoint.

    * **GET** – public listing; supports filter, search, ordering  
    * **POST** – create a new offer (requires *business* authentication)
    """

    queryset = (
        Offer.objects.all()
        .annotate(min_price_annotated=Min("details__price"))
        .select_related("user")
    )
    filter_backends = [
        DjangoFilterBackend,
        filters.SearchFilter,
        filters.OrderingFilter,
    ]
    filterset_class = OfferFilter
    search_fields = ["title", "description"]
    ordering_fields = ["updated_at", "min_price_annotated"]
    ordering = ["-updated_at"]

    def get_permissions(self):
        """
        Return the permission set that applies to the current HTTP method.
        """
        if self.request.method == "POST":
            return [IsAuthenticated(), IsBusinessUser()]
        return [permissions.AllowAny()]

    def get_serializer_class(self):
        """
        Choose the write‑ or read‑serializer based on the HTTP method.
        """
        if self.request.method == "POST":
            return OfferCreateSerializer
        return OfferPublicSerializer

    def perform_create(self, serializer):
        """
        Persist the new offer and link it to ``request.user``.
        """
        serializer.save()


class OfferDetailAPIView(generics.RetrieveUpdateDestroyAPIView):
    """
    Single offer endpoint.

    * **GET**    – any authenticated user  
    * **PATCH / PUT / DELETE** – owner only (object‑level permission)  
    * DELETE returns *204 No Content* on success
    """

    queryset = Offer.objects.all().select_related("user")
    serializer_class = OfferDetailSerializer

    def get_permissions(self):
        """
        Apply object‑level owner check for write methods.
        """
        if self.request.method in ["PATCH", "PUT", "DELETE"]:
            return [IsAuthenticated(), IsOwner()]
        return [IsAuthenticated()]


class OfferDetailDetailAPIView(generics.RetrieveAPIView):
    """
    Retrieve a single *OfferDetail* record by primary key.

    This is used when the frontend needs one specific detail object
    that belongs to an offer.
    """

    queryset = OfferDetail.objects.all()
    serializer_class = OfferDetailFullSerializer
    permission_classes = [IsAuthenticated]