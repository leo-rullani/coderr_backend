"""
Custom permission classes for the Offers API.
"""

from rest_framework.permissions import BasePermission


class IsBusinessUser(BasePermission):
    """
    Allow access only to *business* accounts.

    The check succeeds if either

    1. ``CustomUser.role`` equals ``"business"`` (current accounts), **or**
    2. the related ``UserProfile`` exists and ``is_customer`` is ``False``
       (legacy accounts created before the ``role`` field was introduced).
    """

    def has_permission(self, request, view):
        user = request.user
        if not user.is_authenticated:
            return False
        if getattr(user, "role", None) == "business":
            return True
        profile = getattr(user, "userprofile", None)
        return bool(profile and not getattr(profile, "is_customer", True))


class IsOwner(BasePermission):
    """
    Grant object‑level access only to the owner of the object.

    The object must expose a ``user`` attribute that references its owner.
    """

    def has_object_permission(self, request, view, obj):
        return getattr(obj, "user", None) == request.user