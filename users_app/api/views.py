from rest_framework import generics, permissions
from users_app.models import UserProfile
from .serializers import (
    UserProfileSerializer,
    BusinessProfileListSerializer,
    CustomerProfileListSerializer,
)
from .permissions import IsOwnerProfile
from django.shortcuts import get_object_or_404
from rest_framework.exceptions import PermissionDenied

class UserProfileDetailView(generics.RetrieveUpdateAPIView):
    """
    Allows authenticated users to retrieve or update their own profile,
    using the user's ID in the URL.
    Only the profile owner is authorized.
    """
    queryset = UserProfile.objects.all()
    serializer_class = UserProfileSerializer
    permission_classes = [permissions.IsAuthenticated, IsOwnerProfile]

    def get_object(self):
        """
        Returns the UserProfile where the related user's ID matches the URL pk.
        """
        user_id = self.kwargs["pk"]
        return get_object_or_404(UserProfile, user__id=user_id)

    def perform_update(self, serializer):
        """
        Ensure only the profile owner can update the profile.
        """
        if serializer.instance.user != self.request.user:
            raise PermissionDenied("You do not have permission to update this profile.")
        serializer.save()

class BusinessProfileListView(generics.ListAPIView):
    """
    Returns a list of all business user profiles.
    Accessible only to authenticated users.
    """
    serializer_class = BusinessProfileListSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        """
        Filters all UserProfiles whose linked user has role 'business'.
        """
        return UserProfile.objects.filter(user__role="business")

class CustomerProfileListView(generics.ListAPIView):
    """
    Returns a list of all customer user profiles.
    Accessible only to authenticated users.
    """
    serializer_class = CustomerProfileListSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        """
        Filters all UserProfiles whose linked user has role 'customer'.
        """
        return UserProfile.objects.filter(user__role="customer")