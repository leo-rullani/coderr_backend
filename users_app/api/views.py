from django.db import transaction
from django.http import Http404
from django.shortcuts import get_object_or_404
from rest_framework import generics, permissions

from auth_app.models import CustomUser
from users_app.models import UserProfile
from users_app.permissions import IsProfileOwner

from .serializers import (
    UserProfileSerializer,
    BusinessProfileListSerializer,
    CustomerProfileListSerializer,
)


class BusinessProfileRefUpdateView(generics.RetrieveUpdateAPIView):
    """
    Retrieve **or update** a Business profile by user ID / 'ref<ID>' / username.
    Creates an empty UserProfile automatically if none exists.
    """

    serializer_class = UserProfileSerializer
    permission_classes = [permissions.IsAuthenticated, IsProfileOwner]

    @transaction.atomic
    def get_object(self):
        """Resolve 'ref', ensure role='business', create profile if needed."""
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
    serializer_class = UserProfileSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_object(self):
        qs = UserProfile.objects.filter(user__role="business")
        if not qs.exists():
            raise Http404("No business profile found")
        return qs.first()


class BusinessProfileListView(generics.ListAPIView):
    serializer_class = BusinessProfileListSerializer
    permission_classes = [permissions.IsAuthenticated]
    pagination_class = None

    def get_queryset(self):
        return UserProfile.objects.filter(user__role="business")


class CustomerProfileListView(generics.ListAPIView):
    serializer_class = CustomerProfileListSerializer
    permission_classes = [permissions.IsAuthenticated]
    pagination_class = None

    def get_queryset(self):
        return UserProfile.objects.filter(user__role="customer")


class UserProfileUniversalDetailView(generics.RetrieveUpdateAPIView):
    serializer_class = UserProfileSerializer
    permission_classes = [permissions.IsAuthenticated, IsProfileOwner]

    def get_object(self):
        ref = self.kwargs["ref"]
        if ref.isdigit():
            profile = get_object_or_404(UserProfile, user__id=ref)
        else:
            profile = get_object_or_404(UserProfile, user__username=ref)
        self.check_object_permissions(self.request, profile)
        return profile