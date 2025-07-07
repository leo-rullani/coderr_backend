"""
Custom permission classes for the Offers API.
"""

from rest_framework.permissions import BasePermission


class IsBusinessUser(BasePermission):
    """
    Allow access **only** to accounts whose ``role`` is ``"business"``.

    ‑ No fallback to legacy profile flags – the test‑suite differentiates
      strictly über ``CustomUser.role``.
    """

    def has_permission(self, request, view):
        return request.user.is_authenticated and getattr(request.user, "role", "") == "business"


class IsOwner(BasePermission):
    """
    Object‑level access limited to the related ``user``.
    """

    def has_object_permission(self, request, view, obj):
        return getattr(obj, "user", None) == request.user