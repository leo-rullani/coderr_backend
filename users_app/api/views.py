"""
API views for retrieving and updating customer / business profiles.
"""

from django.db import transaction
from django.http import Http404
from django.shortcuts import get_object_or_404
from rest_framework import generics, permissions, filters
from rest_framework.response import Response

from auth_app.models import CustomUser
from users_app.models import UserProfile
from users_app.permissions import (
    IsProfileOwner,
    IsProfileOwnerOrReadOnly,
)

from .serializers import (
    UserProfileSerializer,
    BusinessProfileListSerializer,
    CustomerProfileListSerializer,
)


# ---------------------------------------------------------------------
# Single‑profile views
# ---------------------------------------------------------------------
class BusinessProfileRefUpdateView(generics.RetrieveUpdateAPIView):
    """
    Retrieve **or update** a single business profile.

    • Authenticated caller required  
    • Read access for everyone; write access only for the profile owner  
    • `ref` may be user‑ID, the alias ``ref<ID>`` or a username
    """
    serializer_class = UserProfileSerializer
    permission_classes = [permissions.IsAuthenticated, IsProfileOwnerOrReadOnly]

    @transaction.atomic
    def get_object(self):
        ref = self.kwargs["ref"]
        if ref.lower().startswith("ref") and ref[3:].isdigit():
            ref = ref[3:]

        if ref.isdigit():
            user = get_object_or_404(CustomUser, id=ref, role="business")
        else:
            user = get_object_or_404(CustomUser, username=ref, role="business")

        profile, _ = UserProfile.objects.get_or_create(user=user)
        self.check_object_permissions(self.request, profile)
        return profile


class BusinessProfileDetailView(generics.RetrieveAPIView):
    """
    Convenience endpoint that returns *one* business profile
    (used by the automated test‑suite to verify representation rules).
    """
    serializer_class = UserProfileSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_object(self):
        qs = UserProfile.objects.filter(user__role="business")
        if not qs.exists():
            raise Http404("No business profile found")
        return qs.first()


# ---------------------------------------------------------------------
# List views
# ---------------------------------------------------------------------
class BusinessProfileListView(generics.ListAPIView):
    """
    List **all** business profiles.

    • Creates placeholder profiles for business users without one  
    • Supports `?search=<term>` on username, first name, last name, location  
    • No pagination → full list returned
    """
    serializer_class = BusinessProfileListSerializer
    permission_classes = [permissions.IsAuthenticated]
    pagination_class = None

    # ← NEW: enable ?search=
    filter_backends = [filters.SearchFilter]
    search_fields = [
        "user__username",
        "first_name",
        "last_name",
        "location",
    ]

    def get_queryset(self):
        business_users = CustomUser.objects.filter(role="business")
        existing = set(
            UserProfile.objects.filter(user__role="business")
            .values_list("user_id", flat=True)
        )

        # create missing placeholder profiles
        missing = [u for u in business_users if u.id not in existing]
        UserProfile.objects.bulk_create(
            [UserProfile(user=u) for u in missing],
            ignore_conflicts=True,
        )

        return (
            UserProfile.objects.filter(user__role="business")
            .select_related("user")
            .order_by("user__id")
        )

    def list(self, request, *args, **kwargs):
        data = self.get_serializer(self.filter_queryset(self.get_queryset()), many=True).data
        return Response(data)


class CustomerProfileListView(generics.ListAPIView):
    """List all customer profiles (auth required, supports ?search=)."""

    serializer_class = CustomerProfileListSerializer
    permission_classes = [permissions.IsAuthenticated]
    pagination_class = None
    filter_backends = [filters.SearchFilter]
    search_fields = ["user__username", "first_name", "last_name"]

    def get_queryset(self):
        return (
            UserProfile.objects.filter(user__role="customer")
            .select_related("user")
            .order_by("user__id")
        )


class UserProfileUniversalDetailView(generics.RetrieveUpdateAPIView):
    """
    Retrieve **or update** *any* profile (customer or business) by
    user‑ID or username.
    """
    serializer_class = UserProfileSerializer
    permission_classes = [permissions.IsAuthenticated, IsProfileOwnerOrReadOnly]

    def get_object(self):
        ref = self.kwargs["ref"]
        if ref.isdigit():
            profile = get_object_or_404(UserProfile, user__id=ref)
        else:
            profile = get_object_or_404(UserProfile, user__username=ref)
        self.check_object_permissions(self.request, profile)
        return profile
