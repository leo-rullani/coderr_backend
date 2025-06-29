from rest_framework import generics, permissions
from users_app.models import UserProfile
from .serializers import UserProfileSerializer
from .permissions import IsOwnerProfile
from django.shortcuts import get_object_or_404

class UserProfileDetailView(generics.RetrieveUpdateAPIView):
    """
    Allows authenticated users to retrieve or update their own profile,
    using the user's ID in the URL.
    Only the profile owner is authorized.
    """

    queryset = UserProfile.objects.all()
    serializer_class = UserProfileSerializer
    permission_classes = [permissions.IsAuthenticated, IsOwnerProfile]
    # lookup_field = 'user_id'  # <- geht auch, aber ist bei OneToOne nicht default!

    def get_object(self):
        """
        Returns the profile for the user ID in the URL.
        """
        user_id = self.kwargs["pk"]
        return get_object_or_404(UserProfile, user_id=user_id)

class BusinessProfileListView(generics.ListAPIView):
    """
    Returns a list of all business user profiles.
    Accessible only to authenticated users.
    """
    serializer_class = UserProfileSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        return UserProfile.objects.filter(user__role='business')

class CustomerProfileListView(generics.ListAPIView):
    """
    Returns a list of all customer user profiles.
    Accessible only to authenticated users.
    """
    serializer_class = UserProfileSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        return UserProfile.objects.filter(user__role='customer')