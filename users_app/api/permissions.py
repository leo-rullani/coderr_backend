from rest_framework import permissions

class IsOwnerProfile(permissions.BasePermission):
    """
    Allows access only to the owner of the profile.
    """

    def has_object_permission(self, request, view, obj):
        return obj.user == request.user