from rest_framework.permissions import BasePermission, SAFE_METHODS

class IsReviewerOrReadOnly(BasePermission):
    """
    Object‑level permission that grants write access (PATCH / DELETE)
    exclusively to the *reviewer* who created the review.
    All authenticated users may perform safe (read‑only) requests.
    """

    def has_object_permission(self, request, view, obj):
        # Allow GET / HEAD / OPTIONS for everyone
        if request.method in SAFE_METHODS:
            return True
        # Write methods – only the original reviewer
        return obj.reviewer == request.user
