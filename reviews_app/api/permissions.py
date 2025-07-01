from rest_framework.permissions import BasePermission, SAFE_METHODS

class IsReviewerOrReadOnly(BasePermission):
    """
    Custom permission: Only the reviewer (creator) of a review can edit or delete it.
    Read permissions are allowed for any request.
    Write permissions are only allowed to the reviewer.
    """
    def has_object_permission(self, request, view, obj):
        # Allow safe methods (GET, HEAD, OPTIONS) for everyone
        if request.method in SAFE_METHODS:
            return True
        # Only the reviewer can PATCH/DELETE
        return obj.reviewer == request.user