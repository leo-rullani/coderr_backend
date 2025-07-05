"""
Custom per‑object permission: only the profile owner may change it.
"""

from rest_framework.permissions import BasePermission


class IsProfileOwner(BasePermission):
    """
    Grants access only if the requesting user owns the profile object.
    """

    def has_object_permission(self, request, view, obj):
        return obj.user == request.user