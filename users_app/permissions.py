"""
Custom per-object permissions for user profiles.
"""

from rest_framework.permissions import SAFE_METHODS, BasePermission
class IsProfileOwner(BasePermission):
    """Write access is limited to the owner of the profile."""
    def has_object_permission(self, request, view, obj):
        return obj.user == request.user
class IsProfileOwnerOrReadOnly(BasePermission):
    """
    Read-only for any authenticated user, write access for the owner only.
    """
    def has_object_permission(self, request, view, obj):
        if request.method in SAFE_METHODS:
            return True
        return obj.user == request.user