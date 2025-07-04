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
    API endpoint to retrieve or update the profile of a specific user by user ID.
    Only the owner of the profile is allowed to update it.

    - GET: Returns profile data for the user with the given ID.
    - PATCH/PUT: Allows the profile owner to update their profile data.
    """
    queryset = UserProfile.objects.all()
    serializer_class = UserProfileSerializer
    permission_classes = [permissions.IsAuthenticated, IsOwnerProfile]

    def get_object(self):
        """
        Fetches the UserProfile object for the user ID provided in the URL.

        Returns:
            UserProfile instance matching the user ID in the URL path.

        Raises:
            Http404 if UserProfile does not exist for the given user ID.
        """
        user_id = self.kwargs["pk"]
        return get_object_or_404(UserProfile, user__id=user_id)

    def perform_update(self, serializer):
        """
        Restricts update operation to the profile owner only.

        Raises:
            PermissionDenied if the authenticated user is not the owner.
        """
        if serializer.instance.user != self.request.user:
            raise PermissionDenied("You do not have permission to update this profile.")
        serializer.save()


class BusinessProfileListView(generics.ListAPIView):
    """
    API endpoint that returns a list of all business user profiles.
    Accessible only to authenticated users.
    Pagination is disabled.
    """
    serializer_class = BusinessProfileListSerializer
    permission_classes = [permissions.IsAuthenticated]
    pagination_class = None

    def get_queryset(self):
        """
        Filters and returns UserProfile objects linked to users with role 'business'.

        Returns:
            QuerySet of UserProfiles with user role 'business'.
        """
        return UserProfile.objects.filter(user__role="business")


class CustomerProfileListView(generics.ListAPIView):
    """
    API endpoint that returns a list of all customer user profiles.
    Accessible only to authenticated users.
    Pagination is disabled.
    """
    serializer_class = CustomerProfileListSerializer
    permission_classes = [permissions.IsAuthenticated]
    pagination_class = None

    def get_queryset(self):
        """
        Filters and returns UserProfile objects linked to users with role 'customer'.

        Returns:
            QuerySet of UserProfiles with user role 'customer'.
        """
        return UserProfile.objects.filter(user__role="customer")