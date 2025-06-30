from rest_framework.permissions import BasePermission, SAFE_METHODS

class IsOwnerOrReadOnly(BasePermission):
    """
    Custom permission to only allow owners of a review to edit or delete it.
    Read permissions are allowed to any request,
    so GET, HEAD, or OPTIONS requests are always allowed.
    Write permissions are only allowed to the owner of the review.
    """
    def has_object_permission(self, request, view, obj):
        # Read permissions are allowed for any request
        if request.method in SAFE_METHODS:
            return True
        # Write permissions are only allowed to the owner
        return obj.user == request.user
