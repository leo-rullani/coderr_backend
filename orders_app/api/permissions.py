from rest_framework.permissions import BasePermission

class IsCustomerUser(BasePermission):
    """
    Allows access only to users with role 'customer'.
    """
    message = "Only customers can create orders."

    def has_permission(self, request, view):
        return request.user.is_authenticated and getattr(request.user, "role", None) == "customer"
