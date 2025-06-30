from rest_framework.permissions import BasePermission

class IsCustomerUser(BasePermission):
    """
    Allows access only to users with role 'customer'.
    """
    message = "Only customers can create orders."

    def has_permission(self, request, view):
        return request.user.is_authenticated and getattr(request.user, "role", None) == "customer"

class IsOrderBusinessUser(BasePermission):
    """
    Allows access only to the business_user of the order with role 'business'.
    """
    message = "Only the business user of this order can update the status."

    def has_object_permission(self, request, view, obj):
        return (
            request.user.is_authenticated
            and getattr(request.user, "role", None) == "business"
            and obj.business_user == request.user
        )
